"""Different scene concepts must not collapse back into the same drawing."""
import unittest
from scripts.preview_visuals import ROLES,scene_visual_signature,draw_scene_art

class VisualVariationTests(unittest.TestCase):
    def test_distinct_signatures(self):
        self.assertEqual(len({scene_visual_signature(role) for role in ROLES}),len(ROLES))
    def test_unknown_role_is_rejected(self):
        with self.assertRaises(ValueError): scene_visual_signature("ADN")
    def test_distinct_pixels_when_pillow_is_installed(self):
        try:
            from PIL import Image,ImageDraw
        except ImportError:
            self.skipTest("Pillow optional for pure unit tests")
        signatures=[]
        for role in ROLES:
            image=Image.new("RGB",(720,1280),(0,0,0))
            draw_scene_art(ImageDraw.Draw(image),role)
            signatures.append(image.crop((0,95,720,585)).tobytes())
        self.assertEqual(len(set(signatures)),len(ROLES))

if __name__=="__main__": unittest.main()
