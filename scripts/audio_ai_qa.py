"""Optional, paid-API-free audio QC using CPU Whisper and Silero VAD.

Independent of the synthesis timestamps: does not silently rewrite subtitles,
claim a voice sounds natural, or publish a video.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path
from difflib import SequenceMatcher


def normalized_words(text):
    if not isinstance(text, str):
        raise TypeError("Text must be a string")
    return re.findall(r"[a-z0-9]+", text.casefold().translate(str.maketrans(
        "áéíóúüñ", "aeiouun")))


def word_accuracy(expected, detected):
    a,b=normalized_words(expected),normalized_words(detected)
    if not a: raise ValueError("Expected narration is empty")
    return round(SequenceMatcher(None,a,b,autojunk=False).ratio(),4)


def pcm16(path):
    """FFmpeg outputs exactly 16 kHz, mono, 16-bit little-endian samples."""
    p=Path(path)
    if not p.is_file() or p.stat().st_size < 48:
        raise ValueError("Audio is missing or empty")
    if p.stat().st_size > 75*1024*1024:
        raise ValueError("Audio is too large for free CPU CI")
    proc=subprocess.run([
        "ffmpeg","-hide_banner","-loglevel","error","-nostdin",
        "-i",str(p),"-vn","-ac","1","-ar","16000",
        "-f","s16le","pipe:1"
    ],capture_output=True,timeout=90,check=True)
    import numpy as np
    data=np.frombuffer(proc.stdout,dtype="<i2").astype("float32")/32768.0
    if not 8000 < len(data) <= 16000*180:
        raise ValueError("Speech clip duration outside 0.5-180s")
    return data


def assess(path, expected, *, transcription=None, speech_segments=None,
           whisper_model="tiny", download_root=None):
    """Use injected outputs in offline unit tests. Real run executes both AIs."""
    if not isinstance(expected,str) or not expected.strip():
        raise ValueError("Narration is required")
    if len(expected)>4000: raise ValueError("Narration too long")
    audio=pcm16(path)
    duration=round(len(audio)/16000,3)
    if speech_segments is None:
        from silero_vad import load_silero_vad,get_speech_timestamps
        vad=load_silero_vad(onnx=True)
        segments=get_speech_timestamps(
            audio,vad,sampling_rate=16000,return_seconds=True,
            min_speech_duration_ms=100)
    else:
        segments=speech_segments
    spans=[]
    for item in segments:
        a,b=float(item["start"]),float(item["end"])
        if not 0<=a<b<=duration+.04: raise ValueError("Invalid VAD segment")
        if spans and a<spans[-1]["end"]-.02: raise ValueError("Overlapping speech")
        spans.append({"start":round(a,3),"end":round(min(duration,b),3)})
    if transcription is None:
        from faster_whisper import WhisperModel
        model=WhisperModel(whisper_model,device="cpu",compute_type="int8",
                           cpu_threads=2,download_root=download_root)
        pieces,info=model.transcribe(
            audio,language="es",beam_size=2,
            word_timestamps=True,vad_filter=False,
            condition_on_previous_text=False)
        items=list(pieces)
        detected=" ".join(x.text.strip() for x in items)
        words=[{"start":round(float(w.start),3),
                "end":round(float(w.end),3),"word":w.word.strip()}
               for seg in items for w in (seg.words or [])
               if w.start is not None and w.end is not None]
    else:
        detected=transcription
        words=[]
    accuracy=word_accuracy(expected,detected)
    total_speech=sum(x["end"]-x["start"] for x in spans)
    leading=spans[0]["start"] if spans else duration
    trailing=duration-spans[-1]["end"] if spans else duration
    # Tiny Whisper can make mistakes in Spanish; this is NOT a definitive
    # verdict. Long-silence or poor transcript triggers human review.
    warnings=[]
    if not spans: warnings.append("No speech detected by independent VAD")
    if leading>.8: warnings.append("Excessive leading silence")
    if trailing>1.0: warnings.append("Excessive trailing silence")
    # A missed opening word is a real editing problem even when most of
    # the script is correct. Any appreciable discrepancy requires review;
    # do not silently change the approved narration from ASR output.
    if accuracy<.98: warnings.append("Transcription differs from reference")
    if not words and transcription is None:
        warnings.append("No word-level timestamps from Whisper")
    return {
        "schema":1,"engines":{
            "transcription":"faster-whisper / CPU int8 / "+whisper_model,
            "speech_detection":"Silero VAD ONNX CPU"
        },"locale":"es",
        "source_file":Path(path).name,
        "duration_s":duration,"speech_s":round(total_speech,3),
        "speech_segments":spans,"recognized_text":detected,
        "expected_text":expected,
        "word_match_ratio":accuracy,"whisper_words":words,
        "leading_silence_s":round(leading,3),
        "trailing_silence_s":round(trailing,3),
        "warnings":warnings,
        "review_needed":bool(warnings),
        "scientific_facts_verified":False,
        "voice_quality_approved":False,
        "ready_to_publish":False,"youtube_enabled":False
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--audio",required=True)
    p.add_argument("--expected",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--model",choices=("tiny","base"),default="tiny")
    a=p.parse_args()
    result=assess(a.audio,a.expected,whisper_model=a.model)
    dst=Path(a.out);dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("AUDIO_QA",result["word_match_ratio"],
          "REVIEW",result["review_needed"],"PUBLISH",False)


if __name__=="__main__":main()
