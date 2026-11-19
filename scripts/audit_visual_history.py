"""Retrospective composition audit of actual visual-supervisor observations.

Read-only: no image generation, model calls, manifest rewrites or approvals.
This is a lower bound for repeated visual motifs, NOT perceptual-image scoring.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from scripts.visual_distinctness import compare_visual_evidence

def audit(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != 2 or not isinstance(data.get("scenes"),list):
        raise ValueError("Expected supervised visual manifest (schema 2)")
    seen=[]
    out={"schema":1,"source":Path(path).name,
         "scenes":len(data["scenes"]),"previously_individual_passed":0,
         "individually_rejected_or_unsure":0,"visual_composition_duplicates":[],
         "scientific_verification":False,"publication_approved":False}
    for i,scene in enumerate(data["scenes"],1):
        if scene.get("scene")!=i:
            raise ValueError("Scene order mismatch")
        candidates=scene.get("candidates",[])
        if not isinstance(candidates,list) or not candidates:
            raise ValueError("No candidate for scene "+str(i))
        observed=candidates[-1].get("vision",{})
        if observed.get("decision") != "PASS":
            out["individually_rejected_or_unsure"]+=1
            continue
        out["previously_individual_passed"]+=1
        evidence=observed.get("evidence","")
        repeated=compare_visual_evidence(evidence,seen)
        if repeated is not None:
            out["visual_composition_duplicates"].append({"scene":i,**repeated})
        else:
            seen.append((i,evidence))
    out["would_require_additional_review"]=bool(
        out["individually_rejected_or_unsure"] or out["visual_composition_duplicates"])
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    result=audit(args.manifest)
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__":
    main()
