"""Personal voice comparison for KELT-9b, with exact source narration.

No video or claims of human equivalence. Preserve spoken lexical text; phonetic
workarounds must be reviewed rather than silently changing subtitles.
"""
import argparse
import hashlib
import json
import subprocess
import wave
from pathlib import Path

# Exact paragraphs from the personal KELT-9b storyboard. Editorial spelling
# already says 'nueve be' to keep pronunciation consistent.
LINES=[
    "¿Te imaginas un planeta tan caliente que supera la temperatura de algunas estrellas?",
    "Se llama KELT nueve be. Es un gigante gaseoso, y parece salido del mismísimo infierno.",
    "En su cara iluminada, la temperatura ronda los cuatro mil trescientos grados Celsius.",
    "No hay océanos de lava que pisar: es un mundo gigante hecho principalmente de gas.",
    "El calor es tan brutal que puede separar las moléculas de hidrógeno en átomos.",
]
SAMPLE_TEXT=" ".join(LINES)
PRESETS=(
    ("dora-narrativa","ef_dora",0.97,0.23,0.10),
    ("dora-dinamica","ef_dora",1.06,0.15,0.06),
    ("alex-narrativo","em_alex",0.99,0.22,0.09),
)

def validate_wave(path):
    import numpy as np
    with wave.open(str(path),"rb") as wavefile:
        rate=wavefile.getframerate()
        frames=wavefile.getnframes()
        raw=wavefile.readframes(frames)
        channels=wavefile.getnchannels()
        bits=wavefile.getsampwidth()
    if channels!=1 or bits!=2 or not (20000<=rate<=48000):
        raise ValueError("Audio format unsupported.")
    samples=np.frombuffer(raw,dtype="<i2").astype(np.float32)/32768
    seconds=len(samples)/rate
    if not 10<=seconds<=70:
        raise ValueError("Duration unreasonable.")
    peak=float(np.max(np.abs(samples)))
    rms=float(np.sqrt(np.mean(samples*samples)))
    if not .002<=rms<=.65 or peak>.999:
        raise ValueError("Silent, clipping or unreasonably loud audio.")
    return {"seconds":round(seconds,2),"rms":round(rms,4),"peak":round(peak,4),"sample_rate":rate}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    from scripts.neural_narration import NeuralNarrator,words_from_phonemes
    import numpy as np
    narrator=NeuralNarrator()
    voices=set(narrator.engine.get_voices())
    args.out.mkdir(parents=True,exist_ok=True)
    summary=[]
    for title,voice,speed,sentence_pause,clause_pause in PRESETS:
        if voice not in voices:
            print("VOICE_UNAVAILABLE",voice)
            continue
        samples,rate,spoken=narrator.engine.create_timed(
            SAMPLE_TEXT,voice=voice,lang="es",speed=speed,trim=True,
            sentence_pause=sentence_pause,clause_pause=clause_pause)
        words=words_from_phonemes(SAMPLE_TEXT,spoken)
        if len(words)<40 or not np.all(np.isfinite(samples)):
            raise ValueError("Phoneme alignment or sample values invalid.")
        # Master voice sample in WAV; AAC copy for easy phone audition.
        samples=np.clip(samples,-.98,.98)
        wav=args.out/(title+".wav")
        with wave.open(str(wav),"wb") as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate)
            f.writeframes((samples*32767).astype("<i2").tobytes())
        metrics=validate_wave(wav)
        mp3=args.out/(title+".mp3")
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(wav),
                        "-af","loudnorm=I=-16:TP=-2:LRA=9","-codec:a","libmp3lame",
                        "-q:a","3",str(mp3)],check=True,timeout=60)
        if not mp3.is_file() or mp3.stat().st_size<15000:
            raise ValueError("MP3 not generated.")
        data={"file":mp3.name,"label":title,"voice":voice,"speed":speed,
              "sentence_pause":sentence_pause,"clause_pause":clause_pause,
              "source_text":SAMPLE_TEXT,"metrics":metrics,
              "phoneme_words":len(words),
              "sha256":hashlib.sha256(mp3.read_bytes()).hexdigest(),
              "human_naturalness_reviewed":False}
        summary.append(data)
        print("VOICE_PREVIEW",title,metrics["seconds"],"seconds",metrics["rms"],"RMS")
    if len(summary)<2:
        raise RuntimeError("At least two neural voice candidates must be produced.")
    report={"scope":"KELT-9b personal voice audition","language":"es",
            "ready_for_youtube":False,"status":"awaiting_human_audition",
            "candidates":summary}
    (args.out/"comparison.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    (args.out/"LEEME.txt").write_text(
        "AUTO STUDIO · COMPARACIÓN DE VOCES KELT-9b\n"
        "Escucha los MP3 en el Samsung, preferiblemente con auriculares.\n"
        "El guion es exactamente el mismo para cada voz. No se ha aprobado para YouTube.\n"
        "Evalúa pronunciación de KELT nueve be, naturalidad, energía y pausas.\n",
        encoding="utf-8")

if __name__=="__main__":
    main()
