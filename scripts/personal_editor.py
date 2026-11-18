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

# zoompan rounds crop offsets to source pixels; 4x input allows 0.25px steps.
CAMERA_SUPERSAMPLE=4


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

def write_ass(path,cues,size,heading,duration,source_type="illustration"):
    width,height=size
    font_size=41 if height>width else 34
    margin_v=205 if height>width else 86
    title_size=26 if height>width else 25
    header=f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,{font_size},&H00FFFFFF,&H0000FFFF,&H00100A08,&H9B000000,-1,0,0,0,100,100,0,0,1,3,1,2,50,50,{margin_v},1
Style: Heading,DejaVu Sans,{title_size},&H00F5F5F5,&H0000FFFF,&H00120B07,&H99000000,-1,0,0,0,100,100,0,0,3,1,0,7,30,30,32,1
Style: Disclosure,DejaVu Sans,18,&H00DDDDDD,&H0000FFFF,&H00120B07,&H99000000,0,0,0,0,100,100,0,0,1,2,0,1,27,27,35,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    clean_title=subtitle_text(str(heading)[:48])
    notice="RECREACIÓN ARTÍSTICA" if source_type=="illustration" else "MATERIAL VISUAL IDENTIFICADO"
    events=[
        f"Dialogue: 1,0:00:00.00,{ass_time(duration)},Heading,,0,0,0,,{clean_title}\n",
        f"Dialogue: 1,0:00:00.00,{ass_time(duration)},Disclosure,,0,0,0,,{notice}\n",
    ]
    for cue in cues:
        events.append(f"Dialogue: 2,{ass_time(cue['start'])},{ass_time(cue['end']+.08)},Default,,0,0,0,,{subtitle_text(cue['text'])}\n")
    result=header+"".join(events)
    if result.count("\nDialogue:") != len(cues)+2:
        raise ValueError("Malformed ASS event separators; refusing visual corruption.")
    Path(path).write_text(result,encoding="utf-8")


def background_still(picture,out,width,height,heading,source_type):
    from PIL import Image,ImageFilter,ImageEnhance,ImageOps,ImageDraw
    with Image.open(picture) as original:
        original=original.convert("RGB")
        ratio=original.width/original.height
        output_ratio=width/height
        if abs(ratio-output_ratio)<.16:
            # Preserve the entire 9:16 original as closely as possible: do not
            # bury a cinematic vertical image inside a narrow rectangle.
            bg=ImageOps.fit(original,(width,height),Image.Resampling.LANCZOS,centering=(.5,.5))
        else:
            bg=original.resize((width,height),Image.Resampling.LANCZOS)
            bg=bg.filter(ImageFilter.GaussianBlur(max(12,width//24)))
            bg=ImageEnhance.Brightness(bg).enhance(.32)
            limitw=width
            limith=int(height*(.70 if height>width else .82))
            scale=min(limitw/original.width,limith/original.height)
            fg=original.resize((round(original.width*scale),round(original.height*scale)),Image.Resampling.LANCZOS)
            x=(width-fg.width)//2
            y=(height-fg.height)//2
            bg.paste(fg,(x,y))
    # Faint gradients behind title/subtitles to ensure legibility without
    # painting permanently moving text into the image.
    overlay=Image.new("RGBA",(width,height),(0,0,0,0))
    draw=ImageDraw.Draw(overlay)
    for y in range(height):
        if y<height*.13:
            alpha=round(100*(1-y/(height*.13)))
        elif y>height*.66:
            alpha=round(95*((y-height*.66)/(height*.34)))
        else:
            alpha=0
        if alpha:draw.line((0,y,width,y),fill=(1,5,12,min(alpha,95)))
    bg=Image.alpha_composite(bg.convert("RGBA"),overlay).convert("RGB")
    bg.save(out,quality=94,subsampling=0,optimize=True)


def zoom_filter(scene,frames,size,fps=60):
    camera=scene["camera"]
    movement=camera["movement"]
    zoom=float(camera.get("zoom",1.08))
    tx,ty=camera.get("target",[.5,.5])
    # Smooth velocity at the beginning and end of each camera move.
    # Supersampling avoids discrete 1px jumps in slow panning shots.
    phase=f"(0.5-0.5*cos(PI*min(on/{max(1,frames-1)},1)))"
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
    return (f"format=yuv444p,"
            f"zoompan=z='{z}':x='{x}':y='{y}':"
            f"d=1:s={width}x{height}:fps={fps},format=yuv420p")


def produce(manifest,out,allow_lab=False):
    project=load_project(manifest,allow_lab=allow_lab)
    work=Path(out);work.mkdir(parents=True,exist_ok=True)
    size=project["profile"]["size"];width,height=size
    fps=project["profile"]["fps"]
    raw_manifest=json.loads(Path(manifest).read_text(encoding="utf-8"))
    parts=[];all_cues=[];offset=0.0;shot_info=[]
    for i,(entry,raw) in enumerate(zip(project["scenes"],raw_manifest["scenes"]),1):
        seconds=entry["voice_seconds"]+.25
        frames=math.ceil(seconds*fps)
        still=work/f"visual_{i:03}.jpg"
        subtitle=work/f"subtitle_{i:03}.ass"
        segment=work/f"part_{i:03}.mp4"
        background_still(entry["image_path"],still,width*CAMERA_SUPERSAMPLE,height*CAMERA_SUPERSAMPLE,
                         raw.get("heading",project["title"]),raw.get("source_type","illustration"))
        cues=caption_groups(entry["timed_words"])
        write_ass(subtitle,cues,size,raw.get("heading",project["title"]),seconds,raw.get("source_type","illustration"))
        # Escaping is required because FFmpeg treats ':' and '\\' as filter delimiters.
        safe_path=subtitle.resolve().as_posix().replace("\\","\\\\").replace(":","\\:")
        vf=zoom_filter(entry,frames,size,fps=fps)+f",ass=filename='{safe_path}'"
        ffmpeg("-loop","1","-framerate",str(fps),"-i",still,
               "-i",entry["audio_path"],"-vf",vf,
               "-frames:v",str(frames),"-af","apad",
               "-c:v","libx264","-preset","veryfast","-crf","22",
               "-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
               "-ar","48000","-ac","2",
               "-t",f"{seconds:.4f}","-movflags","+faststart",segment,timeout=300)
        parts.append(segment)
        all_cues.extend([{"start":c["start"]+offset,"end":c["end"]+offset,"text":c["text"]} for c in cues])
        shot_info.append({"scene":i,"heading":raw.get("heading",project["title"]),"image_sha256":entry["image_sha256"],
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
    from scripts.personal_visual_audit import inspect_visuals
    visual=inspect_visuals(final,shot_info,work,format_name=project["format"])
    report["visual_audit"]=visual
    report["warnings"].extend(visual["warnings"])
    if visual["technical_errors"]:
        report["errors"].extend(visual["technical_errors"])
        report["technical_passed"]=False
        report["status"]="rejected"
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
