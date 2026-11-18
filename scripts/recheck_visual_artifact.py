"""Recheck a generated image without spending any more FLUX image inference."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from scripts.visual_autopilot import evaluate_image
from scripts.image_generation import image_dimensions

def replay(manifest_path,out):
    p=Path(manifest_path)
    report=json.loads(p.read_text(encoding="utf-8"))
    if report.get("schema")!=2 or report.get("mode")!="live" or len(report.get("scenes",[]))!=1:
        raise ValueError("Expected an actual single-scene supervised manifest")
    scene=report["scenes"][0]
    candidates=scene.get("candidates",[])
    if len(candidates)!=1:
        raise ValueError("Expected exactly one original image")
    candidate=candidates[0]
    name=candidate.get("file")
    if name not in ("scene_01_v1.jpg","scene_01_v1.png"):
        raise ValueError("Unexpected image filename")
    image_path=p.parent/name
    if image_path.is_symlink() or not image_path.is_file() or image_path.stat().st_size>12_000_000:
        raise ValueError("Missing original image")
    image=image_path.read_bytes()
    width,height,ext=image_dimensions(image)
    if hashlib.sha256(image).hexdigest()!=candidate.get("sha256") or [width,height]!=candidate.get("dimensions"):
        raise ValueError("Original image verification failed")
    if not name.endswith(ext):
        raise ValueError("Image extension mismatch")
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","")
    token=os.getenv("CLOUDFLARE_API_TOKEN","")
    if not account or not token:
        raise ValueError("Cloudflare secrets required")
    verdict=evaluate_image(image,scene["narration"],scene["image_prompt"],account,token)
    result={"schema":1,"source_sha256":candidate["sha256"],"reused_original_image":True,
       "new_images_generated":0,"verdict":verdict,
       "scientific_fact_check":False,"human_approved":False,"youtube_enabled":False}
    target=Path(out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"decision":verdict.get("decision"),"evidence":verdict.get("evidence"),
        "method":verdict.get("method","undetermined"),"new_images_generated":0,
        "response_keys":verdict.get("response_keys",[]),
        "caption_response_keys":verdict.get("caption_response_keys",[])},ensure_ascii=False),flush=True)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    replay(a.manifest,a.out)

if __name__=="__main__":
    main()
