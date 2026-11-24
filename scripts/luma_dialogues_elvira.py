"""Luma dialogue tests: Ximena narrates, Elvira plays Nuba.

Strictly preserves the story words; page 5 and 8 Nuba lines Elvira,
page 10 Luma line Ximena. Isolated scenes only for review.
"""
import asyncio, json, subprocess, tempfile, wave
from pathlib import Path
import edge_tts

OUT=Path("out/luma-dialogos-elvira")
RATE=24000
NARRATOR=("es-ES-XimenaNeural","-9%","-1Hz",0.97)
NUBA=("es-ES-ElviraNeural","-13%","-2Hz",0.97)
SCENES={
 5:[
  ("narradora","Llegó a un jardín donde las flores eran más altas que los árboles de su casa. De repente, escuchó una vocecita:",0.42),
  ("nuba","¡Socorro! ¿Hay alguien ahí?",0.65)
 ],
 8:[
  ("nuba","¡Gracias, Luma!",0.22),
  ("narradora","exclamó Nuba. Y justo entonces ocurrió algo extraño: la pequeña luz de Luma brilló un poquito más. ¡Qué sorpresa se llevó!",0.65)
 ],
 10:[
  ("luma","No tengas miedo",0.22),
  ("narradora","susurró Luma. Aunque ella también estaba asustada, respiró profundamente, levantó sus antenas y comenzó a iluminar el camino.",0.65)
 ]
}

def ffmpeg(*args):
 subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",*map(str,args)],check=True)

async def generate(text, voice, target):
 profile=NUBA if voice=="nuba" else NARRATOR
 v,rate,pitch,tempo=profile
 exc=None
 for attempt in range(3):
  try:
   await edge_tts.Communicate(text,voice=v,rate=rate,pitch=pitch).save(str(target))
   if target.stat().st_size<1600:raise RuntimeError("empty audio")
   return tempo
  except Exception as e:
   exc=e
   if attempt<2:await asyncio.sleep(1+attempt*2)
 raise RuntimeError(f"Could not synthesize {voice}: {exc}")

async def main():
 OUT.mkdir(parents=True,exist_ok=True)
 voices={v["ShortName"] for v in await edge_tts.list_voices() if v["Locale"]=="es-ES"}
 for v in [NARRATOR[0],NUBA[0]]:
  if v not in voices:raise RuntimeError("Voice unavailable: "+v)
 master=bytearray();manifest=[]
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp)
  for page,parts in SCENES.items():
   pcm_all=bytearray();lines=[]
   for i,(speaker,line,pause) in enumerate(parts):
    source=root/f"p{page}_{i}.mp3";raw=root/f"p{page}_{i}.pcm"
    tempo=await generate(line,speaker,source)
    ffmpeg("-i",source,"-af",f"atempo={tempo}","-f","s16le","-ac","1","-ar",str(RATE),raw)
    data=raw.read_bytes()
    if len(data)<RATE*2//2:raise RuntimeError("Audio unexpectedly short")
    if speaker in ("nuba","luma"):
     spoken=OUT/f"pagina_{page:02}_dialogo_{speaker}.mp3"
     ffmpeg("-f","s16le","-ar",str(RATE),"-ac","1","-i",raw,"-c:a","libmp3lame","-q:a","3",spoken)
    pcm_all.extend(data); pcm_all.extend(bytes(round(RATE*2*pause)))
    lines.append({"speaker":speaker,"text":line,"post_pause":pause,"duration":round(len(data)/(RATE*2),2)})
   raw_full=root/f"page_{page}.pcm";raw_full.write_bytes(pcm_all)
   target=OUT/f"pagina_{page:02}_escena_dos_voces.mp3"
   ffmpeg("-f","s16le","-ar",str(RATE),"-ac","1","-i",raw_full,"-c:a","libmp3lame","-q:a","3",target)
   master.extend(pcm_all);master.extend(bytes(RATE*2*1))
   manifest.append({"page":page,"filename":target.name,"seconds":round(len(pcm_all)/(RATE*2),2),"segments":lines})
   print("PAGE_OK",page,target.stat().st_size,flush=True)
  full=root/"all.pcm";full.write_bytes(master)
  demo=OUT/"escenas_05_08_10_con_elvira.mp3"
  ffmpeg("-f","s16le","-ar",str(RATE),"-ac","1","-i",full,"-c:a","libmp3lame","-q:a","3",demo)
 (OUT/"manifest.json").write_text(json.dumps({"narrator":"Ximena","nuba":"Elvira","luma":"Ximena (provisional)","scenes":manifest,"reference":"14-page complete story"},ensure_ascii=False,indent=2),encoding="utf-8")
 print("FINAL_OK",demo.stat().st_size,round(len(master)/(RATE*2),2),flush=True)

if __name__=="__main__": asyncio.run(main())
