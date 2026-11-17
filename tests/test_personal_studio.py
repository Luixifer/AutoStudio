"""Offline contract checks for personal Short/documentary project safety."""
import json
import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from PIL import Image
from scripts.personal_studio import validate_project,secure_file
from scripts.personal_editor import caption_groups,zoom_filter,srt_time,ass_time,write_ass


def make_sample(root,kind="lab",count=2,seconds=3.2):
    root=Path(root)
    script="Una estrella ilumina el espacio con energía extraordinaria."
    words=script.split()
    scenes=[]
    for index in range(count):
        image=root/f"image{index}.png"
        Image.new("RGB",(500+index,350),(20+index*10,40,100)).save(image)
        wav=root/f"audio{index}.wav"
        with wave.open(str(wav),"wb") as output:
            output.setnchannels(1);output.setsampwidth(2);output.setframerate(16000)
            # Independent acoustic waveform; no claim of speech content.
            output.writeframes(b"".join(
                struct.pack("<h",round(2000*math.sin(2*math.pi*(220+index*40)*j/16000)))
                for j in range(round(seconds*16000))))
        timing=[{"word":word,"start":j*seconds/len(words),
                 "end":(j+1)*seconds/len(words)-.008}
                for j,word in enumerate(words)]
        scenes.append({
            "heading":"Estrella", "narration":script,
            "image":image.name,"audio":wav.name,"timed_words":timing,
            "camera":{"movement":"pan_left" if index%2 else "zoom_in",
                      "target":[.42,.48],"zoom":1.08},
            "rights":{"license":"own_creation"},"source_type":"illustration"
        })
    return {"schema":2,"format":kind,"language":"es","title":"Ciencia y estrellas",
            "editorial_approved":False,"youtube":{"enabled":False},"scenes":scenes}


class PersonalContractTests(unittest.TestCase):
    def test_lab_preview_with_exact_times_and_assets(self):
        with tempfile.TemporaryDirectory() as root:
            doc=make_sample(root)
            check=validate_project(root,doc,allow_lab=True)
            self.assertEqual(len(check["scenes"]),2)
            self.assertFalse(check["youtube_enabled"])
            self.assertFalse(check["editorial_approved"])

    def test_documentary_profile_accepts_long_form_but_not_20_seconds(self):
        with tempfile.TemporaryDirectory() as root:
            doc=make_sample(root,kind="documentary",count=8,seconds=35)
            check=validate_project(root,doc)
            self.assertEqual(check["format"],"documentary")
            self.assertEqual(check["profile"]["size"],[1280,720])
            self.assertGreater(check["estimated_seconds"],180)

    def test_no_unreviewed_youtube_or_unknown_rights(self):
        with tempfile.TemporaryDirectory() as root:
            doc=make_sample(root)
            doc["youtube"]["enabled"]=True
            with self.assertRaises(ValueError):validate_project(root,doc,allow_lab=True)
            doc["youtube"]["enabled"]=False
            doc["scenes"][0]["rights"]["license"]="found_online"
            with self.assertRaises(ValueError):validate_project(root,doc,allow_lab=True)

    def test_traversal_and_duplicate_images_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            doc=make_sample(root)
            doc["scenes"][1]["image"]="../outside.png"
            with self.assertRaises(ValueError):validate_project(root,doc,allow_lab=True)
            doc=make_sample(root)
            doc["scenes"][1]["image"]=doc["scenes"][0]["image"]
            with self.assertRaises(ValueError):validate_project(root,doc,allow_lab=True)

    def test_mismatched_caption_transcript_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            doc=make_sample(root)
            doc["scenes"][0]["timed_words"][0]["word"]="Otra"
            with self.assertRaises(ValueError):validate_project(root,doc,allow_lab=True)

    def test_bad_focal_point_and_movement_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            doc=make_sample(root)
            doc["scenes"][0]["camera"]["target"]=[1.2,.2]
            with self.assertRaises(ValueError):validate_project(root,doc,allow_lab=True)
            doc=make_sample(root)
            doc["scenes"][0]["camera"]["movement"]="teleport"
            with self.assertRaises(ValueError):validate_project(root,doc,allow_lab=True)

    def test_caption_chunking_covers_every_word(self):
        words=[{"word":w,"start":i*.25,"end":i*.25+.23}
               for i,w in enumerate("Un planeta imposible delante de una estrella.".split())]
        cues=caption_groups(words)
        self.assertEqual(" ".join(c["text"] for c in cues),
                         "Un planeta imposible delante de una estrella.")
        self.assertTrue(all(len(c["text"].split())<=3 for c in cues))

    def test_pan_zooms_keep_short_and_long_resolution(self):
        for resolution in [(720,1280),(1280,720)]:
            for movement in ("zoom_in","zoom_out","pan_left","pan_right","focus","static"):
                scene={"camera":{"movement":movement,"zoom":1.08,"target":[.5,.5]}}
                filter_text=zoom_filter(scene,120,resolution)
                self.assertIn(f"s={resolution[0]}x{resolution[1]}",filter_text)
                self.assertIn("format=yuv420p",filter_text)

    def test_ass_events_are_separate_lines_and_fixed_over_image(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"caption.ass"
            cues=[{"start":.25,"end":1.1,"text":"Una aurora"},
                  {"start":1.3,"end":2.6,"text":"muy brillante"}]
            write_ass(path,cues,[720,1280],"AURORA BOREAL",3.2)
            lines=path.read_text(encoding="utf-8").splitlines()
            events=[line for line in lines if line.startswith("Dialogue: ")]
            self.assertEqual(len(events),4)
            self.assertTrue(any(",Heading," in line for line in events))
            self.assertTrue(any(",Disclosure," in line for line in events))
            self.assertTrue(any("Una aurora" in line for line in events))
            self.assertFalse(any("\\\\nDialogue:" in line for line in events))

    def test_timecode_correct(self):
        self.assertEqual(srt_time(63.123),"00:01:03,123")
        self.assertEqual(ass_time(63.12),"0:01:03.12")

if __name__=="__main__":unittest.main()
