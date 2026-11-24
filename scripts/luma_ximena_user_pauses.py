"""Ximena test: exact user-directed pauses for the opening of Luma."""
import asyncio
import json
import subprocess
import tempfile
import wave
from pathlib import Path
import edge_tts

VOICE="es-ES-XimenaNeural"
OUT=Path("out/luma-ximena-pausas-exactas")
RATE="-13%"
PITCH="-2Hz"
# Each silence starts at the end of the corresponding spoken phrase.
SEGMENTS=[
 ("Érase una vez", 0.7),
 ("en un bosque lleno de secretos", 0.7),
 ("una pequeña luciérnaga llamada", 0.1),
 ("Luma.", 0.2),
 ("Vivía", 0.1),
 ("en una acogedora casita escondida entre las raíces de un viejo roble.", 0.0),
]
SAMPLE_RATE=24000

def ffmpeg(*args):
    subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",*map(str,args)],check=True)

async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    data=bytearray()
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        for i,(line,seconds) in enumerate(SEGMENTS):
            mp3=root/f"{i:02}.mp3"
            raw=root/f"{i:02}.pcm"
            await edge_tts.Communicate(line,voice=VOICE,rate=RATE,pitch=PITCH).save(str(mp3))
            if mp3.stat().st_size<1000:raise RuntimeError("No audio for segment "+str(i))
            # Strip synthetic start/end gaps; keep the natural word endings, then
            # insert exactly the user-requested number of silent PCM samples.
            ffmpeg("-i",mp3,"-af","silenceremove=start_periods=1:start_duration=0:start_threshold=-48dB,areverse,silenceremove=start_periods=1:start_duration=0:start_threshold=-48dB,areverse",
                   "-f","s16le","-ac","1","-ar",str(SAMPLE_RATE),raw)
            chunk=raw.read_bytes()
            if len(chunk)<4000:raise RuntimeError("Empty segment "+str(i))
            data.extend(chunk)
            data.extend(bytes(round(seconds*SAMPLE_RATE*2)))
            print("SEGMENT_OK",i,line,"pause",seconds)
    wav=OUT/"ximena_pausas_0p7_0p7_0p1_0p2_0p1.wav"
    with wave.open(str(wav),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(SAMPLE_RATE);f.writeframes(data)
    mp3=OUT/"ximena_pausas_experimentales.mp3"
    ffmpeg("-i",wav,"-c:a","libmp3lame","-q:a","2",mp3)
    wav.unlink()
    manifest={"voice":VOICE,"rate":RATE,"pitch":PITCH,
              "segments":[{"text":text,"pause_after_seconds":pause} for text,pause in SEGMENTS],
              "duration_seconds":round(len(data)/(SAMPLE_RATE*2),3)}
    (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print("AUDIO_OK",mp3,mp3.stat().st_size,manifest["duration_seconds"])
if __name__=="__main__":
    asyncio.run(main())
