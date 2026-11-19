"""Story-wide cinematography planning BEFORE any FLUX image requests.

One bounded Workers AI text request proposes shot types for every scene. Strict
validation catches repeated compositions, hallucination-prone unsupported
details and malformed output before image generation. Editorial/science
approval remains separate. Generic: no per-topic or KELT shot templates.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

SCALES = ("extreme_wide","wide","medium","close","extreme_close")
ANGLES = ("frontal","side","three_quarter","overhead","low","high")
ROLES = ("establish","relationship","detail","process","contrast","consequence","transition")
MODEL = "@cf/meta/llama-3.1-8b-instruct-fp8"
MAX_SCENES = 24
MAX_WORDS = 22
ACTION_FILLER = frozenset("a an the and or of to from in on with without over under above below is are as at by into through seen visible camera view shows showing appears image picture scene shot close distant bright glowing illuminated light dramatic cinematic".split())

def _action_fingerprint(text):
    """Conservative structural overlap: no fixed subject or documentary templates."""
    words=re.findall(r"[a-z]{3,}",text.lower())
    return frozenset(w[:-3]+"y" if w.endswith("ies") and len(w)>5 else w[:-1] if w.endswith("s") and len(w)>5 and not w.endswith("ss") else w for w in words if w not in ACTION_FILLER)


def _scene_list(story):
    scenes=story.get("scenes")
    if not isinstance(scenes,list) or not 1<=len(scenes)<=MAX_SCENES:
        raise ValueError("Expected 1-24 narrated scenes")
    for s in scenes:
        if not isinstance(s,dict) or not isinstance(s.get("narration"),str) or not 12<=len(s["narration"])<=600:
            raise ValueError("Each scene must contain a usable narration")
    return scenes

def validate_plan(plan, story):
    scenes=_scene_list(story)
    if not isinstance(plan,dict) or not isinstance(plan.get("shots"),list) or len(plan["shots"])!=len(scenes):
        raise ValueError("Missing or wrong number of scene shot descriptions")
    known=set()
    prior_actions=[]
    result=[]
    for i,item in enumerate(plan["shots"],1):
        if not isinstance(item,dict) or item.get("scene")!=i:
            raise ValueError("Shot numbering does not match narration order")
        scale,angle,role=(item.get(k) for k in ("scale","angle","role"))
        if scale not in SCALES or angle not in ANGLES or role not in ROLES:
            raise ValueError("Unrecognized cinematographic shot type")
        subject=item.get("subject")
        action=item.get("visible_action")
        if not isinstance(subject,str) or not 4<=len(subject)<=200 or len(subject.split())>MAX_WORDS:
            raise ValueError("Shot subject absent or overly verbose")
        # FLUX cannot turn abstract nouns like "orbital period" into a clear
        # shot. Demand an observable relationship/action before any generation.
        if not isinstance(action,str) or not 16<=len(action)<=200 or not 6<=len(action.split())<=MAX_WORDS:
            raise ValueError("Shot visible_action must describe a concrete observable scene in 6-22 words")
        if re.search(r"\b(?:map|chart|diagram|infographic|graphic|caption|subtitle|label)\b", action, re.I):
            raise ValueError("Abstract visual shorthand is not an image-generation shot")
        if re.search(r"https?://|\b(?:watermark|subtitle|logo)\b",subject+" "+action,re.I):
            raise ValueError("Plan contains forbidden graphic content")
        # A repeated scale+angle+role is the most blatant duplication, and
        # must be fixed before image-generation requests.
        fingerprint=(scale,angle,role)
        if fingerprint in known:
            raise ValueError("Repeated shot grammar; rebuild plan before FLUX")
        # Different metadata cannot disguise two near-identical physical
        # compositions. This is deliberately conservative to allow the same
        # subject in genuinely different shots.
        current=_action_fingerprint(action)
        for previous_scene, previous in prior_actions:
            shared=current & previous
            if len(shared)>=5 and len(shared)/max(1,min(len(current),len(previous)))>=0.80:
                raise ValueError(
                    f"Near-duplicate visible action in scenes {previous_scene} and {i}; "
                    "change actual objects, spatial relationship or visible process")
        prior_actions.append((i,current))
        known.add(fingerprint)
        result.append({"scene":i,"scale":scale,"angle":angle,"role":role,
                       "subject":subject.strip(),"visible_action":action.strip()})
    return result

def parse_reply(content):
    if not isinstance(content,str):
        raise ValueError("Shot planner output is not text")
    clean=content.strip()
    if clean.startswith("```"):
        clean=re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$","",clean,flags=re.I).strip()
    try:
        return json.loads(clean)
    except (ValueError,TypeError) as exc:
        raise ValueError("Shot planner returned invalid JSON") from exc

def check_explicit_story_constraints(story, shots):
    """Reject a few *explicit* script contradictions before consulting an LLM.

    These are narrow general semantic safeguards, not an attempt to infer
    comprehensive scientific truth or KELT-specific scene scripts.
    """
    scenes=_scene_list(story)
    full=" ".join(s["narration"] for s in scenes).lower()
    # Distinguish an explicit no-ground gaseous world from a star whose
    # surface may legitimately be discussed in the same documentary.
    describes_gas_world=bool(re.search(
        r"(?:mundo gaseoso|planeta[^.]{0,100}(?:gas|gaseoso)|gaseous planet|gas giant)",
        full))
    denies_ground=bool(re.search(
        r"(?:no hay (?:un )?suelo|sin superficie s[oó]lida|no solid (?:surface|ground)|without solid ground)",
        full))
    unsupported_materials={
        "dust":("dust","polvo"),
        "galaxy":("galaxy","galaxia"),
    }
    for shot in shots:
        subject=str(shot.get("subject","")).lower()
        action=str(shot.get("visible_action","")).lower()
        if describes_gas_world and denies_ground and "star" not in subject and "estrella" not in subject:
            if re.search(r"\b(?:solid surface|hot surface|rocky ground|terrain|rocky landscape|lava ground)\b",action):
                raise ValueError(
                    f"Scene {shot['scene']} implies solid ground or terrain on a gaseous subject, "
                    "contradicting an explicit no-ground script")
        for term,(english,spanish) in unsupported_materials.items():
            if (re.search(r"\b"+(r"dust(?:y)?" if term=="dust" else re.escape(english))+r"\b",action)
                    and english not in full and spanish not in full):
                raise ValueError(
                    f"Scene {shot['scene']} introduces unsupported {term}, absent from the narration")
    return True


def _critic_response_object(response):
    """Extract only known model text envelopes; never infer approval from metadata."""
    def unwrap(value, depth=0):
        if depth > 6:
            raise ValueError("Narration reviewer response nested too deeply")
        if isinstance(value, str):
            parsed = parse_reply(value)
            if not isinstance(parsed, dict):
                raise ValueError("Narration reviewer must return an object")
            return parsed
        if isinstance(value, dict):
            if "decision" in value or "issues" in value:
                return value
            for key in ("response", "answer", "text", "content", "output", "result"):
                if key in value and value[key] not in (None, "", []):
                    return unwrap(value[key], depth+1)
            choices = value.get("choices")
            if isinstance(choices, list) and choices:
                first = choices[0]
                if isinstance(first, dict):
                    return unwrap(first.get("message", first), depth+1)
        if isinstance(value, list) and len(value) == 1:
            return unwrap(value[0], depth+1)
        raise ValueError("Narration reviewer has no supported reply content")
    result = unwrap(response)
    decision = result.get("decision")
    if isinstance(decision, str):
        decision = decision.strip().upper()
    issues = result.get("issues")
    if decision not in ("PASS", "FAIL") or not isinstance(issues, list):
        raise ValueError("Narration-grounding reviewer returned an invalid verdict")
    return decision, issues

def review_story_consistency(story, shots, request, account, token):
    """Independent TEXT-only cross-scene reviewer; no scientific certification.

    Reject unsupported or contradicted factual scene details BEFORE image
    generation. The same model can still make mistakes, so this does not
    replace editorial and scientific review of the finished documentary.
    """
    scenes=_scene_list(story)
    narrative="\\n".join(str(i)+". "+scene["narration"] for i,scene in enumerate(scenes,1))
    critic=(
        "You are a conservative STORY-ONLY CONTRADICTION reviewer for a documentary. "
        "Your default verdict is PASS. Flag ONLY an explicit conflict with the narrated "
        "facts or an invented, salient, specific object, material, terrain, location, "
        "physical surface or spatial relationship stated as an established fact. "
        "Read the ENTIRE narration before evaluating individual scenes. "
        "The narration is in Spanish, proposed shots in English: recognize accurate "
        "translations, paraphrases and visual metaphors for abstract concepts. "
        "For example, if narration says an extreme nearby star irradiates a planet, "
        "then showing a star shining onto that planet is SUPPORTED. If narration says "
        "hydrogen molecules dissociate and reform, then visualizing that process is SUPPORTED. "
        "If a narrated world is gaseous without solid ground, visible rocky terrain is "
        "a clear CONTRADICTION. Inventing a named location, distant galaxy, dust, "
        "landscape, building or life absent from the narration is also a material issue. "
        "A side-by-side comparison with Earth MAY be appropriate when comparing durations "
        "but Earth must not appear physically adjacent to the distant planet in the same sky. "
        "Do NOT demand the exact narration words in every shot. "
        "Do NOT reject camera angles, framing, reasonable cinematic lighting, atmospheric "
        "interpretations, or descriptive prose merely because a detail is not literally "
        "quoted in the script. Do NOT flag abstract physical relationships or supported "
        "scientific processes as unsupported. "
        "Ignore minor wording imperfections. If a scene is simply too vague rather than "
        "contradictory, accept it; structural shot validation covers vagueness. "
        "Reject only clearly material contradictions or invented facts. "
        "Do not use outside knowledge to contradict this narration. "
        'Return ONLY JSON object {"decision":"PASS" or "FAIL",'
        '"issues":[{"scene":1,"issue":"unsupported claim"}]}. '
        " For PASS, issues MUST be empty. If FAIL, give concrete corrections for up to "
        "four material problems in issues. No Markdown.\\n"
        "Narration:\\n"+narrative+"\\nProposed shots:\\n"+
        json.dumps(shots,ensure_ascii=False)
    )
    # One schema-only retry on malformed/truncated replies. Reuse the identical
    # narration and shots; never accept invalid output as PASS or call FLUX.
    decision = None
    issues = None
    for attempt in range(2):
        prompt = critic if not attempt else (
            critic + "\\nYour previous response could not be parsed. "
            "Return one COMPLETE JSON object with decision PASS or FAIL and "
            "issues as an array. No markdown, no explanations outside JSON. "
            "Do not change the narration or proposed shots."
        )
        response=request(MODEL,{"messages":[{"role":"user","content":prompt}],
                       "max_tokens":1500,"temperature":0.0},account,token)
        try:
            decision,issues=_critic_response_object(response)
            break
        except ValueError:
            if attempt:
                raise ValueError("Narration-grounding reviewer returned an invalid verdict") from None
    if decision=="PASS":
        if issues:
            raise ValueError("Narration-grounding reviewer returned contradictory PASS with issues")
        return True
    if not issues or len(issues)>len(shots):
        raise ValueError("Narration-grounding reviewer rejected without valid issues")
    detail=[]
    for i in issues:
        if (not isinstance(i,dict) or type(i.get("scene")) is not int
                or not 1<=i["scene"]<=len(shots) or
                not isinstance(i.get("issue"),str) or not 8<=len(i["issue"])<=300):
            raise ValueError("Invalid narration-grounding issue")
        detail.append("scene "+str(i["scene"])+": "+i["issue"][:200])
    raise ValueError("Story-grounding review FAIL: "+"; ".join(detail)[:950])


def build_plan(story,request,account,token):
    scenes=_scene_list(story)
    numbered="\n".join(f"{i}. {s['narration']}" for i,s in enumerate(scenes,1))
    prompt=(
        "Plan coherent but VISUALLY DIFFERENT still images for a scientific documentary. "
        "Think across ALL scenes first, not each in isolation. "
        "Each shot needs a distinctive camera scale, angle, narrative role, subject and visible action. "
        "The visible_action MUST contain 6-22 English words describing EXACTLY what the camera "
        "shows and the spatial relationship between the main subjects. Use tangible visible "
        "objects, plausible physical processes and clear composition. "
        "Avoid vague labels like 'orbital period', 'temperature map', 'gas composition', "
        "'extreme environment', 'breaking apart', and any captions, diagrams or text. "
        "Only depict facts from the corresponding narration/title; do not add invented scientific claims, "
        "materials, environments, colors, life or objects not supported by those facts. "
        "Avoid abstract tunnels, generic vortex patterns, or identical central compositions when they "
        "do not actually represent the narrated subject. Preserve one consistent subject identity. "
        "Select fields from these fixed vocabularies, but write subject/action in English. "
        "scale: "+",".join(SCALES)+". angle: "+",".join(ANGLES)+". role: "+",".join(ROLES)+". "
        "Do NOT reuse the same (scale, angle, role) combination in this video. "
        "Different camera metadata is not enough: the visible_action descriptions must also "
        "show different physical events, subject relationships or framing. "
        "Never merely paraphrase the same central gas swirl or stellar glow in multiple scenes. "
        "If the narration describes an abstract fact, illustrate it using the physical "
        "subjects and relationship actually mentioned instead of adding an unsupported object. "
        "Return ONLY JSON object {\"shots\":[{\"scene\":1,\"scale\":\"wide\","
        "\"angle\":\"side\",\"role\":\"establish\",\"subject\":\"...\","
        "\"visible_action\":\"...\"}, ...]}. Exactly "+str(len(scenes))+
        " shots in order, no prose, no Markdown. Each subject and visible_action <=22 words. "
        "Title: "+str(story.get("title","Documentary"))[:180]+"\nNarration scenes:\n"+numbered
    )
    max_tokens=min(4600,max(900,len(scenes)*190))
    # One bounded repair request is permitted; never regenerate images while
    # fixing an unusable whole-story shot outline.
    from scripts.visual_autopilot import _extract_text
    last_error=None
    last_reply=""
    for attempt in range(2):
        user_prompt=prompt
        if attempt:
            user_prompt += (
                "\\nPREVIOUS PLAN REJECTED: "+str(last_error)[:240]+
                "\\nCorrect the invalid plan below, keeping the exact scene numbers "
                "and the narration-grounded physical subjects. "
                "Return the COMPLETE JSON object, not a patch.\\n"+
                last_reply[:3600])
        response=request(MODEL,{"messages":[{"role":"user","content":user_prompt}],
                                "max_tokens":max_tokens,"temperature":0.15},account,token)
        last_reply=_extract_text(response)
        try:
            shots=validate_plan(parse_reply(last_reply),story)
            check_explicit_story_constraints(story, shots)
            review_story_consistency(story, shots, request, account, token)
            return shots
        except ValueError as exc:
            last_error=exc
    raise ValueError("Shot planner failed preflight twice; no image generation: "+
                     str(last_error))

def shot_context(shot):
    return (f"SHOT PLAN, mandatory: {shot['scale']} camera scale; {shot['angle']} viewpoint; "
            f"narrative role {shot['role']}; subject {shot['subject']}; "
            f"visible event {shot['visible_action']}. "
            "Do not replace this with an abstract or generic spiral.")

def plan_file(story_path,out,request,account,token):
    story=json.loads(Path(story_path).read_text(encoding="utf-8"))
    shots=build_plan(story,request,account,token)
    target=Path(out)
    target.parent.mkdir(parents=True,exist_ok=True)
    artifact={"schema":1,"mode":"real-text-only","title":story.get("title","Documentary"),
              "shots":shots,"new_image_requests":0,"vision_requests":0,
              "scientific_facts_verified":False,"ready_to_publish":False}
    target.write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return artifact

def main():
    import argparse,os
    from scripts.visual_autopilot import _request
    p=argparse.ArgumentParser()
    p.add_argument("--story",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    account=os.environ.get("CLOUDFLARE_ACCOUNT_ID","")
    token=os.environ.get("CLOUDFLARE_API_TOKEN","")
    if not account or not token:
        raise ValueError("Cloudflare secrets missing")
    result=plan_file(a.story,a.out,_request,account,token)
    print(json.dumps({"scenes":len(result["shots"]),"new_images":0,
                      "plan_valid":True,"visual_signatures":[
                          "-".join((s["scale"],s["angle"],s["role"])) for s in result["shots"]]},
                     ensure_ascii=False))

if __name__=="__main__":
    main()
