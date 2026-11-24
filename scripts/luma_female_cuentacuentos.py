"""Two Castilian female narration samples, matching Alvaro bedtime pacing."""
import asyncio,json,subprocess,tempfile,wave
from pathlib import Path
import edge_tts
OUT=Path("out/luma-mujeres-cuentacuentos")
SEGMENTS=[
("Érase una vez, en un bosque lleno de secretos, una pequeña luciérnaga llamada Luma.","normal"),
("Vivía en una acogedora casita escondida entre las raíces de un viejo roble.","long"),
("Cada noche, Luma contemplaba las estrellas desde una colina.","short"),
("¡Qué bonitas eran!","expressive"),
("Y siempre deseaba lo mismo: poder brillar tanto como ellas.","end")]
PAUSES={"normal":.60,"long":.82,"short":.43,"expressive":.64,"end":.70}
def ffmpeg(*args):
    subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",*map(str,args)],check=True)
async def render(key,voice):
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);pcm=bytearray()
        for i,(line,pause) in enumerate(SEGMENTS):
            part=root/f"{i:02}.mp3";raw=root/f"{i:02}.raw"
            await edge_tts.Communicate(line,voice=voice,rate="-13%",pitch="-2Hz").save(str(part))
            if not part.exists() or part.stat().st_size<1000:raise RuntimeError("Missing audio for "+voice)
            ffmpeg("-i",part,"-f","s16le","-ac","1","-ar","24000",raw)
            pcm.extend(raw.read_bytes())
            pcm.extend(bytes(int(PAUSES[pause]*24000*2)))
        wav=OUT/(key+".wav")
        with wave.open(str(wav),"wb") as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(pcm)
        mp3=OUT/(key+".mp3")
        ffmpeg("-i",wav,"-codec:a","libmp3lame","-qscale:a","3",mp3);wav.unlink()
        return {"file":mp3.name,"voice":voice,"seconds":round(len(pcm)/48000,1)}
async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    catalog=await edge_tts.list_voices()
    available={v["ShortName"]:v for v in catalog if v["Locale"]=="es-ES" and v["Gender"]=="Female"}
    print("AVAILABLE_ES_ES_FEMALE",sorted(available))
    preferred=["es-ES-ElviraNeural","es-ES-AbrilNeural","es-ES-VeraNeural","es-ES-IreneNeural","es-ES-LiaNeural"]
    names=[v for v in preferred if v in available][:2]
    if len(names)<2:names=list(available)[:2]
    if len(names)<2:raise RuntimeError("Fewer than 2 native es-ES female voices")
    results=[]
    for name in names:
        try:
            result=await render(f"{len(results)+1:02}_{name.split('-')[-1].replace('Neural','').lower()}_cuentacuentos",name)
            print("VOICE_OK",result);results.append(result)
        except Exception as e:print("VOICE_FAILED",name,repr(e))
    if len(results)<1:raise RuntimeError("No samples were generated")
    (OUT/"manifest.json").write_text(json.dumps({"pauses":PAUSES,"samples":results,"text":[x[0] for x in SEGMENTS]},ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":asyncio.run(main())
