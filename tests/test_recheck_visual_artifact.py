"""No FLUX regeneration: vision fallback and replay integrity."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import visual_autopilot as auto
from scripts.recheck_visual_artifact import replay

def fake_jpeg(w=512):
    return (b"\xff\xd8\xff\xc0\x00\x11\x08"
        +(512).to_bytes(2,"big")+w.to_bytes(2,"big")
        +b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
        +b"\xff\xd9"+b"\x00"*8)

class ReplayTests(unittest.TestCase):
    def test_caption_fallback_compares_visible_content(self):
        responses=[{"answer":""},{"caption":"A gaseous planet near a bright star."},
            {"response":"DECISION: PASS\nEVIDENCE: Caption describes a gas planet near a star."}]
        with patch.object(auto,"_request",side_effect=responses) as req:
            verdict=auto.evaluate_image(fake_jpeg(),"A gas planet near a star","A giant gaseous globe", "a"*32,"token")
        self.assertEqual(req.call_count,3)
        self.assertEqual(verdict["decision"],"PASS")
        self.assertEqual(verdict["method"],"caption_plus_text_comparison")

    def test_empty_caption_fails_closed(self):
        with patch.object(auto,"_request",side_effect=[{"answer":""},{"caption":None}]):
            with patch("scripts.vision_gemma.evaluate_gemma",
                return_value={"decision":"UNSURE","evidence":"No readable result"}) as fallback:
                verdict=auto.evaluate_image(fake_jpeg(),"Gas","A gas planet","a"*32,"token")
        self.assertEqual(verdict["decision"],"UNSURE")
        fallback.assert_called_once()

    def test_replay_reuses_hashed_image(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);blob=fake_jpeg()
            (p/"scene_01_v1.jpg").write_bytes(blob)
            doc={"schema":2,"mode":"live","scenes":[{"narration":"A planet circles a star.",
                "image_prompt":"An orbiting gaseous planet.",
                "candidates":[{"file":"scene_01_v1.jpg","dimensions":[512,512],
                "sha256":hashlib.sha256(blob).hexdigest()}]}]}
            m=p/"visual-supervision-manifest.json";m.write_text(json.dumps(doc))
            with patch.dict("os.environ",{"CLOUDFLARE_ACCOUNT_ID":"a"*32,"CLOUDFLARE_API_TOKEN":"tok"}):
                with patch("scripts.vision_gemma.evaluate_gemma",return_value={"decision":"FAIL","evidence":"Ground is visible"}) as check:
                    result=replay(m,p/"out.json")
            self.assertEqual(check.call_count,1)
            self.assertEqual(result["new_images_generated"],0)
            self.assertEqual(result["verdict"]["decision"],"FAIL")

    def test_tampered_source_not_replayed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"scene_01_v1.jpg").write_bytes(fake_jpeg())
            m=p/"visual-supervision-manifest.json"
            m.write_text(json.dumps({"schema":2,"mode":"live","scenes":[{
                "narration":"Sky","image_prompt":"Planet","candidates":[{
                "file":"scene_01_v1.jpg","dimensions":[512,512],"sha256":"0"*64}]}]}))
            with self.assertRaisesRegex(ValueError,"verification"):
                replay(m,p/"out.json")

if __name__=="__main__":
    unittest.main()
