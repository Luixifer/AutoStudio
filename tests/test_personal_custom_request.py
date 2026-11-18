"""Protect against forged, oversized, duplicated or improperly licensed uploads."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image,ImageDraw
from scripts.personal_custom_request import load_request

REQUEST="0"*31+"1"

def fixture(root):
    base=Path(root)/"requests"/REQUEST
    base.mkdir(parents=True)
    scenes=[]
    for i in (1,2):
        filename=f"imagen-{i:02}.jpg"
        im=Image.new("RGB",(720,1280),(20*i,60*i,100))
        ImageDraw.Draw(im).ellipse((30*i,100*i,230*i,380*i),fill=(220,120,70))
        im.save(base/filename,quality=85)
        digest=hashlib.sha256((base/filename).read_bytes()).hexdigest()
        scenes.append({
          "narration":"Un mundo lejano lleno de misterios científicos que merecen una explicación.",
          "image":filename,"image_sha256":digest,
          "source_type":"illustration","rights":{"license":"original_user"},
        })
    document={"schema":3,"request_id":REQUEST,"title":"El universo extraordinario",
              "language":"es","format":"short","youtube":{"enabled":False},
              "scenes":scenes}
    (base/"storyboard.json").write_text(json.dumps(document,ensure_ascii=False))
    return base,document

class RequestValidationTests(unittest.TestCase):
    def test_valid_request_copies_only_approved_fields_and_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            base,document=fixture(tmp)
            document["untrusted_command"]="rm -rf /"
            (base/"storyboard.json").write_text(json.dumps(document))
            output=load_request(tmp,REQUEST,Path(tmp)/"output")
            data=json.loads(output.read_text(encoding="utf8"))
            self.assertNotIn("untrusted_command",data)
            self.assertEqual(len(data["scenes"]),2)
            self.assertFalse(data["editorial_approved"])
            self.assertTrue((output.parent/"imagen-01.jpg").is_file())

    def test_reject_wrong_id_and_modified_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            base,document=fixture(tmp)
            with self.assertRaises(ValueError):load_request(tmp,"../evil",Path(tmp)/"out")
            (base/"imagen-01.jpg").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError,"coincide"):load_request(tmp,REQUEST,Path(tmp)/"out")

    def test_reject_unlicensed_and_repeated_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            base,doc=fixture(tmp)
            doc["scenes"][1]["rights"]={"license":"unknown"}
            (base/"storyboard.json").write_text(json.dumps(doc))
            with self.assertRaises(ValueError):load_request(tmp,REQUEST,Path(tmp)/"out")
            doc["scenes"][1]["rights"]={"license":"original_user"}
            doc["scenes"][1]["image"]=doc["scenes"][0]["image"]
            (base/"storyboard.json").write_text(json.dumps(doc))
            with self.assertRaises(ValueError):load_request(tmp,REQUEST,Path(tmp)/"out")

    def test_reject_youtube_and_wrong_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            base,doc=fixture(tmp)
            doc["youtube"]["enabled"]=True
            (base/"storyboard.json").write_text(json.dumps(doc))
            with self.assertRaises(ValueError):load_request(tmp,REQUEST,Path(tmp)/"out")
            doc["youtube"]["enabled"]=False
            doc["scenes"][0]["image"]="../../other.jpg"
            (base/"storyboard.json").write_text(json.dumps(doc))
            with self.assertRaises(ValueError):load_request(tmp,REQUEST,Path(tmp)/"out")

if __name__=="__main__": unittest.main()
