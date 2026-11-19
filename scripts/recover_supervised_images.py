"""Reassess only previously ambiguous frames; never generate replacement images.

Input is a complete original GitHub Actions artifact: the scene JPEG files and
visual-supervision-manifest.json from a single run. Every file is checked
against the recorded SHA256 before reuse. Fail closed on missing or bad data.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil

from scripts.image_generation import image_dimensions
from scripts.vision_gemma import evaluate_gemma

def recover(original_manifest, output_dir, *, expected_scenes=10, reviewer=evaluate_gemma,
            account="", token="", allowed_retry_scenes=(1,10)):
    source=Path(original_manifest)
    data=json.loads(source.read_text(encoding="utf-8"))
    scenes=data.get("scenes",[])
    if (data.get("schema")!=2 or data.get("mode")!="live" or
        len(scenes)!=expected_scenes or data.get("completed_requests")!=expected_scenes):
        raise ValueError("Wrong or incomplete source generation manifest")
    if not isinstance(data.get("vision_requests"),int) or data["vision_requests"]<expected_scenes:
        raise ValueError("Source image inspections missing")
    retry=set(allowed_retry_scenes)
    if not retry.issubset(set(range(1,expected_scenes+1))):
        raise ValueError("Invalid retry indices")
    if not account or not token:
        raise ValueError("Cloudflare token and account required")
    out=Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise ValueError("Recovery output must be empty")
    # Validate all images before spending inference quota or writing output.
    images=[]
    for i,scene in enumerate(scenes,1):
        if not isinstance(scene,dict) or scene.get("scene")!=i:
            raise ValueError("Scene ordering mismatch")
        candidates=scene.get("candidates")
        if not isinstance(candidates,list) or len(candidates)!=1:
            raise ValueError("Only one original candidate is expected per scene")
        c=candidates[0]
        name=c.get("file")
        if name not in (f"scene_{i:02d}_v1.jpg",f"scene_{i:02d}_v1.png"):
            raise ValueError("Invalid original image filename")
        path=source.parent/name
        if not path.is_file() or path.is_symlink() or path.stat().st_size>12_000_000:
            raise ValueError("Original image missing or oversized")
        content=path.read_bytes()
        w,h,ext=image_dimensions(content)
        if (not name.endswith(ext) or hashlib.sha256(content).hexdigest()!=c.get("sha256")
              or [w,h]!=c.get("dimensions")):
            raise ValueError("Original image hash or dimensions mismatched")
        if not isinstance(scene.get("narration"),str) or not isinstance(scene.get("image_prompt"),str):
            raise ValueError("Scene metadata incomplete")
        decision=c.get("vision",{}).get("decision")
        if i in retry:
            if scene.get("approved") is not False or decision!="UNSURE":
                raise ValueError("Only unresolved UNSURE scenes may be rechecked")
        elif not (scene.get("approved") is True and decision=="PASS" and c.get("status")=="approved"):
            raise ValueError("An additional scene needs review; refusing to bypass review gate")
        images.append((name,content))
    out.mkdir(parents=True,exist_ok=True)
    updated=copy.deepcopy(data)
    updated["recovery_schema"]=1
    updated["original_image_requests"]=data["completed_requests"]
    updated["reinspection_requests"]=0
    updated["new_image_requests"]=0
    updated["human_visual_approved"]=False
    updated["scientific_facts_verified"]=False
    updated["youtube_enabled"]=False
    updated["all_scenes_approved"]=False
    try:
        # Keep originals unchanged, including the 8 already approved.
        for filename,content in images:
            (out/filename).write_bytes(content)
        for i in sorted(retry):
            scene=updated["scenes"][i-1]
            c=scene["candidates"][0]
            original_verdict=copy.deepcopy(c["vision"])
            try:
                verdict=reviewer(images[i-1][1],scene["narration"],scene["image_prompt"],account,token)
            except Exception as exc:
                # An API failure is an unknown result, not a visual rejection.
                verdict={"decision":"UNSURE","evidence":"Vision provider request failed; review pending.",
                         "error_type":type(exc).__name__}
            updated["reinspection_requests"]+=1
            c["original_vision"]=original_verdict
            c["vision"]=verdict
            approved=verdict.get("decision")=="PASS" and bool(verdict.get("evidence","").strip())
            c["status"]="approved" if approved else "generated"
            scene["approved"]=approved
            scene["status"]="approved" if approved else "needs_human_review"
            print(json.dumps({"scene":i,"decision":verdict.get("decision"),
                 "method":verdict.get("method","unspecified"),"new_images_generated":0},ensure_ascii=False),flush=True)
    finally:
        updated["vision_requests"]=data["vision_requests"]+updated["reinspection_requests"]
        updated["all_scenes_approved"]=all(s.get("approved") is True for s in updated["scenes"])
        (out/"visual-supervision-manifest.json").write_text(
            json.dumps(updated,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        report={"schema":1,"total_scenes":len(scenes),
                "original_image_requests":updated["original_image_requests"],
                "new_image_requests":0,"reinspection_requests":updated["reinspection_requests"],
                "approved_scenes":sum(bool(s.get("approved")) for s in updated["scenes"]),
                "all_scenes_approved":updated["all_scenes_approved"],
                "human_visual_approved":False,"scientific_facts_verified":False,
                "youtube_enabled":False}
        (out/"recovery-report.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return updated

def main():
    import os
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--scenes",type=int,default=10)
    args=p.parse_args()
    result=recover(args.manifest,args.out,expected_scenes=args.scenes,
                   account=os.environ.get("CLOUDFLARE_ACCOUNT_ID",""),
                   token=os.environ.get("CLOUDFLARE_API_TOKEN",""))
    print(json.dumps({"approved":sum(s["approved"] for s in result["scenes"]),
         "total":len(result["scenes"]),"new_images":0,
         "reinspections":result["reinspection_requests"]},ensure_ascii=False))
    if not result["all_scenes_approved"]:
        raise SystemExit("Unresolved images preserved. Video staging remains blocked.")

if __name__=="__main__":
    main()
