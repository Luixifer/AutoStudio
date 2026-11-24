"""Luma / Nuba page 5: three tests of a restrained cry with Elvira.

The neural voice cannot truly whisper or scream on command. These samples
explore an urgent plea followed by a quieter tentative question, with measured
pauses and gentle EQ. They are private audition samples, not production-ready.
"""
import asyncio
import json
import subprocess
import tempfile
from pathlib import Path

import edge_tts

OUT=Path("out/luma-nuba-socorro-contenido")
VOICE="es-ES-ElviraNeural"
NARRATOR="es-ES-XimenaNeural"
INTRO="Llegó a un jardín donde las flores eran más altas que los árboles de su casa. De repente, escuchó una vocecita:"
# Each option keeps the SAME spoken words.
PRESETS=[
 {"id":"01_nuba_miedo_contenido","intro_rate":"-9%","first_rate":"+4%","first_pitch":"+7Hz","second_rate":"-13%","second_pitch":"-4Hz","pause":0.35,"first_gain":0.72,"second_gain":0.58,
  "description":"Urgent, restrained call followed by hesitant quiet question"},
 {"id":"02_nuba_susurro_asustado","intro_rate":"-9%","first_rate":"-10%","first_pitch":"+2Hz","second_rate":"-19%","second_pitch":"-8Hz","pause":0.55,"first_gain":0.62,"second_gain":0.48,
  "description":"More fragile and tentative, with a longer listen-for-an-answer pause"},
 {"id":"03_nuba_socorro_urgente","intro_rate":"-9%","first_rate":"+9%","first_pitch":"+10Hz","second_rate":"-11%","second_pitch":"-6Hz","pause":0.43,"first_gain":0.85,"second_gain":0.52,
  "description":"More urgent initial call with an abrupt drop to a soft question"},
]
def ffmpeg(*args):
 subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",*map(str,args)],check=True)

async def say(text,voice,rate,pitch,path):
 err=None
 for retry in range(3):
  try:
   await edge_tts.Communicate(text,voice=voice,rate=rate,pitch=pitch).save(str(path))
   if path.stat().st_size<2000:raise RuntimeError("synthesis produced no audio")
   return
  except Exception as exc:
   err=exc
   if retry<2:await asyncio.sleep(1.5*(retry+1))
 raise RuntimeError(str(err))

def pcm_convert(source,target,volume=1.0):
 # Modest high-pass/low-pass give a close, light voice without claiming true whispering.
 ffmpeg("-i",source,"-af",f"highpass=f=100,lowpass=f=8000,volume={volume}","-f","s16le","-ar","24000","-ac","1",target)
 data=target.read_bytes()
 if len(data)<24000:raise RuntimeError("very short spoken segment")
 return data

def encode(data,raw_path,mp3_path):
 raw_path.write_bytes(data)
 ffmpeg("-f","s16le","-ar","24000","-ac","1","-i",raw_path,"-c:a","libmp3lame","-q:a","3",mp3_path)
 if mp3_path.stat().st_size<2000:raise RuntimeError("MP3 invalid")

async def main():
 OUT.mkdir(parents=True,exist_ok=True)
 cat=await edge_tts.list_voices()
 known={v["ShortName"] for v in cat if v.get("Locale")=="es-ES"}
 if not {VOICE,NARRATOR}.issubset(known):raise RuntimeError("Requested es-ES voices unavailable")
 manifest=[]
 with tempfile.TemporaryDirectory() as dirname:
  temp=Path(dirname)
  narration=temp/"intro.mp3"
  await say(INTRO,NARRATOR,"-9%","-1Hz",narration)
  intro_data=pcm_convert(narration,temp/"intro.pcm",0.94)
  for preset in PRESETS:
   name=preset["id"]
   first=temp/(name+"_first.mp3")
   second=temp/(name+"_second.mp3")
   await say("¡Socorro!",VOICE,preset["first_rate"],preset["first_pitch"],first)
   await say("¿Hay alguien ahí?",VOICE,preset["second_rate"],preset["second_pitch"],second)
   a=pcm_convert(first,temp/(name+"_first.pcm"),preset["first_gain"])
   b=pcm_convert(second,temp/(name+"_second.pcm"),preset["second_gain"])
   gap=bytes(round(preset["pause"]*24000*2))
   spoken=a+gap+b
   only=OUT/(name+".mp3")
   encode(spoken,temp/(name+"_line.raw"),only)
   # Allow Ximena to introduce Nuba, with a separate quiet transition.
   full=intro_data+bytes(round(.42*24000*2))+spoken
   scene=OUT/(name+"_escena05.mp3")
   encode(full,temp/(name+"_scene.raw"),scene)
   record={"name":name,"dialogue":only.name,"scene":scene.name,"duration_dialogue":round(len(spoken)/48000,2),
    "duration_scene":round(len(full)/48000,2),"pause_between_calls":preset["pause"],"description":preset["description"]}
   print("SAMPLE_OK",json.dumps(record,ensure_ascii=False),flush=True)
   manifest.append(record)
 (OUT/"manifest.json").write_text(json.dumps({"narrator":NARRATOR,"nuba":VOICE,"text":"¡Socorro! ¿Hay alguien ahí?","samples":manifest,"note":"TTS emotional approximations, not genuine whisper/cry synthesis"},ensure_ascii=False,indent=2),encoding="utf-8")
 print("ALL_DONE",len(manifest))
if __name__=="__main__": asyncio.run(main())
