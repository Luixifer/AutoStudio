"""Deterministic visual checks: no OCR and no claims of photorealism."""
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image,ImageDraw
from scripts.personal_visual_audit import palette_features,image_distance,build_sheet

class VisualAuditUnitTests(unittest.TestCase):
    def test_solid_color_nearly_zero_texture(self):
        im=Image.new("RGB",(240,426),(0,0,0))
        f=palette_features(im)
        self.assertEqual(f["very_dark_fraction"],1)
        self.assertLess(f["std_luminance"],1)
        self.assertLess(f["edge_mean"],4)

    def test_strikingly_different_illustrations_measure_differently(self):
        a=Image.new("RGB",(240,426),(19,38,99))
        b=Image.new("RGB",(240,426),(245,160,44))
        draw=ImageDraw.Draw(a)
        draw.ellipse((40,130,200,300),fill=(230,90,40))
        draw=ImageDraw.Draw(b)
        draw.rectangle((60,100,170,340),fill=(15,15,44))
        self.assertGreater(image_distance(a,b),30)
        self.assertLess(image_distance(a,a),.01)

    def test_contact_sheet_persists_all_shots(self):
        with tempfile.TemporaryDirectory() as tmp:
            pictures=[Image.new("RGB",(240,426),(i*40,30,160)) for i in range(5)]
            target=Path(tmp)/"sheet.jpg"
            build_sheet(pictures,[str(i) for i in range(5)],target,"short")
            with Image.open(target) as im:
                self.assertEqual(im.size[0],4*(240+14)+14)
                self.assertGreater(im.size[1],2*426)
                im.verify()

    def test_format_rejected_if_no_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                build_sheet([],[],Path(tmp)/"sheet.jpg","short")

if __name__=="__main__":unittest.main()
