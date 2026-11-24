"""Luma: Ximena v2, measured emotional pauses; no publishing or paid API."""
import asyncio,json,subprocess,tempfile,wave
from pathlib import Path
import edge_tts

OUT=Path("out/luma-ximena-v2")
VOICE="es-ES-XimenaNeural"
# Original story text preserved exactly; breaks only where a real storyteller breathes.
LINES=[
 ("Érase una vez,", "opening"),
 ("en un bosque lleno de secretos,", "mystery"),
 ("una pequeña luciérnaga llamada Luma.", "sentence"),
 ("Vivía en una acogedora casita escondida entre las raíces de un viejo roble.", "scene"),
 ("Cada noche, Luma contemplaba las estrellas desde una colina.", "anticipation"),
 ("¡Qué bonitas eran!", "wonder"),
 ("Y siempre deseaba lo mismo:", "wish"),
 ("poder brillar tanto como ellas.", "ending"),
]
TAKES=[
 ("01_ximena_v2_natural", "-12%", "-2Hz", {"opening":.32,"mystery":.47,"sentence":.52,"scene":.76,"anticipation":.42,"wonder":.48,"wish":.29,"ending":.90}),
 ("02_ximena_v2_magica", "-14%", "-2Hz", {"opening":.49,"mystery":.64,"sentence":.57,"scene":.84,"anticipation":.58,"wonder":.66,"wish":.42,"ending":1.08}),
 ("03_ximena_v3_pausas_emotivas", "-14%", "-2Hz", {"opening":.70,"mystery":.90,"sentence":1.50,"scene":1.70,"anticipation":.90,"wonder":1.20,"wish":.80,"ending":1.40})
]
def ffmpeg(*args):
 subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",*map(str,args)],check=True)
async def render(name,rate,pitch,pauses):
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);data=bytearray()
  for i,(text,kind) in enumerate(LINES):
   mp3=root/f"{i:02}.mp3";raw=root/f"{i:02}.pcm"
   await edge_tts.Communicate(text,voice=VOICE,rate=rate,pitch=pitch).save(str(mp3))
   if not mp3.exists() or mp3.stat().st_size<1000:raise RuntimeError(f"Voice failed on segment {i}: {text}")
   ffmpeg("-i",mp3,"-f","s16le","-ac","1","-ar","24000",raw)
   data.extend(raw.read_bytes());data.extend(bytes(round(pauses[kind]*48000)))
  wav=OUT/f"{name}.wav"
  with wave.open(str(wav),"wb") as f:
   f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(data)
  target=OUT/f"{name}.mp3"
  ffmpeg("-i",wav,"-c:a","libmp3lame","-q:a","3",target)
  wav.unlink()
  if target.stat().st_size<10000:raise RuntimeError("Output too small")
  report={"file":target.name,"duration_seconds":round(len(data)/48000,2),"voice":VOICE,"rate":rate,"pitch":pitch,"pauses":pauses}
  print("SAMPLE_OK",report)
  return report
async def main():
 OUT.mkdir(parents=True,exist_ok=True)
 catalog=await edge_tts.list_voices()
 assert any(v["ShortName"]==VOICE and v["Locale"]=="es-ES" for v in catalog),"Ximena not available as es-ES"
 results=[]
 for name,rate,pitch,pauses in TAKES:
  try:results.append(await render(name,rate,pitch,pauses))
  except Exception as e:print("SAMPLE_FAILED",name,repr(e))
 if not results:raise RuntimeError("All variants failed")
 (OUT/"manifest.json").write_text(json.dumps({"text":" ".join(x[0] for x in LINES),"samples":results},ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":asyncio.run(main())
