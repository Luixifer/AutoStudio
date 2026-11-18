"""Non-destructive cinematic polish tests: focal composition and scientific cautions."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image,ImageDraw
from scripts.personal_cinematic import cinematic_grade,fit_for_camera,source_image_report
from scripts.personal_editor import zoom_filter,background_still


class CinematicPolishTests(unittest.TestCase):
    def test_grade_retains_geometry_and_does_not_claim_ai_generation(self):
        image=Image.new("RGB",(720,1280),(18,33,65))
        draw=ImageDraw.Draw(image)
        draw.ellipse((170,380,550,760),fill=(225,125,42))
        unchanged=cinematic_grade(image,0)
        graded=cinematic_grade(image)
        self.assertEqual(graded.size,(720,1280))
        self.assertEqual(unchanged.getpixel((200,400)),image.getpixel((200,400)))
        self.assertNotEqual(graded.getpixel((200,400)),image.getpixel((200,400)))
        with self.assertRaises(ValueError):cinematic_grade(image,1.5)

    def test_fit_near_vertical_and_wide_image_with_focal(self):
        near=Image.new("RGB",(720,1280),(30,70,140))
        wide=Image.new("RGB",(1280,720),(30,70,140))
        frame,full=fit_for_camera(near,720,1280,(.7,.4))
        self.assertTrue(full)
        self.assertEqual(frame.size,(720,1280))
        frame,full=fit_for_camera(wide,720,1280,(.7,.4))
        self.assertFalse(full)
        self.assertEqual(frame.size,(720,1280))
        with self.assertRaises(ValueError):
            fit_for_camera(near,720,1280,(2,.4))

    def test_dark_illustrations_warn_without_false_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"dark.png"
            Image.new("RGB",(720,1280),(0,0,0)).save(path)
            report=source_image_report(path)
            self.assertTrue(report["warnings"])
            self.assertFalse(report["artistic_quality_verified"])
            self.assertGreater(report["dark_fraction"],.9)

    def test_focal_camera_motion_respects_point_of_interest(self):
        a={"camera":{"movement":"pan_right","zoom":1.12,"target":[.25,.45]}}
        b={"camera":{"movement":"pan_right","zoom":1.12,"target":[.75,.45]}}
        fa=zoom_filter(a,300,[720,1280],fps=60)
        fb=zoom_filter(b,300,[720,1280],fps=60)
        self.assertNotEqual(fa,fb)
        self.assertIn("clip(",fa)
        self.assertIn("fps=60",fa)
        self.assertIn("cos(PI*",fa)

    def test_focus_is_a_real_smooth_approach(self):
        focus={"camera":{"movement":"focus","zoom":1.12,"target":[.7,.45]}}
        still={"camera":{"movement":"static","zoom":1.12,"target":[.7,.45]}}
        focused=zoom_filter(focus,300,[720,1280],fps=60)
        stationary=zoom_filter(still,300,[720,1280],fps=60)
        self.assertNotEqual(focused,stationary)
        self.assertIn("1+(1.12-1)",focused)
        self.assertIn("cos(PI*",focused)

    def test_output_still_keeps_requested_size(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            Image.new("RGB",(720,1280),(30,90,120)).save(p/"input.jpg")
            meta=background_still(p/"input.jpg",p/"output.jpg",720,1280,
                                  "PLANETA","illustration",focal=(.65,.45))
            with Image.open(p/"output.jpg") as image:
                self.assertEqual(image.size,(720,1280))
            self.assertTrue(meta["full_bleed"])
            self.assertEqual(meta["focal"],[.65,.45])


if __name__=="__main__":unittest.main()
