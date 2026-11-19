"""AutoStudio experimental visual autopilot: script -> AI art brief -> image -> vision QC.

All AI calls are opt-in. Fail closed: an image is not approved unless vision
explicitly returns PASS with visible evidence. This is NOT scientific fact-checking.
Do not use the generated art as factual evidence.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import difflib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

from scripts.image_generation import MAX_BYTES, MAX_PROMPT, generate_cloudflare, image_dimensions

DIRECTOR_MODEL = "@cf/meta/llama-3.1-8b-instruct-fp8"
VISION_MODEL = "@cf/moondream/moondream3.1-9B-A2B"
ROOT_API = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/"
MAX_RETRIES = 1
MAX_SCENES = 24

def _request(model, payload, account, token, timeout=95):
    if not re.fullmatch(r"[0-9a-fA-F]{32}", account or "") or not token:
        raise ValueError("Missing Cloudflare credentials")
    req=urllib.request.Request(
        ROOT_API.format(account=account) + model,
        data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),
        method="POST",headers={"Authorization":"Bearer "+token,
                                "Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as resp:
            data=resp.read(1_000_001)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("Workers AI request rejected: HTTP "+str(exc.code)) from None
    if len(data)>1_000_000:
        raise ValueError("Workers AI response too large")
    reply=json.loads(data)
    if not isinstance(reply,dict) or not reply.get("success"):
        raise RuntimeError("Workers AI unsuccessful response")
    return reply.get("result")

def _extract_text(result):
    """Extract a text reply from known Cloudflare and nested model envelopes.

    Do not coerce arbitrary objects to text: that could accidentally approve
    an image on an unrelated metadata field.
    """
    if isinstance(result, str):
        return result.strip()
    if not isinstance(result, dict):
        return ""
    for key in ("answer", "response", "caption", "text", "content", "output"):
        item = result.get(key)
        if isinstance(item, str) and item.strip():
            return item.strip()
        if isinstance(item, dict):
            nested = _extract_text(item)
            if nested:
                return nested
    choices = result.get("choices")
    if isinstance(choices, list) and choices:
        msg = choices[0].get("message") if isinstance(choices[0], dict) else None
        if isinstance(msg, dict):
            nested = _extract_text(msg)
            if nested:
                return nested
    # Some SDK and compatibility layers add another result envelope.
    if isinstance(result.get("result"), dict):
        return _extract_text(result["result"])
    return ""

def plan_scene(narration, title, previous_style, account, token):
    """The model makes scene-specific instructions; no hardcoded subject templates."""
    if not isinstance(narration,str) or not 12<=len(narration)<=600:
        raise ValueError("Narration required for automatic art direction")
    user=(
        "You direct scientific documentary visuals. Generate ONE single-frame "
        "image-generation prompt in English, at most 1000 characters. "
        "Use ONLY the factual information in the supplied narration and title. "
        "If a scientific property is not supported, avoid depicting it. "
        "Never invent land, structures, organisms, exact colors, dimensions, or materials. "
        "If the subject is a gas planet, depict gas only, not rocky land. "
        "Show the actual subject, clear shot composition, lighting and visual hierarchy. "
        "Photorealistic premium cinematic scientific reconstruction, no text/labels/watermark. "
        "Keep the same main subject's identity, but vary camera scale, viewpoint and visual storytelling. "
        "Never repeat the framing or composition of the previous scene. "
        "Do not turn planets or stars into generic spiral tunnels or black-hole accretion disks. "
        "When the narration describes an orbit or scale, show the spatial relation, not abstract swirling gas. "
        "Return ONLY the image prompt as plain text, no explanation.\n"
        + "Video title: "+title[:180]+"\nNarration: "+narration+"\n"
        + "Previous composition that MUST NOT be repeated: "+previous_style[:350]
    )
    response=_request(DIRECTOR_MODEL,{"messages":[{"role":"user","content":user}],
        "max_tokens":320,"temperature":0.2},account,token)
    prompt=_extract_text(response)
    if not 40<=len(prompt)<=1800 or "http://" in prompt or "https://" in prompt:
        raise ValueError("Automatic visual director produced invalid or incomplete prompt")
    return prompt[:MAX_PROMPT]

def evaluate_image(image_bytes, narration, prompt, account, token):
    """Ask a vision model about visible evidence, not merely a textual plan.

    Strict output grammar makes ambiguous responses UNSURE rather than silently
    approving. Vision models can still make mistakes; human editorial review remains.
    """
    _,_,ext=image_dimensions(image_bytes)
    mime="image/png" if ext==".png" else "image/jpeg"
    data_uri="data:"+mime+";base64,"+base64.b64encode(image_bytes).decode("ascii")
    question=(
        "Act as a cautious image quality inspector. Describe ONLY what is VISIBLE "
        "in the attached image. Compare it with this intended scientific documentary "
        "shot. Reject if a clearly depicted object or setting contradicts the narration "
        "or scene description, if the main subject is missing, if the image is a sketch, "
        "or if it contains text/watermarks. Do not assume objects absent from the image "
        "are present. If you cannot tell, say UNSURE. "
        "Reply on exactly TWO lines:\n"
        "DECISION: PASS or FAIL or UNSURE\n"
        "EVIDENCE: brief visible evidence; if FAIL, say what must change.\n"
        "Narration: "+narration[:550]+"\nPlanned visual: "+prompt[:850]
    )
    result=_request(VISION_MODEL,{"task":"query","image":data_uri,"question":question,
        "reasoning":False,"max_tokens":220,"temperature":0.1},account,token)
    answer=_extract_text(result)
    # On parse failure expose only model response shape (not image bytes or tokens).
    response_keys = sorted(str(k)[:60] for k in result.keys()) if isinstance(result, dict) else []
    match=re.search(r"(?im)^DECISION:\s*(PASS|FAIL|UNSURE)\s*$",answer)
    evidence=re.search(r"(?im)^EVIDENCE:\s*(.{8,500})$",answer)
    if not match or not evidence:
        # Moondream query occasionally returns an empty answer. Use its simpler
        # caption task and ask a text model to compare the OBSERVED caption with
        # the scene. Never approve a blank caption or malformed classifier.
        caption_result=_request(VISION_MODEL,{"task":"caption","image":data_uri,
            "caption_length":"long","max_tokens":320},account,token)
        caption=_extract_text(caption_result)
        if not caption:
            # Moondream returned no content twice in the first real AutoStudio
            # experiment. A different multimodal model now inspects the original
            # image, with no additional FLUX generation.
            from scripts.vision_gemma import evaluate_gemma
            alternative = evaluate_gemma(image_bytes, narration, prompt, account, token)
            alternative["moondream_query_empty"] = not bool(answer)
            alternative["moondream_caption_empty"] = True
            return alternative
        judge_input=(
            "Inspect ONLY this caption produced by an image-viewing model. "
            "A caption can omit objects, so do not assume unmentioned objects are absent. "
            "Reject only clear visual contradictions. If ambiguous, reply UNSURE. "
            "Reply in EXACTLY two lines: DECISION: PASS or FAIL or UNSURE; "
            "EVIDENCE: one factual reason. Do not infer scientific truth merely from a caption.\n"
            "Expected narration: "+narration[:500]+"\\nExpected composition: "+prompt[:750]+
            "\\nWhat is actually visible (caption): "+caption[:950])
        judgement=_extract_text(_request(DIRECTOR_MODEL,{"messages":[
            {"role":"user","content":judge_input}],"max_tokens":180,"temperature":0.0},
            account,token))
        jmatch=re.search(r"(?im)^DECISION:\s*(PASS|FAIL|UNSURE)\s*$",judgement)
        jreason=re.search(r"(?im)^EVIDENCE:\s*(.{8,500})$",judgement)
        if not jmatch or not jreason:
            return {"decision":"UNSURE","evidence":"Caption obtained but judge response unclear.",
                    "caption_excerpt":caption[:400],"judge_excerpt":judgement[:260]}
        return {"decision":jmatch.group(1).upper(),"evidence":jreason.group(1).strip(),
                "method":"caption_plus_text_comparison","caption_excerpt":caption[:400]}
    return {"decision":match.group(1).upper(),"evidence":evidence.group(1).strip(),
            "method":"direct_vision_query"}

def _scenes(story):
    scenes=story.get("scenes")
    if not isinstance(scenes,list) or not 1<=len(scenes)<=MAX_SCENES:
        raise ValueError("Storyboard must contain 1-24 scenes")
    title=story.get("title","Scientific documentary")
    if not isinstance(title,str):
        raise ValueError("Invalid title")
    for item in scenes:
        if not isinstance(item,dict) or not isinstance(item.get("narration"),str):
            raise ValueError("Each scene must contain narration")
    return scenes,title

def run(story_path, out_path, live=False, max_attempts=1, request_budget=10,
        director=plan_scene, generator=generate_cloudflare, vision=None, shot_planner=None):
    """Run a bounded visual loop; always write manifest, even after partial failure."""
    if not 1<=max_attempts<=MAX_RETRIES+1 or not 1<=request_budget<=48:
        raise ValueError("Invalid generation budget")
    story=json.loads(Path(story_path).read_text(encoding="utf-8"))
    scenes,title=_scenes(story)
    if len(scenes)*max_attempts>request_budget:
        raise ValueError("Budget too low for worst-case attempts; no requests made")
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","") if live else ""
    token=os.getenv("CLOUDFLARE_API_TOKEN","") if live else ""
    if live and (not account or not token):
        raise ValueError("Missing Cloudflare secrets")
    if vision is None:
        # Prefer the actual vision model proven on a real FLUX image. This avoids
        # two nonproductive Moondream calls per scene on the Free allocation.
        from scripts.vision_gemma import evaluate_gemma
        vision=evaluate_gemma
        vision_model="@cf/google/gemma-4-26b-a4b-it"
    else:
        vision_model="injected_vision_evaluator"
    from scripts.shot_preflight import build_plan, shot_context
    if shot_planner is None and director is plan_scene:
        shot_planner=build_plan
    out=Path(out_path)
    out.mkdir(parents=True,exist_ok=True)
    report={"schema":2,"mode":"live" if live else "dry-run",
            "director_model":DIRECTOR_MODEL,"vision_model":vision_model,
            "generator_model":"@cf/black-forest-labs/flux-1-schnell",
            "planned_max_image_requests":len(scenes)*max_attempts,
            "completed_requests":0,"vision_requests":0,
            "human_visual_approved":False,"scientific_facts_verified":False,
            "youtube_enabled":False,"all_scenes_approved":False,"scenes":[]}
    identity=""
    prior_visual=[]
    plan=None
    try:
        # Plan the ENTIRE storyboard before spending any image-generation quota.
        # An invalid or repeated composition aborts before FLUX is called.
        if live and shot_planner is not None:
            plan=shot_planner(story,_request,account,token)
            report["preflight_shot_plan"]=plan
            report["preflight_validated"]=True
        else:
            report["preflight_validated"]=False
        for idx,scene in enumerate(scenes,1):
            narration=scene["narration"]
            entry={"scene":idx,"narration":narration,"candidates":[],"approved":False}
            report["scenes"].append(entry)
            if not live:
                entry["status"]="planned"
                continue
            shot_hint=shot_context(plan[idx-1]) if plan is not None else ""
            context=(shot_hint+" Previous composition: "+identity) if shot_hint else identity
            prompt=director(narration,title,context,account,token)
            if identity and difflib.SequenceMatcher(None, prompt.lower(), identity.lower()).ratio()>0.70:
                # Re-plan composition once without spending any image-generation quota.
                # Never bypass this with a deterministic manual per-topic shot list.
                alternate=director(narration,title,
                    shot_hint+" Avoid repeating the previous shot; keep the exact shot scale, angle "
                    "and narrative role specified. Change framing while remaining scientifically grounded. "
                    +identity[:250],account,token)
                if difflib.SequenceMatcher(None, alternate.lower(), identity.lower()).ratio()<difflib.SequenceMatcher(None,prompt.lower(),identity.lower()).ratio():
                    prompt=alternate
                    entry["replanned_for_visual_variety"]=True
            entry["image_prompt"]=prompt
            if plan is not None:
                entry["preflight_shot"]=plan[idx-1]
            identity=prompt[:350]
            for attempt in range(1,max_attempts+1):
                refined=prompt
                if attempt>1:
                    last=entry["candidates"][-1]["vision"]
                    refined=(prompt[:1350]+" Correction after seeing previous image: "
                             +last["evidence"][:350]
                             +". Do not repeat the previous visual mistake.")[:MAX_PROMPT]
                image=generator(refined,account,token)
                width,height,ext=image_dimensions(image)
                path=out/f"scene_{idx:02d}_v{attempt}{ext}"
                path.write_bytes(image)
                report["completed_requests"]+=1
                candidate={"variant":attempt,"status":"generated","file":path.name,
                           "sha256":hashlib.sha256(image).hexdigest(),
                           "dimensions":[width,height],"format":ext[1:]}
                entry["candidates"].append(candidate)
                assessment=vision(image,narration,refined,account,token)
                report["vision_requests"]+=1
                if assessment.get("decision")=="PASS":
                    from scripts.visual_distinctness import compare_visual_evidence
                    evidence=assessment.get("evidence","")
                    if not isinstance(evidence,str) or len(evidence.strip())<12:
                        assessment={"decision":"UNSURE",
                                    "evidence":"Vision model PASS without sufficient observed evidence.",
                                    "original_vision":assessment}
                    else:
                        repeated=compare_visual_evidence(evidence,prior_visual)
                        if repeated:
                            assessment={"decision":"FAIL",
                                "evidence":"Composition appears repeated from scene "
                                +str(repeated["prior_scene"])+". Change camera scale, viewpoint, "
                                "composition and spatial arrangement.",
                                "method":"cross_scene_visual_distinctness",
                                "visual_similarity":repeated,
                                "original_vision":assessment}
                candidate["vision"]=assessment
                # Reveal model verdict without printing account tokens or base64 images.
                print(json.dumps({"scene":idx,"variant":attempt,
                    "vision_decision":assessment.get("decision","UNSURE"),
                    "vision_evidence":assessment.get("evidence","")[:300],
                    "vision_excerpt":assessment.get("raw_excerpt","")[:240],
                    "vision_response_keys":assessment.get("response_keys",[]),
                    "vision_method":assessment.get("method","undetermined")},ensure_ascii=False),flush=True)
                if assessment.get("decision")=="PASS":
                    candidate["status"]="approved"
                    entry["approved"]=True
                    prior_visual.append((idx,assessment["evidence"]))
                    break
            entry["status"]="approved" if entry["approved"] else "needs_human_review"
    finally:
        report["all_scenes_approved"]=bool(report["scenes"]) and len(report["scenes"])==len(scenes) and all(s["approved"] for s in report["scenes"])
        (out/"visual-supervision-manifest.json").write_text(
            json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser(description="Autonomous image prompting and image vision QC; dry-run by default")
    p.add_argument("--story",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--live",action="store_true")
    p.add_argument("--max-attempts",type=int,default=1)
    p.add_argument("--request-budget",type=int,default=10)
    a=p.parse_args()
    result=run(a.story,a.out,live=a.live,max_attempts=a.max_attempts,request_budget=a.request_budget)
    print(json.dumps({"scenes":len(result["scenes"]),"images":result["completed_requests"],
                      "vision_requests":result["vision_requests"],"all_approved":result["all_scenes_approved"],
                      "live":a.live}))
    if a.live and not result["all_scenes_approved"]:
        rejected=[{"scene":s["scene"],"decision":s["candidates"][-1].get("vision",{}).get("decision","UNSURE"),
                   "evidence":s["candidates"][-1].get("vision",{}).get("evidence","")[:300]}
                  for s in result["scenes"] if not s["approved"] and s["candidates"]]
        print("VISUAL_REVIEW_REQUIRED "+json.dumps(rejected,ensure_ascii=False),flush=True)
        raise SystemExit("Some images need human review; no unapproved MP4 produced.")

if __name__=="__main__":
    main()
