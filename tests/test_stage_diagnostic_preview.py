"""Preview mode is explicitly non-publishable and preserves QC rejection."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from scripts.stage_diagnostic_preview import stage_preview

def jpeg(w):
    return (b"\xff\xd8\xff\xc0\x00\x11\x08"
         +(512).to_bytes(2,"big")+w.to_bytes(2,"big")
         +b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
         +b"\xff\xd9"+b"\x00"*8)

class DiagnosticPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.story=self.base/"story.json"
        self.story.write_text(json.dumps({"schema":3,"scenes":[{"image":f"prior{i}.png",
                  "narration":f"Scene {i} describes cosmic gas."} for i in range(1,11)]}))
        self.manifest=self.base/"visual-supervision-manifest.json"
        self.entries=[]
        for i in range(1,11):
            raw=jpeg(512+i)
            name=f"scene_{i:02d}_v1.jpg"
            (self.base/name).write_bytes(raw)
            decision="FAIL" if i==1 else "PASS"
            self.entries.append({"scene":i,"candidates":[{"variant":1,"file":name,
                "sha256":hashlib.sha256(raw).hexdigest(),"dimensions":[512+i,512],
                "status":"generated" if i==1 else "approved",
                "vision":{"decision":decision,"evidence":"An inspected frame"}}]})
        self.write()

    def write(self):
        self.manifest.write_text(json.dumps({"schema":2,"mode":"live",
              "completed_requests":10,"scenes":self.entries}))

    def test_preview_preserves_fail_without_approving(self):
        out=self.base/"preview"
        r=stage_preview(self.story,self.manifest,out)
        self.assertFalse(r["ready_to_publish"])
        self.assertFalse(r["human_visual_approved"])
        self.assertEqual(r["source_image_qa"]["1"],"FAIL")
        self.assertTrue((out/"auto-scene-01.jpg").exists())
        doc=json.loads((out/"storyboard.json").read_text())
        self.assertFalse(doc["editorial_approved"])
        self.assertFalse(doc["youtube"]["enabled"])

    def test_hash_tampering_rejected(self):
        self.entries[3]["candidates"][0]["sha256"]="0"*64
        self.write()
        with self.assertRaisesRegex(ValueError,"integrity"):
            stage_preview(self.story,self.manifest,self.base/"preview")

if __name__=="__main__":
    unittest.main()
