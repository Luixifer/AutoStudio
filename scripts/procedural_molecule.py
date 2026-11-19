"""Controlled neutral-hydrogen bond and separation illustration.

This does not depict electrons, electric arcs, ionization, or actual atom
trajectories. It illustrates H2 <-> H + H qualitatively with smooth motion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter

WIDTH, HEIGHT = 1280, 720
FPS, SECONDS = 24, 5


def smoothstep(t: float) -> float:
    if not 0 <= t <= 1:
        raise ValueError("Normalized time outside 0..1")
    return t * t * (3 - 2*t)


def molecular_centers(t: float, mode: str):
    """Positions represent two neutral atoms; gap varies continuously."""
    if mode not in ("dissociation", "recombination"):
        raise ValueError("Unknown molecular process")
    # Stable hold -> transition -> stable hold.
    phase = min(1., max(0., (t - .23)/.55))
    separation = smoothstep(phase)
    if mode == "recombination":
        separation = 1. - separation
    gap = 92 + 360 * separation
    return ((WIDTH/2-gap/2, HEIGHT/2),
            (WIDTH/2+gap/2, HEIGHT/2))


def _atom(radius=59):
    size=radius*4
    sprite=Image.new("RGBA", (size,size),(0,0,0,0))
    x=y=size//2
    outer=Image.new("RGBA",sprite.size,(0,0,0,0))
    d=ImageDraw.Draw(outer,"RGBA")
    d.ellipse((x-radius*1.42,y-radius*1.42,x+radius*1.42,y+radius*1.42),
              fill=(52,176,240,105))
    sprite.alpha_composite(outer.filter(ImageFilter.GaussianBlur(radius*.45)))
    d=ImageDraw.Draw(sprite,"RGBA")
    for factor,color in (
        (1.08,(40,118,204,110)),
        (1.0,(65,181,229,245)),
        (.86,(117,216,249,255)),
        (.55,(203,245,255,255)),
        (.23,(243,253,255,255))):
        r=radius*factor
        d.ellipse((x-r,y-r,x+r,y+r),fill=color)
    return sprite


def molecular_frame(index: int, total: int, mode: str):
    if total<2 or not 0<=index<total:
        raise ValueError("Invalid frame")
    a,b=molecular_centers(index/total,mode)
    canvas=Image.new("RGBA",(WIDTH,HEIGHT),(4,9,24,255))
    # Dark, restrained nebular backdrop with no false physical objects.
    draw=ImageDraw.Draw(canvas,"RGBA")
    for n in range(8):
        r=130+n*60
        alpha=max(0,20-n*2)
        draw.ellipse((WIDTH/2-r,HEIGHT/2-r*.54,
                      WIDTH/2+r,HEIGHT/2+r*.54),
                     outline=(36,75,120,alpha),width=2)
    dist=math.dist(a,b)
    # Controlled bond cue only while atoms overlap as a molecule;
    # not a literal visible chemical bond or electron motion.
    if dist<190:
        d=ImageDraw.Draw(canvas,"RGBA")
        d.line((a[0],a[1],b[0],b[1]),fill=(95,208,240,105),width=15)
    sprite=_atom()
    for x,y in (a,b):
        canvas.alpha_composite(sprite, (round(x-sprite.width/2),
                                        round(y-sprite.height/2)))
    return canvas.convert("RGB")


def render(out_dir: str|Path, mode: str, *, fps=FPS, seconds=SECONDS):
    if mode not in ("dissociation","recombination"):
        raise ValueError("Invalid molecular mode")
    if (fps,seconds)!=(FPS,SECONDS):
        raise ValueError("Output limited to 5 seconds at 24fps")
    out=Path(out_dir)
    out.mkdir(parents=True,exist_ok=True)
    total=fps*seconds
    target=out/f"hydrogen-{mode}.mp4"
    cmd=[imageio_ffmpeg.get_ffmpeg_exe(), "-y","-hide_banner","-loglevel","error",
         "-f","rawvideo","-pixel_format","rgb24",
         "-video_size",f"{WIDTH}x{HEIGHT}","-framerate",str(fps),
         "-i","pipe:0","-an","-c:v","libx264","-preset","veryfast",
         "-crf","19","-pix_fmt","yuv420p","-movflags","+faststart",
         str(target)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for i in range(total):
            frame=molecular_frame(i,total,mode)
            if i==0:
                frame.save(out/f"hydrogen-{mode}-first.jpg",quality=90)
            if i==total//2:
                frame.save(out/f"hydrogen-{mode}-middle.jpg",quality=90)
            proc.stdin.write(frame.tobytes())
    except Exception:
        proc.kill()
        proc.wait()
        raise
    finally:
        proc.stdin.close()
    if proc.wait():
        raise RuntimeError("Molecular ffmpeg failed")
    manifest={
        "mode":mode,"mp4":target.name,
        "sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
        "frames":total,"fps":fps,"size":[WIDTH,HEIGHT],
        "illustrative_neutral_hydrogen_atoms":2,
        "electron_stripping_depicted":False,
        "ionization_depicted":False,
        "not_a_quantum_simulation":True,
        "human_visual_approved":False,
        "scientific_facts_verified":False,
        "ready_to_publish":False,"youtube_enabled":False}
    (out/f"hydrogen-{mode}-manifest.json").write_text(
        json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return manifest


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    p.add_argument("--mode",choices=["dissociation","recombination"],required=True)
    a=p.parse_args()
    print(json.dumps(render(a.out,a.mode)))


if __name__=="__main__":
    main()
