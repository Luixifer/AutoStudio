"""Video QA fails closed on technical errors and reports editorial uncertainty.

These automated signal checks cannot decide whether storytelling, narration,
factual assertions, imagery or licensing are subjectively excellent.
"""
import array
import hashlib
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path


def inspect_production(path,project,shots,srt):
    path=Path(path)
    if not path.is_file() or path.stat().st_size<10_000:
        raise ValueError("No se ha generado un MP4 válido.")
    info=json.loads(subprocess.check_output([
        "ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)
    ],text=True,timeout=30))
    errors=[];warnings=list(project["warnings"])
    video=[s for s in info["streams"] if s.get("codec_type")=="video"]
    audio=[s for s in info["streams"] if s.get("codec_type")=="audio"]
    if len(video)!=1 or len(audio)!=1:
        raise ValueError("Se requiere un único vídeo y una única pista de audio.")
    v,a=video[0],audio[0]
    want=project["profile"]["size"]
    actual=[v["width"],v["height"]]
    if actual!=want:errors.append("Resolución distinta del perfil.")
    if v.get("codec_name")!="h264" or v.get("pix_fmt")!="yuv420p":
        errors.append("Vídeo sin H264/yuv420p.")
    if Fraction(v["avg_frame_rate"])!=25:errors.append("FPS incorrectos.")
    if a.get("codec_name")!="aac" or int(a.get("sample_rate",0))!=48000:
        errors.append("Audio sin AAC/48 kHz.")
    seconds=float(info["format"]["duration"])
    if not project["profile"]["hard_seconds"][0]-.75<=seconds<=project["profile"]["hard_seconds"][1]+.75:
        errors.append("Duración fuera de perfil.")
    if abs(seconds-project["estimated_seconds"])>max(.8,.015*seconds):
        errors.append("La duración del MP4 no coincide con la narración.")
    if len(shots)!=len(project["scenes"]):
        errors.append("Hay escenas o imágenes perdidas.")
    text=Path(srt).read_text(encoding="utf-8")
    expected=sum(len(s["timed_words"]) for s in project["scenes"])
    grouped=sum(s["caption_groups"] for s in shots)
    if text.count(" --> ")!=grouped or grouped==0 or expected<grouped:
        errors.append("Subtítulos incompletos o incoherentes.")
    if path.stat().st_size<10000:errors.append("Tamaño de MP4 anómalo.")
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(path),
                    "-f","null","-"],check=True,timeout=300,
                   stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    pcm=subprocess.check_output(["ffmpeg","-v","error","-i",str(path),
                                 "-map","0:a:0","-ac","1","-ar","16000",
                                 "-f","s16le","-"],timeout=180)
    samples=array.array("h");samples.frombytes(pcm)
    if not samples:raise ValueError("No se puede decodificar el sonido.")
    rms=math.sqrt(sum(x*x for x in samples)/len(samples))/32768
    peak=max(abs(x) for x in samples)/32768
    clipped=sum(abs(x)>=32760 for x in samples)/len(samples)
    if rms<.004:errors.append("Audio demasiado bajo o silencioso.")
    if clipped>.001:errors.append("Clipping de audio.")
    # A 100-ms RMS window prevents a missing scene from being masked by the
    # average loudness of the rest; short intended pauses remain permitted.
    gaps=[];current=0;count=0
    for start in range(0,len(samples),1600):
        chunk=samples[start:start+1600]
        if not chunk:continue
        sound=math.sqrt(sum(x*x for x in chunk)/len(chunk))/32768
        if sound<.00055:
            count+=1
        else:
            if count>=18:gaps.append(round(count/10,1))
            count=0
    if count>=18:gaps.append(round(count/10,1))
    if gaps:warnings.append("Silencios largos detectados: "+str(gaps))
    # No YouTube publishing, even on a technically perfect video.
    return {
        "status":("rejected" if errors else "technical_pass_editorial_review_required"),
        "technical_passed":not errors,"editorial_approved":project["editorial_approved"],
        "youtube_enabled":False,"ready_to_publish":False,
        "voice_human_reviewed":False,"visual_human_reviewed":False,
        "science_reviewed_by_renderer":False,"errors":errors,"warnings":warnings,
        "video":str(path),"seconds":round(seconds,3),"size":actual,
        "shots":shots,"subtitle_words":expected,"subtitle_cues":grouped,
        "audio_metrics":{"rms":round(rms,5),"peak":round(peak,5),
                         "clipped_fraction":round(clipped,7),"long_silences":gaps},
        "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "review_instructions":"Escuchar voz y revisar datos, licencias, imágenes y título antes de subir manualmente.",
    }
