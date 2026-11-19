"""Bridge the supervised image manifest into the original schema-3 video workflow."""
import argparse
import json
from pathlib import Path
from scripts.image_staging import stage_generated_images
from scripts.image_duplicate_qa import audit as audit_visual_duplicates

def stage_supervised(storyboard_path, supervised_manifest_path, out_dir):
    manifest_path=Path(supervised_manifest_path)
    original=json.loads(manifest_path.read_text(encoding="utf-8"))
    if (original.get("schema")!=2 or original.get("mode")!="live"
            or original.get("all_scenes_approved") is not True):
        raise ValueError("Visual supervisor did not approve all scenes")
    if not all(s.get("approved") is True for s in original.get("scenes",[])):
        raise ValueError("Scene approval mismatch")
    # Adapter uses only explicitly approved variants; never silently chooses a failed frame.
    candidates=[]
    approved_paths=[]
    for scene in original["scenes"]:
        ok=[c for c in scene.get("candidates",[]) if c.get("status")=="approved"
            and c.get("vision",{}).get("decision")=="PASS"]
        if len(ok)!=1:
            raise ValueError("Exactly one supervised image must be approved per scene")
        candidates.append({"scene":scene["scene"],"candidates":[{**ok[0],"status":"generated"}]})
        approved_paths.append(manifest_path.parent/ok[0]["file"])
    # Additional independent pixel-level gate runs before any staging writes.
    # Image-staging still performs full SHA-256 and dimension verification.
    perceptual = audit_visual_duplicates(approved_paths) if len(approved_paths)>=2 else None
    if perceptual and any(pair["verdict"] in ("DUPLICATE", "POSSIBLE_DUPLICATE", "UNSURE")
                          for pair in perceptual["pairs"]):
        raise ValueError("Perceptual image QA requires review; approved staging blocked")
    legacy={"schema":1,"provider":"supervised-cloudflare",
            "completed_requests":len(candidates),"scenes":candidates}
    bridge=manifest_path.parent/"approved-images-for-staging.json"
    bridge.write_text(json.dumps(legacy,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    report=stage_generated_images(storyboard_path,bridge,out_dir)
    report["supervision"]="Gemma 4 image-aware AI review; not scientific fact-checking"
    report["perceptual_image_qa"] = {"method":"perceptual-dhash-9x8",
        "pairs_checked":len(perceptual["pairs"]) if perceptual else 0,
        "possible_duplicate_pairs":0,
        "result":"no_near_duplicates_detected_not_editorial_approval"}
    report["human_visual_approved"]=False
    Path(out_dir,"image-staging-report.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--storyboard",required=True)
    p.add_argument("--manifest",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    print(json.dumps(stage_supervised(args.storyboard,args.manifest,args.out)))

if __name__=="__main__":
    main()
