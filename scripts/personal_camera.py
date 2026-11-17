"""Conservative automatic framing and near-duplicate detection.

Uses image texture/contrast, never claims semantic object understanding.
Respects explicit user focal coordinates and uses no external AI service.
"""
import math
from pathlib import Path


def edge_energy(tile):
    from PIL import ImageFilter,ImageStat
    greys=tile.convert("L")
    edge=ImageStat.Stat(greys.filter(ImageFilter.FIND_EDGES)).mean[0]
    contrast=ImageStat.Stat(greys).stddev[0]
    return edge*.6+contrast*.4


def suggest_focal_point(image_path):
    from PIL import Image,ImageOps
    with Image.open(image_path) as src:
        im=ImageOps.exif_transpose(src).convert("RGB")
        im.thumbnail((360,540))
        im.load()
    w,h=im.size
    if w<40 or h<40:raise ValueError("Imagen demasiado pequeña.")
    # Avoid extreme edges (crop risk) and text-safe top/bottom areas.
    grid=((.25,.24),(.5,.24),(.75,.24),
          (.25,.43),(.5,.43),(.75,.43),
          (.25,.62),(.5,.62),(.75,.62))
    patch=max(24,min(w,h)//3)
    evaluations=[]
    for cx,cy in grid:
        x=int(cx*w);y=int(cy*h)
        left=max(0,x-patch//2);upper=max(0,y-patch//2)
        tile=im.crop((left,upper,min(w,left+patch),min(h,upper+patch)))
        score=edge_energy(tile)
        # A mild center preference avoids violent cropping on near ties.
        score*=1-.1*(abs(cx-.5)+abs(cy-.45))
        evaluations.append((score,cx,cy))
    evaluations.sort(key=lambda item:(item[0],-abs(item[1]-.5)),reverse=True)
    top=evaluations[0]
    median=sorted(e[0] for e in evaluations)[len(evaluations)//2]
    spread=(top[0]-median)/max(top[0],1.)
    confidence="low" if spread<.12 else "medium"
    if confidence=="low":focal=[.5,.45]
    else:focal=[round(top[1],3),round(top[2],3)]
    return {"target":focal,"confidence":confidence,
            "method":"local_texture_heuristic_not_subject_detection",
            "score":round(top[0],2)}


def dhash(image_path):
    from PIL import Image,ImageOps
    with Image.open(image_path) as src:
        im=ImageOps.exif_transpose(src).convert("L").resize((9,8))
    px=list(im.getdata())
    bits=0
    for row in range(8):
        for col in range(8):
            bits=(bits<<1)|(px[row*9+col]>px[row*9+col+1])
    return bits


def visual_similarity_warnings(image_paths):
    # Cryptographic hashes are checked elsewhere. dHash only warns about
    # similar composition; visually matching scenes need editorial review.
    signatures=[dhash(p) for p in image_paths]
    warnings=[]
    for i,a in enumerate(signatures):
        for j in range(i+1,len(signatures)):
            difference=(a^signatures[j]).bit_count()
            if difference<=4:
                warnings.append({
                    "scene_a":i+1,"scene_b":j+1,"hamming_distance":difference,
                    "warning":"Imágenes visualmente muy parecidas; revisar repetición.",
                })
    return warnings
