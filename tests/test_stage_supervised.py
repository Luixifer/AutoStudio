"""Stage only image candidates explicitly approved by the visual supervisor."""
import hashlib
import io
from PIL import Image, ImageDraw
import json
from pathlib import Path
import tempfile
import unittest
from scripts.stage_supervised import stage_supervised

def jpg(w):
    # Fully decodable and visually different fixtures; a JPEG header alone
    # cannot exercise real pixel-level QA.
    im = Image.new("RGB", (w, 512), (10, 10, 10))
    draw = ImageDraw.Draw(im)
    if w % 2:
        draw.rectangle((5, 5, w//3, 480), fill=(240, 240, 240))
    else:
        draw.rectangle((w//2, 5, w-5, 480), fill=(240, 240, 240))
    sink = io.BytesIO()
    im.save(sink, format="JPEG", quality=95)
    return sink.getvalue()

class ApprovedStagingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.story=self.root/"story.json"
        self.story.write_text(json.dumps({"schema":3,"format":"short","title":"Two scenes",
             "editorial_approved":False,"youtube":{"enabled":False},
             "scenes":[{"image":"old1.jpg","narration":"A glowing gas world is visible."},
                       {"image":"old2.jpg","narration":"The star appears behind the gas."}]}))
        self.manifest=self.root/"visual-supervision-manifest.json"
        self.scenes=[]
        for i in [1,2]:
            blob=jpg(512+i)
            filename=f"scene_{i:02}_v1.jpg"
            (self.root/filename).write_bytes(blob)
            self.scenes.append({"scene":i,"approved":True,"candidates":[{
                 "variant":1,"status":"approved","file":filename,
                 "sha256":hashlib.sha256(blob).hexdigest(),
                 "dimensions":[512+i,512],"vision":{"decision":"PASS","evidence":"Visible."}}]})
        self.write()

    def write(self,approved=True):
        self.manifest.write_text(json.dumps({"schema":2,"mode":"live",
                    "all_scenes_approved":approved,"scenes":self.scenes}))

    def test_stages_only_approved(self):
        result=stage_supervised(self.story,self.manifest,self.root/"staged")
        self.assertEqual(result["scenes"],2)
        self.assertTrue((self.root/"staged"/"auto-scene-01.jpg").exists())
        doc=json.loads((self.root/"staged"/"storyboard.json").read_text())
        self.assertEqual(doc["scenes"][0]["rights"]["license"],"own_creation")

    def test_rejected_scene_blocks_all_staging(self):
        self.scenes[0]["approved"]=False
        self.write(False)
        with self.assertRaises(ValueError):
            stage_supervised(self.story,self.manifest,self.root/"staged")
        self.assertFalse((self.root/"staged").exists())

    def test_mismatched_approval_blocks(self):
        self.scenes[0]["candidates"][0]["vision"]["decision"]="FAIL"
        self.write()
        with self.assertRaises(ValueError):
            stage_supervised(self.story,self.manifest,self.root/"staged")

    def test_identical_pixels_different_jpeg_encoding_blocks(self):
        from io import BytesIO
        img = Image.open(io.BytesIO((self.root/"scene_01_v1.jpg").read_bytes()))
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=80)
        blob = buf.getvalue()
        second = self.root/"scene_02_v1.jpg"
        second.write_bytes(blob)
        candidate = self.scenes[1]["candidates"][0]
        candidate["sha256"] = hashlib.sha256(blob).hexdigest()
        candidate["dimensions"] = [513,512]
        self.write()
        with self.assertRaisesRegex(ValueError,"Perceptual image QA"):
            stage_supervised(self.story,self.manifest,self.root/"staged")
        self.assertFalse((self.root/"staged").exists())

    def test_low_information_does_not_auto_approve(self):
        img = Image.new("RGB",(514,512),(90,90,90))
        sink = io.BytesIO()
        img.save(sink,format="JPEG")
        blob=sink.getvalue()
        second=self.root/"scene_02_v1.jpg"
        second.write_bytes(blob)
        candidate=self.scenes[1]["candidates"][0]
        candidate["sha256"]=hashlib.sha256(blob).hexdigest()
        candidate["dimensions"]=[514,512]
        self.write()
        with self.assertRaisesRegex(ValueError,"Perceptual image QA"):
            stage_supervised(self.story,self.manifest,self.root/"staged")
        self.assertFalse((self.root/"staged").exists())

    def test_positive_staging_never_grants_editorial_approval(self):
        report=stage_supervised(self.story,self.manifest,self.root/"staged")
        self.assertEqual(report["perceptual_image_qa"]["pairs_checked"],1)
        self.assertFalse(report["human_visual_approved"])
        self.assertFalse(report["scientific_reviewed"])

if __name__=="__main__":
    unittest.main()
