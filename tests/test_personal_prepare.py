"""A single storyboard + pictures must automatically become valid Alex+subtitle input."""
import json
import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from PIL import Image
from scripts.personal_prepare import camera_for,prepare
from scripts.personal_studio import load_project

class TestNarrator:
    def synthesize(self,text,target):
        rate=16000;seconds=6.2
        tone=14+(sum(ord(c) for c in text)%13)\n        with wave.open(str(target),"wb") as output:
            output.setnchannels(1);output.setsampwidth(2);output.setframerate(rate)
            output.writeframes(b"".join(struct.pack("<h",int(2500*math.sin(i/tone)))
                                        for i in range(int(rate*seconds))))
        words=text.split()
        return {"voice":"em_alex","words":[
            {"word":w,"start":i*seconds/len(words),
             "end":(i+1)*seconds/len(words)-.005}
            for i,w in enumerate(words)]}


class SingleClickTests(unittest.TestCase):
    def test_input_images_to_verified_voice_package(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);scenes=[]
            for i in range(3):
                pic=p/f"original{i}.png"
                Image.new("RGB",(750,1300),(30+30*i,100,120)).save(pic)
                scenes.append({
                    "image":pic.name,
                    "heading":"PLANETA EXTREMO",
                    "narration":"Un planeta extraordinario puede sorprendernos desde una galaxia muy lejana. Escena número "+str(i+1)+".",
                    "rights":{"license":"original_user"}
                })
            data={"schema":3,"format":"short","language":"es","youtube":{"enabled":False},
                  "title":"Tres fenómenos espaciales","scenes":scenes}
            source=p/"storyboard.json";source.write_text(json.dumps(data,ensure_ascii=False))
            result=prepare(source,p/"out",narrator=TestNarrator())
            project=load_project(result)
            self.assertEqual(len(project["scenes"]),3)
            self.assertEqual(project["format"],"short")
            self.assertFalse(project["youtube_enabled"])
            self.assertFalse(project["editorial_approved"])
            self.assertEqual([s["camera"]["movement"] for s in project["scenes"]],
                             ["zoom_in","pan_right","focus"])
            self.assertTrue(all(Path(s["audio_path"]).is_file() for s in project["scenes"]))

    def test_no_silent_fallback_to_wrong_voice(self):
        class WrongVoice(TestNarrator):
            def synthesize(self,text,target):
                output=super().synthesize(text,target)
                output["voice"]="ef_dora"
                return output
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            for i in range(2):
                Image.new("RGB",(750,1300),(i*20+10,20,30)).save(p/f"{i}.png")
            scenes=[{"image":f"{i}.png","narration":"Un relato especial acerca de fenómenos misteriosos en el cielo.",
                     "rights":{"license":"original_user"}} for i in range(2)]
            inputpath=p/"source.json"
            inputpath.write_text(json.dumps({"schema":3,"title":"Misterios del cosmos",
                 "format":"short","language":"es","youtube":{"enabled":False},
                 "scenes":scenes}))
            with self.assertRaisesRegex(ValueError,"Álex"):
                prepare(inputpath,p/"out",narrator=WrongVoice())

    def test_motions_are_deterministic(self):
        self.assertEqual(camera_for(0,{})["movement"],"zoom_in")
        self.assertEqual(camera_for(1,{})["movement"],"pan_right")
        self.assertEqual(camera_for(5,{})["movement"],"zoom_in")

if __name__=="__main__":unittest.main()
