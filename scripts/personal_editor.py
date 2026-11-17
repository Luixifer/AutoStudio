"""Personal AutoStudio audiovisual composer.

Input: schema-2 manifest + actual images, voice WAV and word timings.
No paid API and no YouTube publication. All movement occurs behind fixed,
synchronised captions; assets are checked before any encoding.
"""
import argparse
import hashlib
import json
import math
import os
import subprocess
import tempfile
from pathlib import Path

from scripts.personal_studio import load_project, summarize_project, sha256_file

FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def ffmpeg(*arguments,timeout=180):
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",*map(str,arguments)],
                   check=True,timeout=timeout)


def caption_groups(words,max_words=3):
    if not words:raise ValueError("Sin tiempos para subtítulos.")
    out=[];chunk=[]
    for word in words:
        chunk.append(word)
        if len(chunk)==max_words or word["word"].rstrip('”»"').endswith((".","?","!",":",";")):
            out.append(chunk)
            chunk=[]
    if chunk:out.append(chunk)
    return [{"start":part[0]["start"],"end":part[-1]["end"],
             "text":" ".join(w["word"] for w in part)} for part in out]


def subtitle_text(text):
    return str(text).replace("\\","\\\\").replace("{","").replace("}","").replace("\n"," ")

def ass_time(t):
    h=int(t//3600);m=int((t%3600)//60);s=t%60
    return f"{h}:{m:02}:{s:05.2f}"

def srt_time(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def write_ass(path,cues,size):
    width,height=size
    # Caption bar sits in a visually quiet lower band. Short 1-3-word groups.
    font_size=40 if height>width else 32
    margin_v=230 if height>width else 90
    header=f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,{font_size},&H00FFFFFF,&H0000FFFF,&H00100A08,&H9B000000,-1,0,0,0,100,100,0,0,1,3,1,2,50,50,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines=[header]
    for cue in cues:
        lines.append(f"Dialogue: 0,{ass_time(cue['start'])},{ass_time(cue['end']+.08)},Default,,0,0,0,,{subtitle_text(cue['text'])}\n")
    Path(path).write_text("".join(lines),encoding="utf-8")


def background_still(picture,out,width,height,heading,source_type):
    from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance
    with Image.open(picture) as original:
        picture=original.convert("RGB")
    bg=picture.resize((width,height),Image.Resampling.LANCZOS)
    bg=bg.filter(ImageFilter.GaussianBlur(max(12,width//24)))
    bg=ImageEnhance.Brightness(bg).enhance(.29)
    # Preserve a wide original without aggressive cropping; depth comes from
    # a separate smoothly moving canvas, not turning it into a false photo.
    limitw=width
    limith=int(height*(.64 if height>width else .76))
    ratio=min(limitw/picture.width,limith/picture.height)
    resized=picture.resize((round(picture.width*ratio),round(picture.height*ratio)),Image.Resampling.LANCZOS)
    x=(width-resized.width)//2
    y=max(height//7,(height-resized.height)//2-40) if height>width else (height-resized.height)//2
    bg.paste(resized,(x,y))
    draw=ImageDraw.Draw(bg)
    titlefont=ImageFont.truetype(BOLD,27 if height>width else 24)
    labelfont=ImageFont.truetype(FONT,19 if height>width else 17)
    draw.rounded_rectangle((24,24,min(width-24,686),100),radius=18,fill=(9,17,29))
    draw.text((41,34),heading[:32],font=titlefont,fill=(249,247,244))
    notice=("RECREACIÓN ARTÍSTICA" if source_type=="illustration" else "MATERIAL VISUAL CON PROCEDENCIA")
    draw.text((28,height-85),notice,font=labelfont,fill=(225,231,242))
    bg.save(out,optimize=True)


def zoom_filter(scene,frames,size):
    camera=scene["camera"]
    movement=camera["movement"]
    zoom=float(camera.get("zoom",1.08))
    tx,ty=camera.get("target",[.5,.5])
    # Evaluated per output frame with zoompan's built-in "on" counter.
    # All parameters are clamped by the manifest validator.
    phase=f"min(on/{max(1,frames-1)},1)"
    if movement=="zoom_in":
        z=f"1+({zoom}-1)*{phase}"
    elif movement=="zoom_out":
        z=f"{zoom}-({zoom}-1)*{phase}"
    else:
        z=f"{zoom}"
    if movement=="pan_left":
        x=f"(iw-iw/zoom)*(0.85-0.70*{phase})"
    elif movement=="pan_right":
        x=f"(iw-iw/zoom)*(0.15+0.70*{phase})"
    else:
        x=f"(iw-iw/zoom)*{tx}"
    y=f"(ih-ih/zoom)*{ty}"
    width,height=size
    return (f"zoompan=z='{z}':x='{x}':y='{y}':"
            f"d=1:s={width}x{height}:fps=25,format=yuv420p")


def produce(manifest,out,allow_lab=False):
    project=load_project(manifest,allow_lab=allow_lab)
    work=Path(out);work.mkdir(parents=True,exist_ok=True)
    size=project["profile"]["size"];width,height=size
    raw_manifest=json.loads(Path(manifest).read_text(encoding="utf-8"))
    parts=[];all_cues=[];offset=0.0;shot_info=[]
    for i,(entry,raw) in enumerate(zip(project["scenes"],raw_manifest["scenes"]),1):
        seconds=entry["voice_seconds"]+.25
        frames=math.ceil(seconds*25)
        still=work/f"visual_{i:03}.png"
        subtitle=work/f"subtitle_{i:03}.ass"
        segment=work/f"part_{i:03}.mp4"
        background_still(entry["image_path"],still,width,height,
                         raw.get("heading",project["title"]),raw.get("source_type","illustration"))
        cues=caption_groups(entry["timed_words"])
        write_ass(subtitle,cues,size)
        # Escaping is required because FFmpeg treats ':' and '\\' as filter delimiters.
        safe_path=subtitle.resolve().as_posix().replace("\\","\\\\").replace(":","\\:")
        vf=zoom_filter(entry,frames,size)+f",ass=filename='{safe_path}'"
        ffmpeg("-loop","1","-framerate","25","-i",still,
               "-i",entry["audio_path"],"-vf",vf,
               "-frames:v",str(frames),"-af","apad",
               "-c:v","libx264","-preset","veryfast","-crf","22",
               "-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
               "-ar","48000","-ac","2",
               "-t",f"{seconds:.4f}","-movflags","+faststart",segment,timeout=180)
        parts.append(segment)
        all_cues.extend([{"start":c["start"]+offset,"end":c["end"]+offset,"text":c["text"]} for c in cues])
        shot_info.append({"scene":i,"image_sha256":entry["image_sha256"],
                          "voice_sha256":entry["audio_sha256"],
                          "camera":entry["camera"],"seconds":seconds,
                          "caption_groups":len(cues)})
        offset+=seconds
    listing=work/"concat.txt"
    listing.write_text("".join("file '"+p.name+"'\n" for p in parts),encoding="utf-8")
    final=work/"autostudio-personal-REVIEW.mp4"
    ffmpeg("-f","concat","-safe","0","-i",listing,
           "-c","copy","-movflags","+faststart",final,timeout=180)
    srt=work/"captions.srt"
    srt.write_text("\n".join(
        f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n"
        for i,c in enumerate(all_cues,1)),encoding="utf-8")
    from scripts.personal_quality import inspect_production
    report=inspect_production(final,project,shot_info,srt)
    (work/"quality-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if not report["technical_passed"]:
        raise RuntimeError("Vídeo rechazado por QA: "+str(report["errors"]))
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("manifest",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--lab",action="store_true")
    args=parser.parse_args()
    report=produce(args.manifest,args.out,allow_lab=args.lab)
    print(json.dumps({"video":report["video"],"seconds":report["seconds"],
                      "quality":report["status"],"sha256":report["sha256"]},ensure_ascii=False))


if __name__=="__main__":main()
