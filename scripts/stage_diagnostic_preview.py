"""Make a strictly non-publishable diagnostic storyboard from cached images.

This NEVER converts visual FAIL/UNSURE into approval. It uses the same SHA256
validation and path checks as staging, but enables an internal editor preview.
"""
import argparse
import json
from pathlib import Path
from scripts.image_staging import stage_generated_images

def stage_preview(storyboard_path,supervisor_manifest,out_dir):
    source=Path(supervisor_manifest)
    manifest=json.loads(source.read_text(encoding="utf-8"))
    scenes=manifest.get("scenes")
    if manifest.get("schema")!=2 or manifest.get("mode")!="live" or not isinstance(scenes,list):
        raise ValueError("Expected original live supervised image manifest")
    if len(scenes)!=10 or manifest.get("completed_requests")!=10:
        raise ValueError("Expected exactly ten already-generated KELT images")
    staging=[]
    for i,s in enumerate(scenes,1):
        if s.get("scene")!=i or not isinstance(s.get("candidates"),list) or len(s["candidates"])!=1:
            raise ValueError("Unexpected candidate count or scene ordering")
        c=s["candidates"][0]
        verdict=c.get("vision",{}).get("decision")
        if verdict not in ("PASS","FAIL","UNSURE"):
            raise ValueError("Missing vision verdict; cannot document preview provenance")
        if c.get("status") not in ("approved","generated"):
            raise ValueError("Invalid original candidate status")
        staging.append({"scene":i,"candidates":[{**c,"status":"generated"}]})
    out=Path(out_dir)
    bridge=source.parent/"diagnostic-bridge.json"
    bridge.write_text(json.dumps({"schema":1,"provider":"diagnostic-preview",
        "completed_requests":10,"scenes":staging},ensure_ascii=False)+"\n",encoding="utf-8")
    result=stage_generated_images(storyboard_path,bridge,out)
    result["preview_only"]=True
    result["scientific_reviewed"]=False
    result["human_visual_approved"]=False
    result["ready_to_publish"]=False
    result["youtube_enabled"]=False
    result["source_image_qa"]={str(s["scene"]):s["candidates"][0]["vision"]["decision"] for s in scenes}
    (out/"diagnostic-preview-report.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--storyboard",required=True)
    p.add_argument("--manifest",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    print(json.dumps(stage_preview(a.storyboard,a.manifest,a.out),ensure_ascii=False))

if __name__=="__main__":
    main()
