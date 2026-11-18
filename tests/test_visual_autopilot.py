"""Offline tests for automated art direction, visual review and bounded retries."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import visual_autopilot as auto

def fake_jpeg():
    return (b"\xff\xd8\xff\xc0\x00\x11\x08"
        + (512).to_bytes(2,"big")*2
        + b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
        + b"\xff\xd9" + b"\x00"*8)

class AutopilotTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.story=self.root/"story.json"
        self.story.write_text(json.dumps({"schema":3,"title":"Clouds on another world",
                    "scenes":[{"narration":"A gas planet is heated by a nearby star."},
                              {"narration":"The gas escapes into space under radiation."}]}))

    def test_offline_plan(self):
        r=auto.run(self.story,self.root/"out")
        self.assertEqual(r["completed_requests"],0)
        self.assertFalse(r["all_scenes_approved"])
        self.assertEqual(len(r["scenes"]),2)

    def test_no_secrets_no_live(self):
        with patch.dict("os.environ",{"CLOUDFLARE_API_TOKEN":"","CLOUDFLARE_ACCOUNT_ID":""}):
            with self.assertRaisesRegex(ValueError,"secrets"):
                auto.run(self.story,self.root/"out",live=True)

    def test_budget_preflight(self):
        with self.assertRaisesRegex(ValueError,"Budget"):
            auto.run(self.story,self.root/"out",live=False,max_attempts=2,request_budget=2)

    def test_approved_scenes(self):
        with patch.dict("os.environ",{"CLOUDFLARE_API_TOKEN":"test","CLOUDFLARE_ACCOUNT_ID":"a"*32}):
            r=auto.run(self.story,self.root/"out",live=True,max_attempts=1,request_budget=2,
                director=lambda *a:"Photorealistic gas, deep sky, strong space composition and luminous clouds",
                generator=lambda *a:fake_jpeg(),
                vision=lambda *a:{"decision":"PASS","evidence":"Visible gas clouds and starlight"})
        self.assertEqual(r["completed_requests"],2)
        self.assertEqual(r["vision_requests"],2)
        self.assertTrue(r["all_scenes_approved"])
        self.assertTrue(all(s["candidates"][0]["status"]=="approved" for s in r["scenes"]))

    def test_ambiguous_vision_must_reject(self):
        with patch.dict("os.environ",{"CLOUDFLARE_API_TOKEN":"test","CLOUDFLARE_ACCOUNT_ID":"a"*32}):
            r=auto.run(self.story,self.root/"out",live=True,max_attempts=1,request_budget=2,
                director=lambda *a:"Photorealistic gas, deep sky, strong space composition and luminous clouds",
                generator=lambda *a:fake_jpeg(),
                vision=lambda *a:{"decision":"UNSURE","evidence":"Cannot see object"})
        self.assertFalse(r["all_scenes_approved"])
        self.assertTrue(all(s["status"]=="needs_human_review" for s in r["scenes"]))

    def test_retry_only_once(self):
        calls=[]
        def supervisor(*a):
            calls.append(1)
            return {"decision":"PASS" if len(calls)%2==0 else "FAIL",
                    "evidence":"Visible ground inconsistent with described gas"}
        with patch.dict("os.environ",{"CLOUDFLARE_API_TOKEN":"test","CLOUDFLARE_ACCOUNT_ID":"a"*32}):
            r=auto.run(self.story,self.root/"out",live=True,max_attempts=2,request_budget=4,
                director=lambda *a:"Photorealistic gas, deep sky, strong space composition and luminous clouds",
                generator=lambda *a:fake_jpeg(),vision=supervisor)
        self.assertEqual(r["completed_requests"],4)
        self.assertTrue(r["all_scenes_approved"])
        self.assertEqual(r["scenes"][0]["candidates"][0]["status"],"generated")
        self.assertEqual(r["scenes"][0]["candidates"][1]["status"],"approved")

    def test_response_parser_no_trusting_ambiguous(self):
        with patch.object(auto,"_request",return_value={"answer":"It looks good."}):
            r=auto.evaluate_image(fake_jpeg(),"A gas world","View of gaseous planet","a"*32,"tok")
        self.assertEqual(r["decision"],"UNSURE")
        with patch.object(auto,"_request",return_value={"answer":"DECISION: FAIL\nEVIDENCE: A mountain on a gas world."}):
            r=auto.evaluate_image(fake_jpeg(),"A gas world","View of gaseous planet","a"*32,"tok")
        self.assertEqual(r["decision"],"FAIL")

    def test_nested_moondream_response_is_read(self):
        self.assertEqual(auto._extract_text({"result":{"answer":"DECISION: PASS\\nEVIDENCE: Visible gas clouds."}}),
                         "DECISION: PASS\\nEVIDENCE: Visible gas clouds.")
        self.assertEqual(auto._extract_text({"output":{"answer":"A bright planet"}}),"A bright planet")
        self.assertEqual(auto._extract_text({"choices":[{"message":{"content":"Visible star"}}]}),"Visible star")

    def test_moondream_unknown_shape_rejected_with_gemma_fallback(self):
        with patch.object(auto,"_request",return_value={"unexpected_response":{"stuff":"not image evidence"}}):
            with patch("scripts.vision_gemma.evaluate_gemma",
                       return_value={"decision":"UNSURE","evidence":"Unknown visual evidence",
                                     "response_keys":["usage"]}) as fallback:
                result=auto.evaluate_image(fake_jpeg(),"Gas giant","Space planet","a"*32,"tok")
        self.assertEqual(result["decision"],"UNSURE")
        self.assertIn("usage",result["response_keys"])
        fallback.assert_called_once()

    def test_planner_uses_narration_not_hardcoded_kelt(self):
        with patch.object(auto,"_request",return_value={"response":"An ultra-realistic science documentary still of water droplets in rain, high contrast natural lighting, crisp foreground."}):
            prompt=auto.plan_scene("Raindrops form from water vapor.","Weather","", "a"*32,"tok")
            self.assertIn("rain",prompt)
            self.assertNotIn("KELT",prompt)

if __name__=="__main__":
    unittest.main()
