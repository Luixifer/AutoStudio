"""Create a clearly labeled non-publishable 9:16 research preview video.

Uses ONLY locally rendered schematic diagrams and eSpeak NG speech. This is
not cinematic footage, source-verified science or a YouTube-ready product.
Never reuses visuals from a different scientific topic.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

WIDTH, HEIGHT, FPS = 720, 1280, 25
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def validate_preview(package):
    if not isinstance(package, dict) or package.get("safe_for_render") is not False:
        raise ValueError("Solo se admiten expedientes de investigación pendientes de revisión.")
    draft=package.get("spanish_draft", {})
    scenes=draft.get("scenes", [])
    if draft.get("can_render") is not False or draft.get("approved") is not False:
        raise ValueError("El borrador no debe estar aprobado automáticamente.")
    if not isinstance(scenes, list) or not 3 <= len(scenes) <= 5:
        raise ValueError("Se necesitan entre 3 y 5 escenas del borrador limitado.")
    if package.get("topic") != "¿Qué ocurre dentro de un agujero negro?":
        # Intentional, explicit proof-of-concept limit. Not any-topic video.
        raise ValueError("Vista previa audiovisual limitada a la pregunta de demostración.")
    for scene in scenes:
        voice=scene.get("narration_draft_es","")
        url=scene.get("reference_url","")
        if not isinstance(voice,str) or not 25<=len(voice)<=480:
            raise ValueError("Narración no válida.")
        if url not in {
            "https://science.nasa.gov/universe/black-holes/anatomy/",
            "https://science.nasa.gov/universe/what-happens-when-something-gets-too-close-to-a-black-hole/",
            "https://science.nasa.gov/universe/black-holes/new-nasa-black-hole-visualization-takes-viewers-beyond-the-brink/",
        }:
            raise ValueError("Referencia externa no autorizada.")
    return scenes


def wrap(draw, words, font, max_width):
    result=[]
    current=""
    for word in words.split():
        proposal=(current+" "+word).strip()
        if current and draw.textbbox((0,0), proposal, font=font)[2] > max_width:
            result.append(current)
            current=word
        else:
            current=proposal
    if current:
        result.append(current)
    return result


def frame(scene, index, count, output):
    from PIL import Image, ImageDraw, ImageFont
    im=Image.new("RGB",(WIDTH,HEIGHT),(6,14,31))
    d=ImageDraw.Draw(im)
    normal=ImageFont.truetype(FONT_REGULAR,32)
    heading=ImageFont.truetype(FONT_BOLD,47)
    small=ImageFont.truetype(FONT_REGULAR,24)
    badge=ImageFont.truetype(FONT_BOLD,23)
    # Generic, original schematic; no NASA imagery and no claim of physical accuracy.
    cx,cy=WIDTH//2,330
    for radius,color in [(240,(18,46,73)),(196,(31,73,105)),(145,(47,95,131)),
                         (104,(221,129,57)),(93,(245,190,102)),(76,(5,10,20))]:
        d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=color)
    d.text((48,40),"AUTOSTUDIO 0.4 · PRUEBA",font=badge,fill=(185,209,238))
    d.rounded_rectangle((32,575,WIDTH-32,1150),radius=24,fill=(14,30,54))
    y=610
    for line in wrap(d,scene.get("role","Escena"),heading,WIDTH-100):
        d.text((52,y),line,font=heading,fill=(255,209,150));y+=60
    y+=28
    for line in wrap(d,scene["narration_draft_es"],normal,WIDTH-104):
        d.text((52,y),line,font=normal,fill=(232,239,246));y+=47
        if y>1040:
            raise ValueError("Texto de la escena demasiado largo para el vídeo.")
    d.text((52,1074),f"ESCENA {index}/{count}  ·  FUENTE NASA",font=small,fill=(168,194,222))
    d.rectangle((0,1170,WIDTH,HEIGHT),fill=(111,38,37))
    d.text((26,1192),"BORRADOR SIN REVISIÓN CIENTÍFICA",font=badge,fill=(255,255,255))
    d.text((30,1232),"Diagrama esquemático · NO PUBLICAR",font=small,fill=(255,234,222))
    im.save(output)


def produce(package, directory):
    scenes=validate_preview(package)
    for binary in ("ffmpeg","ffprobe","espeak-ng"):
        if not shutil.which(binary):
            raise RuntimeError("Falta una herramienta gratuita: "+binary)
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow no está instalado.") from exc
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    parts=[]
    durations=[]
    for i,scene in enumerate(scenes,1):
        still=directory/f"scene_{i:02}.png"
        audio=directory/f"scene_{i:02}.wav"
        video=directory/f"scene_{i:02}.mp4"
        frame(scene,i,len(scenes),still)
        subprocess.run(["espeak-ng","-v","es","-s","148","-w",str(audio),"--stdin"],
                       input=scene["narration_draft_es"],text=True,check=True,timeout=60)
        with wave.open(str(audio),"rb") as wav:
            seconds=wav.getnframes()/wav.getframerate()+.5
        if not 1<=seconds<=35:
            raise ValueError("Audio con duración anómala.")
        subprocess.run([
            "ffmpeg","-y","-loglevel","error",
            "-loop","1","-framerate",str(FPS),"-i",str(still),"-i",str(audio),
            "-t",str(round(seconds,3)),"-c:v","libx264","-preset","veryfast",
            "-pix_fmt","yuv420p","-c:a","aac","-b:a","96k",
            "-af","apad","-movflags","+faststart",str(video)
        ],check=True,timeout=120)
        parts.append(video)
        durations.append(seconds)
    manifest=directory/"concat.txt"
    manifest.write_text("".join("file '"+p.name+"'\n" for p in parts),encoding="utf-8")
    output=directory/"autostudio-black-hole-REVIEW-ONLY.mp4"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0",
                    "-i",str(manifest),"-c","copy","-movflags","+faststart",str(output)],
                   check=True,timeout=90)
    if not output.is_file() or output.stat().st_size<10000:
        raise RuntimeError("La vista previa no se ha generado correctamente.")
    report={
        "status":"experimental_unapproved_preview",
        "video_file":output.name,
        "scene_count":len(scenes),
        "estimated_seconds":round(sum(durations),2),
        "sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
        "scientifically_approved":False,
        "youtube_enabled":False,
        "paid_inference":False,
        "visuals":"Original non-scientific schematic cards, not footage or simulation",
        "audio":"eSpeak NG offline Spanish (experimental quality)",
        "references":[s["reference_url"] for s in scenes],
    }
    (directory/"preview-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("research_json",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    pkg=json.loads(args.research_json.read_text(encoding="utf-8"))
    report=produce(pkg,args.out)
    print(json.dumps(report,ensure_ascii=False))


if __name__=="__main__":
    main()
