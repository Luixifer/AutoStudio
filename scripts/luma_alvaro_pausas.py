"""Luma: two Castilian narrator takes with intentional sentence pauses."""
import asyncio, json, subprocess, tempfile, wave
from pathlib import Path
import edge_tts

OUT=Path("out/luma-alvaro-pausas")
VOICE="es-ES-AlvaroNeural"
SEGMENTS=[
    ("Érase una vez, en un bosque lleno de secretos, una pequeña luciérnaga llamada Luma.", "normal"),
    ("Vivía en una acogedora casita escondida entre las raíces de un viejo roble.", "long"),
    ("Cada noche, Luma contemplaba las estrellas desde una colina.", "short"),
    ("¡Qué bonitas eran!", "expressive"),
    ("Y siempre deseaba lo mismo: poder brillar tanto como ellas.", "end"),
]
STYLES=[
    ("01_alvaro_natural", "-9%", {"normal":.43,"long":.62,"short":.33,"expressive":.43,"end":.5}),
    ("02_alvaro_cuentacuentos", "-13%", {"normal":.60,"long":.82,"short":.43,"expressive":.64,"end":.7})
]
def ffmpeg(*args):
    subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",*map(str,args)],check=True)
async def take(name, rate, pauses):
    # Each sentence is spoken as a complete prosodic unit, followed by measured silence.
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)
        pcm=bytearray()
        for i,(text,kind) in enumerate(SEGMENTS):
            mp3=root/f"{i:02}.mp3"
            raw=root/f"{i:02}.raw"
            await edge_tts.Communicate(text,voice=VOICE,rate=rate,pitch="-2Hz").save(str(mp3))
            if not mp3.exists() or mp3.stat().st_size<1000: raise RuntimeError(f"Missing speech at sentence {i}")
            ffmpeg("-i",mp3,"-f","s16le","-ac","1","-ar","24000",raw)
            pcm.extend(raw.read_bytes())
            pcm.extend(b"\0"*int(24000*2*pauses[kind]))
        wav=OUT/(name+".wav")
        with wave.open(str(wav),"wb") as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(pcm)
        mp3=OUT/(name+".mp3")
        ffmpeg("-i",wav,"-codec:a","libmp3lame","-qscale:a","3",mp3)
        wav.unlink()
        print("SAMPLE_OK",name,round(len(pcm)/48000,2),"sec",mp3.stat().st_size,"bytes")
        return {"file":mp3.name,"seconds":round(len(pcm)/48000,2),"rate":rate,"pauses":pauses}
async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    samples=[]
    for name,rate,pauses in STYLES:
        samples.append(await take(name,rate,pauses))
    (OUT/"manifest.json").write_text(json.dumps({"voice":VOICE,"segments":[x[0] for x in SEGMENTS],"samples":samples},ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":asyncio.run(main())
