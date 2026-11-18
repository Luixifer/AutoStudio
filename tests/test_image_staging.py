"""Tests for staging actual generated images against the real schema-3 storyboard."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from scripts.image_staging import stage_generated_images

def jpeg(w=512, h=512):
    # Minimal marker stream for header parser only; not a decodable photograph.
    return (b"\xff\xd8\xff\xc0\x00\x11\x08"
            + h.to_bytes(2, "big") + w.to_bytes(2, "big")
            + b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
            + b"\xff\xd9")

class ImageStagingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        storyboard={"schema":3,"format":"short","title":"KELT-9b","editorial_approved":True,
                    "youtube":{"enabled":False},"scenes":[{"image":"old.jpg","narration":"Scientific narration sample."},
                     {"image":"old2.jpg","narration":"A different sample."}]}
        self.story=self.root/"story.json"
        self.story.write_text(json.dumps(storyboard))
        self.manifest=self.root/"manifest.json"
        entries=[]
        for i in (1,2):
            raw=jpeg(512+i,512)
            path=self.root/f"scene_{i:02}_v1.jpg"
            path.write_bytes(raw)
            entries.append({"scene":i,"candidates":[{"variant":1,"status":"generated","file":path.name,
                                                    "sha256":hashlib.sha256(raw).hexdigest(),"dimensions":[512+i,512]}]})
        self.manifest.write_text(json.dumps({"provider":"cloudflare-flux-schnell",
                                             "completed_requests":2,"scenes":entries}))

    def test_stage_real_schema(self):
        result=stage_generated_images(self.story,self.manifest,self.root/"out")
        self.assertEqual(result["scenes"],2)
        doc=json.loads((self.root/"out"/"storyboard.json").read_text())
        self.assertFalse(doc["editorial_approved"])
        self.assertEqual(doc["scenes"][0]["rights"]["license"],"own_creation")
        self.assertTrue((self.root/"out"/"auto-scene-01.jpg").exists())

    def test_missing_image_rejected(self):
        (self.root/"scene_02_v1.jpg").unlink()
        with self.assertRaises(ValueError):
            stage_generated_images(self.story,self.manifest,self.root/"out")

    def test_changed_bytes_rejected(self):
        (self.root/"scene_01_v1.jpg").write_bytes(jpeg(768,512))
        with self.assertRaisesRegex(ValueError,"integrity"):
            stage_generated_images(self.story,self.manifest,self.root/"out")

    def test_dry_run_rejected(self):
        doc=json.loads(self.manifest.read_text())
        doc["provider"]="dry-run"
        self.manifest.write_text(json.dumps(doc))
        with self.assertRaises(ValueError):
            stage_generated_images(self.story,self.manifest,self.root/"out")

if __name__=="__main__":
    unittest.main()
