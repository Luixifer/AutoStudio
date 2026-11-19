"""Regression tests for recovering a full ten-scene visual run without FLUX."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from scripts.recover_supervised_images import recover

def fake_jpeg(w):
    return (b"\xff\xd8\xff\xc0\x00\x11\x08"
        +(512).to_bytes(2,"big")+w.to_bytes(2,"big")
        +b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
        +b"\xff\xd9"+b"\x00"*8)

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.scenes=[]
        for i in range(1,11):
            b=fake_jpeg(512+i)
            name=f"scene_{i:02d}_v1.jpg"
            (self.root/name).write_bytes(b)
            passed=i not in (1,10)
            self.scenes.append({"scene":i,"narration":f"An important cosmic object appears in scene {i}.",
             "image_prompt":f"Cinematic depiction scene {i} with a shining gas planet.",
             "approved":passed,"status":"approved" if passed else "needs_human_review",
             "candidates":[{"variant":1,"file":name,"sha256":hashlib.sha256(b).hexdigest(),
                "dimensions":[512+i,512],"status":"approved" if passed else "generated",
                "vision":{"decision":"PASS" if passed else "UNSURE","evidence":"Image seen" if passed else "No answer"}}]})
        self.manifest=self.root/"visual-supervision-manifest.json"
        self.write()

    def write(self):
        self.manifest.write_text(json.dumps({"schema":2,"mode":"live",
            "completed_requests":10,"vision_requests":10,"scenes":self.scenes,
            "all_scenes_approved":False}))

    def test_only_two_reinspections_no_new_images(self):
        calls=[]
        def vision(img,narration,prompt,account,token):
            calls.append(narration)
            return {"decision":"PASS","evidence":"A distinct gas planet is clearly visible"}
        report=recover(self.manifest,self.root/"recovered",account="a"*32,token="test",reviewer=vision)
        self.assertEqual(len(calls),2)
        self.assertEqual(report["reinspection_requests"],2)
        self.assertEqual(report["new_image_requests"],0)
        self.assertEqual(report["vision_requests"],12)
        self.assertTrue(report["all_scenes_approved"])
        self.assertEqual(len(list((self.root/"recovered").glob("scene_*.jpg"))),10)
        self.assertEqual(report["scenes"][1]["candidates"][0]["vision"]["decision"],"PASS")
        self.assertEqual(report["scenes"][0]["candidates"][0]["original_vision"]["decision"],"UNSURE")

    def test_unsure_remains_blocked_with_all_images_preserved(self):
        def vision(*a):
            return {"decision":"UNSURE","evidence":"No usable model output"}
        result=recover(self.manifest,self.root/"failed",account="a"*32,token="test",reviewer=vision)
        self.assertFalse(result["all_scenes_approved"])
        self.assertEqual(sum(bool(s["approved"]) for s in result["scenes"]),8)
        self.assertEqual(len(list((self.root/"failed").glob("scene_*.jpg"))),10)

    def test_corrupted_sha_blocks_before_calls_and_writes(self):
        self.scenes[4]["candidates"][0]["sha256"]="0"*64
        self.write()
        calls=[]
        with self.assertRaisesRegex(ValueError,"hash"):
            recover(self.manifest,self.root/"recovered",account="a"*32,token="test",
                reviewer=lambda *a:calls.append(1))
        self.assertFalse(calls)
        self.assertFalse((self.root/"recovered").exists())

    def test_additional_unapproved_scene_does_not_bypass_gate(self):
        self.scenes[4]["approved"]=False
        self.scenes[4]["candidates"][0]["vision"]["decision"]="UNSURE"
        self.write()
        with self.assertRaisesRegex(ValueError,"additional"):
            recover(self.manifest,self.root/"recovered",account="a"*32,token="test",
                reviewer=lambda *a:{"decision":"PASS","evidence":"Fine"})

    def test_rejected_visual_stays_not_approved(self):
        def vision(*a):
            return {"decision":"FAIL","evidence":"Wrong kind of object is clearly visible"}
        r=recover(self.manifest,self.root/"failed",account="a"*32,token="test",reviewer=vision)
        self.assertFalse(r["all_scenes_approved"])
        self.assertTrue(all(not r["scenes"][i]["approved"] for i in (0,9)))

if __name__=="__main__":
    unittest.main()
