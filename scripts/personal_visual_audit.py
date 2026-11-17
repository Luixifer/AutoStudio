"""Visual inspection of real decoded video, not renderer metadata.

Every check is heuristic: passes do NOT establish photorealism or factual
accuracy. Contact sheet is required for human/editorial review.
"""
import io
import json
import math
import statistics
import subprocess
from pathlib import Path


def frame_at(video, seconds, size=(240, 426)):
    from PIL import Image
    width, height=size
    cmd=[
        "ffmpeg","-hide_banner","-loglevel","error",
        "-ss",f"{seconds:.3f}","-i",str(video),
        "-frames:v","1","-vf",f"scale={width}:{height}:flags=lanczos",
        "-f","image2pipe","-vcodec","png","pipe:1"
    ]
    data=subprocess.check_output(cmd,timeout=40)
    with Image.open(io.BytesIO(data)) as picture:
        result=picture.convert("RGB")
        result.load()
    if result.size!=size:
        raise ValueError("Frame size mismatch.")
    return result


def palette_features(image):
    from PIL import ImageStat,ImageFilter
    frame=image.resize((80,80))
    stat=ImageStat.Stat(frame)
    rgb=stat.mean
    lum=frame.convert("L")
    lstat=ImageStat.Stat(lum)
    # Texture proxy avoids rejecting intentionally dark astronomical frames.
    edges=ImageStat.Stat(lum.filter(ImageFilter.FIND_EDGES)).mean[0]
    histogram=lum.histogram()
    dark=sum(histogram[:14])/sum(histogram)
    return {"mean_rgb":[round(c,2) for c in rgb],
            "luminance":round(lstat.mean[0],2),
            "std_luminance":round(lstat.stddev[0],2),
            "edge_mean":round(edges,2),
            "very_dark_fraction":round(dark,4)}


def image_distance(a,b):
    from PIL import ImageChops,ImageStat
    a=a.resize((96,96));b=b.resize((96,96))
    delta=ImageStat.Stat(ImageChops.difference(a,b)).mean
    return round(sum(delta)/3,3)


def build_sheet(images,titles,out,format_name):
    from PIL import Image,ImageDraw,ImageFont
    if not images:raise ValueError("No frames for contact sheet.")
    columns=4 if format_name=="short" else 3
    sample=images[0]
    width,height=sample.size
    gap=14;titlebar=62
    rows=math.ceil(len(images)/columns)
    canvas=Image.new("RGB",(columns*(width+gap)+gap,rows*(height+titlebar+gap)+gap),(14,19,28))
    draw=ImageDraw.Draw(canvas)
    try:font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",19)
    except OSError:font=ImageFont.load_default()
    for index,(image,title) in enumerate(zip(images,titles)):
        x=gap+(index%columns)*(width+gap);y=gap+(index//columns)*(height+titlebar+gap)
        canvas.paste(image,(x,y+titlebar))
        draw.text((x+3,y+3),f"PLANO {index+1:02}",fill=(239,241,250),font=font)
        draw.text((x+3,y+31),str(title)[:24],fill=(183,193,217),font=font)
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(out,optimize=True)


def inspect_visuals(video,shots,destination,format_name="short"):
    """Return audit with exact sampled timestamps, contact sheet and warnings."""
    if format_name not in ("short","documentary","lab"):
        raise ValueError("Unsupported video format.")
    if not isinstance(shots,list) or not shots:
        raise ValueError("Shot timeline missing.")
    video=Path(video);destination=Path(destination)
    width,height=((240,426) if format_name!="documentary" else (384,216))
    images=[];raw_metrics=[];errors=[];warnings=[]
    offset=0.0;timestamps=[]
    for idx,shot in enumerate(shots,1):
        duration=float(shot.get("seconds",0))
        if not math.isfinite(duration) or duration<=0:
            raise ValueError("Invalid shot duration.")
        midpoint=offset+duration*.5
        beginning=offset+min(.35,duration*.2)
        ending=offset+duration-max(.2,duration*.2)
        if ending<=beginning:ending=midpoint
        center=frame_at(video,midpoint,(width,height))
        first=frame_at(video,beginning,(width,height))
        last=frame_at(video,ending,(width,height))
        images.append(center);timestamps.append(round(midpoint,3))
        features=palette_features(center)
        motion=image_distance(first,last)
        if features["very_dark_fraction"]>.96 and features["std_luminance"]<10:
            errors.append(f"Plano {idx}: fotograma casi totalmente negro.")
        if features["std_luminance"]<4 and features["edge_mean"]<4:
            errors.append(f"Plano {idx}: plano visualmente uniforme.")
        if motion<.6 and shot.get("camera",{}).get("movement") not in ("static",None):
            warnings.append(f"Plano {idx}: movimiento anunciado casi imperceptible.")
        raw_metrics.append({"scene":idx,"at_seconds":round(midpoint,3),
                            **features,"movement_pixel_delta":motion})
        offset+=duration
    adjacent=[]
    for a,b in zip(images,images[1:]):
        adjacent.append(image_distance(a,b))
    for index,distance in enumerate(adjacent,1):
        if distance<2.5:
            warnings.append(f"Planos {index} y {index+1}: imágenes visualmente demasiado parecidas.")
    contact=destination/"contacto-planos.jpg"
    build_sheet(images,[s.get("heading",f"Escena {i+1}") for i,s in enumerate(shots)],
                contact,"short" if format_name=="lab" else format_name)
    report={
        "status":"visual_decode_pass" if not errors else "visual_decode_rejected",
        "technical_errors":errors,"warnings":warnings,
        "shots_checked":len(images),
        "sample_timestamps":timestamps,
        "per_shot":raw_metrics,
        "adjacent_scene_distances":adjacent,
        "contact_sheet":str(contact),
        "visual_human_reviewed":False,
        "photorealism_or_accuracy_verified":False,
        "disclaimer":"Heuristics check frames/contrast only, not cinematic quality, scientific facts or typography.",
    }
    (destination/"visual-audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report
