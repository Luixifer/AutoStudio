"""Local image analysis quality controls must be bounded and non-semantic."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image,ImageDraw
from scripts.personal_camera import suggest_focal_point,dhash,visual_similarity_warnings
from scripts.personal_prepare import camera_for

class CameraPlanningTests(unittest.TestCase):
    def test_default_focal_is_bounded_and_deterministic(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"picture.png"
            im=Image.new("RGB",(600,900),(10,13,35))
            draw=ImageDraw.Draw(im)
            for x in range(220,440,20):
                for y in range(300,520,20):
                    draw.rectangle((x,y,x+8,y+8),fill=(225,156,38))
            im.save(path)
            a=suggest_focal_point(path)
            b=suggest_focal_point(path)
            self.assertEqual(a,b)
            self.assertTrue(.15<=a["target"][0]<=.85)
            self.assertTrue(.15<=a["target"][1]<=.75)
            self.assertIn(a["confidence"],("low","medium"))
            plan=camera_for(0,{},path)
            self.assertEqual(plan["target"],a["target"])

    def test_manual_camera_always_wins(self):
        with tempfile.TemporaryDirectory() as folder:
            image=Path(folder)/"image.png"
            Image.new("RGB",(500,700),(30,80,90)).save(image)
            camera={"movement":"pan_left","target":[.3,.4],"zoom":1.04}
            self.assertEqual(camera_for(9,{"camera":camera},image),camera)
            self.assertEqual(camera_for(4,{"focal_point":[.2,.6]},image)["target"],[.2,.6])

    def test_resized_duplicate_warning_without_false_licensing_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/"a.png";b=Path(folder)/"b.png";c=Path(folder)/"c.png"
            img=Image.new("RGB",(480,720),(40,65,120))
            ImageDraw.Draw(img).ellipse((30,45,450,580),fill=(180,90,50))
            img.save(a);img.resize((600,900)).save(b)
            img2=Image.new("RGB",(480,720),(70,180,20))
            ImageDraw.Draw(img2).rectangle((40,140,430,300),fill=(220,40,95))
            img2.save(c)
            self.assertEqual(dhash(a),dhash(b))
            warnings=visual_similarity_warnings([a,b,c])
            self.assertTrue(any(w["scene_a"]==1 and w["scene_b"]==2 for w in warnings))

if __name__=="__main__":unittest.main()
