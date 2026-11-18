"""Camera regression: 50 fps, subpixel positions, genuine decoded motion."""
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageStat
from scripts.personal_editor import zoom_filter,CAMERA_SUPERSAMPLE,background_still
from scripts.personal_studio import PROFILES


class SmoothCameraTests(unittest.TestCase):
    def test_profiles_use_50_fps_and_four_times_source_pixels(self):
        for kind in ("short","documentary","lab"):
            self.assertEqual(PROFILES[kind]["fps"],50)
        self.assertEqual(CAMERA_SUPERSAMPLE,4)
        example={"camera":{"movement":"pan_right","zoom":1.09,"target":[.5,.45]}}
        vf=zoom_filter(example,150,[720,1280],fps=50)
        self.assertIn("format=yuv444p",vf)
        self.assertIn("fps=50",vf)
        self.assertIn("cos(PI*",vf)
        self.assertIn("s=720x1280",vf)

    def test_real_moving_frames_have_temporally_consistent_camera(self):
        # A high-contrast checkerboard reveals stop-start camera jumps.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            original=Image.new("RGB",(720,1280),(12,26,48))
            draw=ImageDraw.Draw(original)
            for x in range(0,720,17):
                draw.line((x,0,x,1280),fill=(198,130,70),width=2)
            for y in range(0,1280,29):
                draw.line((0,y,720,y),fill=(78,175,204),width=2)
            original.save(root/"original.png")
            background_still(root/"original.png",root/"large.jpg",
                             720*CAMERA_SUPERSAMPLE,1280*CAMERA_SUPERSAMPLE,
                             "CAMERA CHECK","illustration")
            scene={"camera":{"movement":"pan_right","zoom":1.12,"target":[.5,.5]}}
            filtergraph=zoom_filter(scene,125,[720,1280],fps=50)
            output=root/"camera.mp4"
            subprocess.run([
                "ffmpeg","-hide_banner","-loglevel","error","-y",
                "-loop","1","-framerate","50","-i",str(root/"large.jpg"),
                "-vf",filtergraph,"-frames:v","125",
                "-c:v","libx264","-preset","ultrafast","-crf","18",
                "-pix_fmt","yuv420p",str(output)
            ],check=True,timeout=120)
            probe=subprocess.check_output([
                "ffprobe","-v","error","-select_streams","v:0",
                "-show_entries","stream=avg_frame_rate,nb_frames",
                "-of","json",str(output)],text=True,timeout=20)
            import json
            info=json.loads(probe)["streams"][0]
            self.assertEqual(info["avg_frame_rate"],"50/1")
            self.assertEqual(int(info["nb_frames"]),125)
            # Decode raw frames and measure consecutive differences in a
            # stable central region. Motion is gradual, not jumps between
            # almost identical images separated by big discontinuities.
            raw=subprocess.check_output([
                "ffmpeg","-v","error","-i",str(output),
                "-vf","crop=200:200:240:400,scale=80:80",
                "-f","rawvideo","-pix_fmt","gray","-"],timeout=120)
            count=80*80
            self.assertEqual(len(raw),125*count)
            diffs=[]
            for i in range(1,125):
                a=raw[(i-1)*count:i*count]
                b=raw[i*count:(i+1)*count]
                diffs.append(sum(abs(x-y) for x,y in zip(a,b))/count)
            center=diffs[20:105]
            self.assertGreater(sum(x>0.12 for x in center),65)
            self.assertLess(max(center),5.0)
            self.assertLess(max(center),max(.5,sum(center)/len(center)*7))


if __name__=="__main__":
    unittest.main()
