"""Original procedural orbital illustration for AutoStudio.

Educational *not-to-scale* visualization: a luminous host star and a gaseous
planet on a smooth projected orbit. No scene claims it is observational footage.
Frame generation has no external model calls or paid APIs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError as exc:
    raise RuntimeError("Install Pillow to render orbital scenes") from exc

DEFAULT_WIDTH, DEFAULT_HEIGHT = 1280, 720
DEFAULT_FPS, DEFAULT_SECONDS = 24, 5
SEED = 93517


def orbital_position(t: float, center: tuple[float, float],
                     rx: float, ry: float) -> tuple[float, float]:
    """Continuous closed orbit; t is normalized fraction [0,1]."""
    if not 0 <= t <= 1:
        raise ValueError("Normalized time must be between 0 and 1")
    angle = 2 * math.pi * t - .46
    return center[0] + rx * math.cos(angle), center[1] + ry * math.sin(angle)


def _static_background(w: int, h: int):
    import random
    rng = random.Random(SEED)
    base = Image.new("RGB", (w, h), (3, 6, 20))
    draw = ImageDraw.Draw(base, "RGBA")
    for _ in range(round(w*h/3700)):
        x,y=rng.randrange(w),rng.randrange(h)
        radius=rng.choice((1,1,1,2))
        a=rng.randrange(55,180)
        draw.ellipse((x-radius,y-radius,x+radius,y+radius),
                     fill=(190,205,244,a))
    return base


def _star_layer(w: int, h: int, x: float, y: float, radius: float):
    layer=Image.new("RGBA", (w,h), (0,0,0,0))
    glow=Image.new("RGBA", (w,h), (0,0,0,0))
    g=ImageDraw.Draw(glow, "RGBA")
    g.ellipse((x-radius*1.6,y-radius*1.6,x+radius*1.6,y+radius*1.6),
              fill=(255,153,55,90))
    layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(radius*.48)))
    # Three overlapping photosphere disks form a luminous physical star,
    # not a second blue planetary sphere.
    d=ImageDraw.Draw(layer, "RGBA")
    for factor,color in (
        (1.10,(255,123,28,90)), (1.02,(255,186,60,180)),
        (1.0,(255,222,115,255)), (.87,(255,247,183,255)),
        (.62,(255,255,235,255))):
        r=radius*factor
        d.ellipse((x-r,y-r,x+r,y+r),fill=color)
    return layer


def _planet_sprite(radius: int):
    size=radius*2+12
    sprite=Image.new("RGBA",(size,size),(0,0,0,0))
    d=ImageDraw.Draw(sprite,"RGBA")
    cx=cy=size//2
    for py in range(-radius,radius+1):
        extent=math.sqrt(max(0, radius*radius-py*py))
        left=int(cx-extent);right=int(cx+extent)
        # Blue atmospheric banding, not mountains or solid cratered ground.
        band=math.sin(py/radius*18+math.sin(py/radius*4)*2)
        illumination=.66+.20*math.sin(py/radius*math.pi)
        r=int((29+12*band)*illumination)
        g=int((107+28*band)*illumination)
        b=int((179+30*band)*illumination)
        d.line((left,cy+py,right,cy+py),fill=(r,g,b,255),width=1)
    d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),
              outline=(125,207,248,185),width=2)
    return sprite


def frame_at(index: int, total: int, width: int = DEFAULT_WIDTH,
             height: int = DEFAULT_HEIGHT):
    if total < 2 or index < 0 or index >= total:
        raise ValueError("Invalid frame index or total")
    if width < 320 or height < 180:
        raise ValueError("Minimum size 320x180")
    bg=_static_background(width,height).convert("RGBA")
    cx,cy=width*.50,height*.50
    # Projected orbit: a visual aid, not a scale representation.
    pos=orbital_position(index/total,(cx,cy),width*.28,height*.29)
    star=_star_layer(width,height,cx,cy,min(width,height)*.175)
    planet=_planet_sprite(round(min(width,height)*.069))
    px,py=round(pos[0]-planet.width/2),round(pos[1]-planet.height/2)
    # Correct order for an inclined orbit: far-side planet behind star,
    # near-side planet in front. Does not imply a solid planetary surface.
    if math.sin(index/total*2*math.pi-.46) < 0:
        bg.alpha_composite(planet,(px,py))
        bg.alpha_composite(star)
    else:
        bg.alpha_composite(star)
        bg.alpha_composite(planet,(px,py))
    return bg.convert("RGB")


def render(out_dir: str|Path, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
           fps=DEFAULT_FPS, seconds=DEFAULT_SECONDS) -> dict:
    if (width,height)!=(DEFAULT_WIDTH,DEFAULT_HEIGHT):
        raise ValueError("Production preview is fixed at 1280x720")
    if (fps,seconds)!=(DEFAULT_FPS,DEFAULT_SECONDS):
        raise ValueError("Production preview is capped at 5s / 24fps")
    out=Path(out_dir)
    out.mkdir(parents=True,exist_ok=True)
    total=fps*seconds
    proc=subprocess.Popen([
        "ffmpeg","-y","-hide_banner","-loglevel","error",
        "-f","rawvideo","-pixel_format","rgb24",
        "-video_size",f"{width}x{height}","-framerate",str(fps),
        "-i","pipe:0","-an","-c:v","libx264","-preset","veryfast",
        "-crf","19","-pix_fmt","yuv420p","-movflags","+faststart",
        str(out/"orbit-preview.mp4")],stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for i in range(total):
            image=frame_at(i,total,width,height)
            if i==0:
                image.save(out/"orbit-first-frame.jpg",quality=89)
            proc.stdin.write(image.tobytes())
    except Exception:
        proc.kill()
        proc.wait()
        raise
    finally:
        proc.stdin.close()
    code=proc.wait()
    if code:
        raise RuntimeError("ffmpeg did not finish the orbital preview")
    movie=out/"orbit-preview.mp4"
    manifest={
        "scene":"KELT-9b compact orbit","renderer":"procedural-pillow-ffmpeg",
        "frames":total,"fps":fps,"width":width,"height":height,
        "duration_seconds":seconds,"mp4":movie.name,
        "sha256":hashlib.sha256(movie.read_bytes()).hexdigest(),
        "not_to_scale":True,"scientific_illustration_not_observation":True,
        "contains_voice":False,"human_visual_approved":False,
        "scientific_facts_verified":False,"ready_to_publish":False,
        "youtube_enabled":False}
    (out/"orbit-manifest.json").write_text(
        json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return manifest


def main():
    parser=argparse.ArgumentParser(description="Original 5s orbital demonstration")
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    print(json.dumps(render(args.out)))


if __name__=="__main__":
    main()
