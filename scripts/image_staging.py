"""Prepare a complete replacement storyboard from generated images without touching originals.

Requires one verified image per scene; rejects partial jobs and inconsistent manifests.
The resulting storyboard can be consumed by personal_prepare from the pinned engine.
"""
import argparse
import hashlib
import json
from pathlib import Path

from scripts.image_generation import image_dimensions

def stage_generated_images(storyboard_path, manifest_path, output):
    storyboard_path=Path(storyboard_path)
    manifest_path=Path(manifest_path)
    source=json.loads(storyboard_path.read_text(encoding="utf-8"))
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    scenes=source.get("scenes")
    entries=manifest.get("scenes")
    if source.get("schema")!=3 or not isinstance(scenes,list) or not isinstance(entries,list) or len(entries)!=len(scenes):
        raise ValueError("Storyboard and image manifest do not match")
    if manifest.get("provider")=="dry-run" or manifest.get("completed_requests",0)<len(scenes):
        raise ValueError("Generated images are incomplete")
    selected=[]
    for i,(scene,entry) in enumerate(zip(scenes,entries),1):
        if entry.get("scene")!=i:
            raise ValueError("Scene order mismatch")
        candidates=[c for c in entry.get("candidates",[]) if c.get("status")=="generated"]
        # Without verified visual scoring, deterministic first candidate; not called 'best'.
        if not candidates:
            raise ValueError(f"Missing generated image for scene {i}")
        candidate=candidates[0]
        name=candidate.get("file","")
        if not isinstance(name,str) or name not in (f"scene_{i:02d}_v{candidate.get('variant')}.png", f"scene_{i:02d}_v{candidate.get('variant')}.jpg"):
            raise ValueError("Invalid candidate path")
        path=manifest_path.parent/name
        if not path.is_file() or path.is_symlink() or path.stat().st_size>12_000_000:
            raise ValueError("Missing or oversized image")
        data=path.read_bytes()
        width,height,ext=image_dimensions(data)
        dimensions=[width,height]
        if not name.endswith(ext):
            raise ValueError("Image extension and format mismatch")
        digest=hashlib.sha256(data).hexdigest()
        if digest!=candidate.get("sha256") or dimensions!=candidate.get("dimensions"):
            raise ValueError("Generated image integrity mismatch")
        selected.append((data,digest,dimensions,ext))
    if len(set(digest for _,digest,_,_ in selected))!=len(selected):
        raise ValueError("Duplicate generated images")
    out=Path(output)
    if out.exists() and any(out.iterdir()):
        raise ValueError("Output must be empty, to prevent stale art")
    out.mkdir(parents=True,exist_ok=True)
    copy=json.loads(json.dumps(source))
    copy["editorial_approved"]=False
    copy["youtube"]={"enabled":False}
    for i,(scene,(data,digest,dimensions,ext)) in enumerate(zip(copy["scenes"],selected),1):
        name=f"auto-scene-{i:02d}{ext}"
        (out/name).write_bytes(data)
        scene.update({"image":name, "image_sha256":digest,
                      "rights":{"license":"own_creation"},
                      "source_type":"illustration"})
        scene.pop("camera",None) if scene.get("camera")=="invalid" else None
    (out/"storyboard.json").write_text(json.dumps(copy,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    report={"schema":1,"scenes":len(scenes),"chosen_variant":"first valid candidate, NOT visual ranking",
            "scientific_reviewed":False,"human_visual_approved":False,"youtube_enabled":False,
            "images":[{"scene":i,"sha256":d,"size":sz} for i,(_,d,sz,ext) in enumerate(selected,1)]}
    (out/"image-staging-report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--storyboard",required=True)
    p.add_argument("--manifest",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    print(json.dumps(stage_generated_images(a.storyboard,a.manifest,a.out),ensure_ascii=False))

if __name__=="__main__":
    main()
