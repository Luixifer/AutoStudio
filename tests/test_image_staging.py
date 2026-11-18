"""Tests for staging actual generated images against the real schema-3 storyboard."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from scripts.image_staging import stage_generated_images

def png(w=512,h=512):
    return b"\x89PNG\r\n\x1a\n"+b"\x00\x00\x00\rIHDR"+struct.pack(">II",w,h)+b"\x08\x02\x00\x00\x00"+b"\x00"*4

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
            raw=png(512+i,512)
            path=self.root/f"scene_{i:02}_v1.png"
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
        self.assertTrue((self.root/"out"/"auto-scene-01.png").exists())

    def test_missing_image_rejected(self):
        (self.root/"scene_02_v1.png").unlink()
        with self.assertRaises(ValueError):
            stage_generated_images(self.story,self.manifest,self.root/"out")

    def test_changed_bytes_rejected(self):
        (self.root/"scene_01_v1.png").write_bytes(png(768,512))
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
