"""Story-wide cinematography planning BEFORE any FLUX image requests.

One bounded Workers AI text request proposes shot types for every scene. Strict
validation catches repeated compositions, hallucination-prone unsupported
details and malformed output before image generation. Editorial/science
approval remains separate. Generic: no per-topic or KELT shot templates.
"""
from __future__ import annotations
import json
import re
import hashlib
import hmac
import os
import tempfile
from pathlib import Path

SCALES = ("extreme_wide","wide","medium","close","extreme_close")
ANGLES = ("frontal","side","three_quarter","overhead","low","high")
ROLES = ("establish","relationship","detail","process","contrast","consequence","transition")
MODEL = "@cf/meta/llama-3.1-8b-instruct-fp8"
# Independent reviewer uses a different, stronger free-tier Workers AI model.
# Unlike the planner, it supports schema-constrained JSON at the /ai/run API.
CRITIC_MODEL = "@cf/google/gemma-4-26b-a4b-it"
CRITIC_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": ["PASS", "FAIL"]},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene": {"type": "integer"},
                    "issue": {"type": "string"}
                },
                "required": ["scene", "issue"]
            }
        }
    },
    "required": ["decision", "issues"]
}
SHOT_PATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {"type": "string"},
        "visible_action": {"type": "string"}
    },
    "required": ["subject", "visible_action"],
    "additionalProperties": False
}
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
    prior_subjects=[]
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
            raise ValueError(f"Scene {i}: Shot visible_action must describe a concrete observable scene in 6-22 words")
        visual = subject+" "+action
        # Both the subject and action must be drawable documentary content.
        # The original 10-shot live output mistakenly passed a chart because
        # only visible_action (not subject) was screened.
        if re.search(r"\b(?:map|chart|diagram|infographic|graphic|caption|subtitle|label)\b", visual, re.I):
            raise ValueError(f"Scene {i}: Forbidden diagram or graphic in a visual documentary shot")
        # A talking head or pointing presenter is not a faithful illustration
        # of a narration that only describes physical subjects/processes.
        # This is conditional, not a blanket ban on scientific presenters.
        spoken = scenes[i-1]["narration"]
        if (re.search(r"\b(?:scientists?|presenters?|narrators?|speakers?|lecturers?|people|persons?|humans?|hands?|pointing|gestures?|gesturing|speaking)\b",visual,re.I)
            and not re.search(r"\b(?:scientists?|presenters?|narrators?|speakers?|lecturers?|people|persons?|humans?|hands?|cient[ií]fic[oa]s?|presentador[ae]s?|narrador[ae]s?|personas?|human[oa]s?|manos?|investigador[ae]s?)\b",spoken,re.I)):
            raise ValueError(f"Scene {i}: Unnarrated human presenter or gesture replaces the scientific subject")
        if re.search(r"\b(?:explaining a concept|illustrating a concept|talking about an idea)\b",action,re.I):
            raise ValueError(f"Scene {i}: Abstract explanation is not a concrete documentary image")
        if re.search(r"https?://|\b(?:watermark|subtitle|logo)\b",visual,re.I):
            raise ValueError("Plan contains forbidden graphic content")
        # Three adjacent/nearby scenes with an identical central subject
        # are usually three shots of the same object even with new camera
        # metadata. Require a narrower narrated physical subject instead.
        # Two repeats can be legitimate; apply the rule only on the third.
        normalized_subject=re.sub(r"[^a-z0-9]+"," ",subject.lower()).strip()
        earlier=[n for n,old in prior_subjects
                 if old==normalized_subject and i-n<=4]
        if len(earlier)>=2:
            raise ValueError(
                f"Repeated central subject in scenes {earlier[0]} and {i}; "
                "show a distinct narrated physical subject or process")
        prior_subjects.append((i,normalized_subject))
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

def _fix_only_current_camera_angle_collisions(shots, frozen_count):
    """Vary the angle of an unapproved shot, never its narrated content.

    If a model repeats an exact camera tuple used earlier, find the next
    unused viewpoint with the SAME scale and narrative role. Previously
    accepted scenes remain frozen. If no angle fits, fail closed in the
    subsequent standard validator instead of silently relaxing uniqueness.
    """
    result=[dict(shot) for shot in shots]
    used=set()
    for i,item in enumerate(result):
        triple=(item["scale"],item["angle"],item["role"])
        if triple in used and i >= frozen_count:
            old_angle=item["angle"]
            # Prefer minimally different framing: traverse stable available
            # viewpoints from the original angle, not random metadata.
            alternatives=(ANGLES[(ANGLES.index(old_angle)+offset)%len(ANGLES)]
                          for offset in range(1,len(ANGLES)))
            for angle in alternatives:
                candidate=(item["scale"],angle,item["role"])
                if candidate not in used:
                    item["angle"]=angle
                    triple=candidate
                    break
        used.add(triple)
    return result


def parse_reply(content):
    """Accept one complete JSON object, even with a harmless text wrapper.

    Fail closed on truncation, non-object JSON, or multiple objects.
    Never guess or fill missing model output.
    """
    if not isinstance(content,str):
        raise ValueError("Shot planner output is not text")
    clean=content.strip()
    if not clean or len(clean)>100_000:
        raise ValueError("Shot planner returned invalid JSON")
    fence=chr(96)*3
    if clean.startswith(fence):
        clean=clean[len(fence):].strip()
        if clean.lower().startswith("json"):
            clean=clean[4:].strip()
        if clean.endswith(fence):
            clean=clean[:-len(fence)].strip()
    try:
        value=json.loads(clean)
    except (ValueError,TypeError):
        decoder=json.JSONDecoder()
        candidates=[]
        for index,char in enumerate(clean):
            if char!="{":
                continue
            try:
                candidate,end=decoder.raw_decode(clean,index)
            except ValueError:
                continue
            if not isinstance(candidate,dict):
                continue
            prefix,suffix=clean[:index],clean[end:]
            if ("{" in prefix or "}" in prefix or
                    "{" in suffix or "}" in suffix):
                raise ValueError("Shot planner returned invalid JSON")
            # The outer complete object has been found; nested braces belong
            # to this object, not to independent reply candidates.
            candidates.append(candidate)
            break
        if len(candidates)!=1:
            raise ValueError("Shot planner returned invalid JSON")
        value=candidates[0]
    if not isinstance(value,dict):
        raise ValueError("Shot planner returned invalid JSON")
    return value

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
            # An explicitly groundless gas planet cannot acquire lava,
            # molten rock, a crust or rocky terrain just because the script
            # mentions those objects in a NEGATED sentence.
            if re.search(r"\b(?:lava|molten (?:rock|ground)|rocky (?:surface|crust|terrain)|solid crust)\b",
                         subject+" "+action):
                raise ValueError(
                    f"Scene {shot['scene']} implies lava or rocky terrain on a gaseous subject, "
                    "contradicting an explicit no-ground script")
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
    # Keep this short: the free small language model sporadically truncates
    # a long rubric and returns an unusable verdict. A short, self-contained
    # prompt preserves the same independent factual check and fail-closed gate.
    critic=(
        "You are a STORY-ONLY CONTRADICTION reviewer. Review proposed "
        "documentary shots against ONLY the narration below. "
        "The narration may be Spanish; shots are in English. Recognize faithful "
        "translations and physically plausible depictions of narrated processes "
        "are SUPPORTED. "
        "FAIL for an explicit contradiction or a prominent invented factual "
        "object, material, terrain, named place, organism, or spatial relation. "
        "Also FAIL when the PRIMARY subject or action is unrelated to the "
        "specific narration scene, even if the shot resembles its general topic. "
        "For example, a scientist talking or a diagram is NOT a cinematic image "
        "of a planet unless the narration actually discusses that scientist or diagram. "
        "A generic glowing planet is NOT an illustration of a narrated molecular "
        "reaction or orbital-period comparison. "
        "Examples: a gaseous world described without ground must not gain rocky "
        "terrain; a distant galaxy not in the script must not be invented. "
        "Do not FAIL for camera angles, ordinary lighting, visual metaphors, "
        "or a legitimate star-to-planet relationship described in the script. "
        "Do not use outside science to override the supplied narration. "
        "Return ONLY a compact JSON object with EXACTLY two keys: decision "
        "('PASS' or 'FAIL') and issues (array). For PASS use an empty array. "
        "For FAIL issues contains up to 4 objects with keys scene (integer, "
        "numbered locally) and issue (specific factual contradiction). "
        "Do not explain outside JSON.\\n"
        "Narration:\\n"+narrative+
        "\\nShots:\\n"+json.dumps(shots,ensure_ascii=False,
                                     separators=(',',':'))
    )
    # One schema-only retry on malformed/truncated replies. Reuse the identical
    # narration and shots; never accept invalid output as PASS or call FLUX.
    decision = None
    issues = None
    for attempt in range(2):
        prompt = critic if not attempt else (
            "Your previous response could not be parsed. Previous verdict was malformed. "
            "Answer the same question using only a COMPLETE JSON object: "
            '{"decision":"PASS","issues":[]} or '
            '{"decision":"FAIL","issues":[{"scene":1,"issue":"clear contradiction"}]}. '
            "No prose, no markdown, no missing fields. Do not ignore any "
            "material factual conflict.\\n" + critic
        )
        response=request(CRITIC_MODEL,{
            "messages":[{"role":"user","content":prompt}],
            "max_completion_tokens":450,
            "temperature":0.0,
            "chat_template_kwargs":{"enable_thinking":False},
            "response_format":{"type":"json_schema",
                               "json_schema":CRITIC_SCHEMA}
        },account,token)
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


def _build_plan_whole(story,request,account,token):
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
    # One bounded semantic repair, without another full ten-scene JSON dump.
    # After structural validation, repair an explicit offending scene alone;
    # merge its new fields into the original plan and rerun ALL safeguards.
    from scripts.visual_autopilot import _extract_text
    last_error=None
    last_reply=""
    last_shots=None
    for attempt in range(2):
        repair_scene=None
        if attempt and last_shots is not None and last_error is not None:
            match=re.search(r"\b[Ss]cene (\d+) (?:introduces|implies)\b",str(last_error))
            if match:
                n=int(match.group(1))
                if 1<=n<=len(last_shots):
                    repair_scene=n
        if repair_scene is not None:
            original=last_shots[repair_scene-1]
            user_prompt=(
                "Repair ONE invalid documentary shot. Do not add facts absent "
                "from the supplied narration. Return ONLY a JSON object with "
                "two string keys: subject and visible_action. No scene list, "
                "no markdown, no new named places, materials or terrain. "
                "visible_action must contain 6-22 English words describing "
                "a concrete visible relationship. Other shot fields and all "
                "other scenes remain frozen.\\n"
                "ERROR: "+str(last_error)[:700]+"\\n"
                "SCENE NARRATION: "+scenes[repair_scene-1]["narration"]+"\\n"
                "FULL NARRATIVE CONTEXT: "+numbered+"\\n"
                "ORIGINAL SHOT: "+json.dumps(original,ensure_ascii=False)
            )
            repair_tokens=480
        else:
            user_prompt=prompt
            if attempt:
                user_prompt+=(
                    "\\nPREVIOUS PLAN REJECTED: "+str(last_error)[:950]+
                    "\\nReturn COMPLETE corrected JSON for exactly "+
                    str(len(scenes))+" shots; no invented facts.\\n"+
                    last_reply[:1200]
                )
            repair_tokens=max_tokens
        response=request(MODEL,{"messages":[{"role":"user","content":user_prompt}],
                                "max_tokens":repair_tokens,"temperature":0.15},account,token)
        last_reply=_extract_text(response)
        try:
            parsed=parse_reply(last_reply)
            if repair_scene is not None:
                if (not isinstance(parsed,dict) or
                    set(parsed)!={"subject","visible_action"} or
                    not all(isinstance(parsed[k],str) for k in parsed)):
                    raise ValueError("Single-scene semantic repair returned invalid fields")
                candidate=[dict(item) for item in last_shots]
                candidate[repair_scene-1].update(parsed)
                shots=validate_plan({"shots":candidate},story)
            else:
                shots=validate_plan(parsed,story)
            last_shots=shots
            check_explicit_story_constraints(story, shots)
            review_story_consistency(story, shots, request, account, token)
            return shots
        except ValueError as exc:
            last_error=exc
    raise ValueError("Shot planner failed preflight twice; no image generation: "+
                     str(last_error))


def _retry_timed_out_text_request(request):
    """Retry one transient text timeout; no images or approval bypasses.

    The exact same prompt is retried once. Structural and independent
    semantic checks still run on the returned content, and exhausted
    timeouts abort preproduction before FLUX.
    """
    import urllib.error

    def guarded(model, payload, account, token):
        for attempt in range(2):
            try:
                return request(model, payload, account, token)
            except TimeoutError:
                if attempt:
                    raise
            except urllib.error.URLError as exc:
                if not isinstance(exc.reason, TimeoutError) or attempt:
                    raise
        raise RuntimeError("Unreachable text retry state")

    return guarded


CHECKPOINT_VERSION = 1


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def _story_digest(story):
    return hashlib.sha256(_canonical_json(story)).hexdigest()


def _checkpoint_signature(payload, token):
    # A persisted prefix must be authenticated: otherwise arbitrary edited
    # JSON could masquerade as shots that passed the model consistency review.
    if not isinstance(token, str) or not token:
        raise ValueError("Cannot authenticate a shot checkpoint without credentials")
    return hmac.new(token.encode("utf-8"), _canonical_json(payload),
                    hashlib.sha256).hexdigest()


def _write_checkpoint(path, story, accepted, chunk_size, token):
    """Atomically save only text-reviewed accepted shots, never a partial approval."""
    if not path:
        return
    if not isinstance(chunk_size, int) or chunk_size not in (1, 2):
        raise ValueError("Invalid checkpoint batch size")
    if not accepted or len(accepted) > len(_scene_list(story)):
        raise ValueError("Cannot checkpoint an empty or oversized shot prefix")
    shots = validate_plan({"shots":accepted},
                          {"scenes":_scene_list(story)[:len(accepted)]})
    check_explicit_story_constraints(story, shots)
    payload = {"version": CHECKPOINT_VERSION,
               "story_sha256": _story_digest(story),
               "batch_size": chunk_size,
               "accepted_shots": shots,
               "ready_to_publish": False,
               "scientific_facts_verified": False}
    signed = {**payload, "signature": _checkpoint_signature(payload, token)}
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent,
            prefix=".autostudio-checkpoint-", suffix=".tmp", delete=False
        ) as tmp:
            temp_name = tmp.name
            json.dump(signed, tmp, ensure_ascii=False, indent=2)
            tmp.write("\n")
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(temp_name, target)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def _read_checkpoint(path, story, token):
    """Verify the exact story, integrity and visual rules before resuming."""
    if not path or not Path(path).exists():
        return [], 2
    try:
        target = Path(path)
        if target.stat().st_size > 150_000:
            raise ValueError("Shot checkpoint too large")
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Invalid shot checkpoint schema")
        signature = data.get("signature")
        payload = {k: v for k, v in data.items() if k != "signature"}
        if (set(payload) != {"version", "story_sha256", "batch_size",
                             "accepted_shots", "ready_to_publish",
                             "scientific_facts_verified"} or
            data["version"] != CHECKPOINT_VERSION or
            payload["story_sha256"] != _story_digest(story) or
            payload["ready_to_publish"] is not False or
            payload["scientific_facts_verified"] is not False or
            not isinstance(signature, str) or
            not hmac.compare_digest(signature,
                                    _checkpoint_signature(payload, token))):
            raise ValueError("Checkpoint identity or authentication mismatch")
        size = data["batch_size"]
        if type(size) is not int or size not in (1, 2):
            raise ValueError("Invalid checkpoint batch size")
        shots = data["accepted_shots"]
        if not isinstance(shots, list) or not 1 <= len(shots) <= len(_scene_list(story)):
            raise ValueError("Invalid checkpoint scene count")
        if len(shots) != len(_scene_list(story)) and len(shots) % size:
            raise ValueError("Checkpoint does not end on a complete batch")
        # A formerly accepted, authenticated checkpoint can become invalid
        # when explicit narration constraints are strengthened. NEVER reuse
        # the invalid scene or anything after it. Rewind only the
        # deterministic named factual contradiction, while preserving the
        # complete preceding independently-reviewed batches. Structural
        # corruption, invalid HMAC, altered story and invalid schemas still
        # fail closed rather than silently rewinding.
        try:
            checked = validate_plan(
                {"shots":shots}, {"scenes":_scene_list(story)[:len(shots)]})
            check_explicit_story_constraints(story, checked)
        except ValueError as exc:
            contradicted = re.match(
                r"^Scene (\d+) (?:implies|introduces)\b", str(exc))
            invalid_visual = re.match(
                r"^Scene (\d+): (?:Forbidden diagram or graphic|Unnarrated human presenter|Abstract explanation)\b",
                str(exc))
            repetitive_subject = re.match(
                r"^Repeated central subject in scenes \d+ and (\d+);",
                str(exc))
            if not contradicted and not invalid_visual and not repetitive_subject:
                raise
            first_invalid = int((contradicted or invalid_visual or repetitive_subject).group(1))
            if not 1 <= first_invalid <= len(shots):
                raise
            keep = first_invalid - 1
            # Never keep half of an originally two-shot reviewed batch.
            keep -= keep % size
            safe = shots[:keep]
            if safe:
                validate_plan({"shots":safe},
                              {"scenes":_scene_list(story)[:len(safe)]})
                check_explicit_story_constraints(story, safe)
                # Persist the NEW safe boundary immediately, not only after
                # another model batch happens to pass. Even if Cloudflare
                # fails next, the uploaded checkpoint cannot retain shots
                # already disproved by the current factual policy.
                _write_checkpoint(path, story, safe, size, token)
            else:
                # Delete only after full HMAC/story validation established
                # that no previously saved scene remains reusable.
                Path(path).unlink()
            return safe, size
        return checked, size
    except (OSError, UnicodeError, TypeError, KeyError, json.JSONDecodeError,
            ValueError) as exc:
        raise ValueError("Untrusted or incompatible shot checkpoint: "+
                         str(exc)) from None


def build_plan(story, request, account, token, checkpoint_path=None):
    """Use short, sequential requests for long stories, preserving all guards."""
    scenes = _scene_list(story)
    guarded_request = _retry_timed_out_text_request(request)
    if len(scenes) <= 4:
        return _build_plan_whole(story, guarded_request, account, token)
    accepted, size = _read_checkpoint(checkpoint_path, story, token)
    if len(accepted) == len(scenes):
        return validate_plan({"shots":accepted}, story)
    return _build_plan_chunks(
        story, guarded_request, account, token, chunk_size=size,
        initial_accepted=accepted, start_at=len(accepted),
        on_accepted=(lambda shots, batch_size:
                     _write_checkpoint(checkpoint_path, story, shots,
                                       batch_size, token))
        if checkpoint_path else None)


def _story_visual_constraints(story):
    """Return a grounded positive visual brief, never a topic template."""
    full = " ".join(x["narration"] for x in _scene_list(story)).lower()
    gas = bool(re.search(
        r"(?:mundo gaseoso|planeta[^.]{0,100}(?:gas|gaseoso)|gaseous planet|gas giant)",
        full))
    no_ground = bool(re.search(
        r"(?:no hay (?:un )?suelo|sin superficie s[oó]lida|no solid (?:surface|ground)|without solid ground)",
        full))
    if gas and no_ground:
        return (
            "SCIENCE CONSTRAINT FROM FULL STORY: depict the narrated gas "
            "planet with atmospheric gas layers only. Any temperature or "
            "hydrogen process must take place in gas, not on a physical "
            "landscape or material surface. Use the star only when narrated. "
        )
    return (
        "SCENE CONSTRAINT: Treat negated or absent elements as exclusions, "
        "not objects to illustrate. Depict only positively supported "
        "subjects and processes in the corresponding narration. "
    )


def _build_plan_chunks(story, request, account, token, chunk_size=2,
                       initial_accepted=None, start_at=0, on_accepted=None):
    """Plan in <=2-scene batches; no FLUX or publication can be called here.

    Every completed prefix is structurally revalidated, including visual
    diversity across batch boundaries. Only the current batch is retried.
    Semantic checks use the complete narration for explicit constraints, and
    a short independent story critic evaluates each batch. Any failure blocks
    the whole plan; a partial plan is never returned as approved.
    """
    from scripts.visual_autopilot import _extract_text

    scenes = _scene_list(story)
    if not isinstance(chunk_size, int) or not 1 <= chunk_size <= 4:
        raise ValueError("Invalid bounded shot batch size")
    if start_at < 0 or start_at > len(scenes) or start_at % chunk_size:
        raise ValueError("Invalid shot batch resume boundary")
    accepted = list(initial_accepted or [])
    if len(accepted) != start_at:
        raise ValueError("Shot batch resume does not match accepted prefix")
    if accepted:
        validate_plan({"shots":accepted},{"scenes":scenes[:start_at]})
        check_explicit_story_constraints(story,accepted)
    for start in range(start_at, len(scenes), chunk_size):
        batch = scenes[start:start+chunk_size]
        chunk_story = {"title":story.get("title", "Documentary"),"scenes":batch}
        reason = None
        repair_local = None
        previous_batch = None
        duplicate_reference = None
        attempts = 2
        attempt = 0
        while attempt < attempts:
            attempt += 1
            prior = [{"scene":x["scene"],"scale":x["scale"],
                      "angle":x["angle"],"role":x["role"],
                      "subject":x["subject"],"visible_action":x["visible_action"]}
                     for x in accepted]
            forbidden = [" / ".join((x["scale"],x["angle"],x["role"]))
                         for x in accepted]
            request_text = (
                "Return exactly one valid JSON object and nothing else. "
                "The object MUST contain shots, a list of EXACTLY "+
                str(len(batch))+" objects, with scene numbering 1 to "+
                str(len(batch))+". Do not add extra scenes. "
                "Each shot has keys scene (integer), scale, angle, role, "
                "subject and visible_action. "
                "scale: "+",".join(SCALES)+". angle: "+",".join(ANGLES)+
                ". role: "+",".join(ROLES)+". "
                "Each visible_action must be 6-22 English words describing "
                "a concrete physical action or relationship. Subject and action "
                "must depict the PARTICULAR narrated phenomenon, not a generic "
                "planet, a speaker, a diagram, charts or captions. "
                "Only show facts supported by EACH batch narration below; do not "
                "invent materials, terrain, galaxies, locations or physical surfaces. "
                "NEGATIVE STATEMENTS in narration prohibit, rather than request, "
                "the depicted objects. "+_story_visual_constraints(story)+
                "Avoid repeated composition, central subjects, viewpoint or actions "
                "from earlier shots; distinguish the SPECIFIC physical process "
                "narrated in each scene, not just camera grammar. "
                "Each scale/angle/role triple must be UNIQUE across all batches. "
                "The following triples are FORBIDDEN and must not be selected: "+
                json.dumps(forbidden,ensure_ascii=False)+". "
                "Also use distinct triples inside this batch. "
                "No text outside JSON.\n"
                "TITLE: "+str(story.get("title","Documentary"))[:160]+
                "\nBATCH SCRIPT (local scene numbers):\n"+
                "\n".join(f"{i}. {item['narration']}"
                          for i,item in enumerate(batch,1))+
                "\nPREVIOUS APPROVED SHOTS (do not repeat):\n"+
                json.dumps(prior,ensure_ascii=False)
            )
            if reason is not None:
                request_text += (
                    "\nPREVIOUS BATCH FAILED VALIDATION: "+str(reason)[:500]+
                    "\nReturn ONLY one COMPLETE JSON object with exactly "+
                    str(len(batch))+" shots. No prose, markdown, or partial "
                    "JSON. This is the final bounded retry; never guess "
                    "unsupported scientific content."
                )
            if repair_local is not None and previous_batch is not None:
                request_text = (
                    "Fix ONLY the subject and visible_action of ONE documentary "
                    "shot. Return JSON object with exactly subject and "
                    "visible_action string keys. visible_action MUST contain "
                    "6-22 English words. Aim for 10-16 words showing concrete "
                    "visible subjects and their physical relationship. "
                    "The NARRATION, not the "
                    "reviewer's complaint, is the ONLY positive factual source. "
                    "The ERROR describes unsupported or contradicted claims "
                    "to REMOVE, NEVER facts to illustrate or repeat. "
                    "If a prior shot is duplicated, changing a few adjectives "
                    "is NOT enough: depict a different narrated physical event, "
                    "a different subject relationship, or a demonstrably "
                    "different spatial composition. Keep the intended narration "
                    "and existing camera scale, angle, and role. "
                    "When narration describes gas or molecules, illustrate "
                    "only the narrated gas or molecules, not invented solid "
                    "surfaces, landscapes or background worlds. Do not add "
                    "locations, materials or terrain absent from the narration. "
                    "Do not output a shot list.\n"
                    "ERROR: "+str(reason)[:350]+"\n"
                    "NARRATION: "+batch[repair_local-1]["narration"]+"\n"
                    "PREVIOUS SHOT: "+
                    json.dumps(previous_batch["shots"][repair_local-1],
                               ensure_ascii=False)+
                    ("\nDUPLICATED EARLIER SHOT (do not repeat its concrete "
                     "objects, composition or visible process): "+
                     json.dumps(duplicate_reference,ensure_ascii=False)
                     if duplicate_reference is not None else "")
                )
            # A bounded, schema-constrained final repair uses a stronger
            # existing Workers AI model. No new provider or paid API. The
            # resulting fields still undergo every structural and factual
            # gate; model JSON mode does NOT itself guarantee validity.
            constrained_patch = attempt == 3 and repair_local is not None
            if constrained_patch:
                payload = {
                    "messages":[{"role":"user","content":request_text}],
                    "max_completion_tokens":400, "temperature":0.0,
                    "chat_template_kwargs":{"enable_thinking":False},
                    "response_format":{"type":"json_schema",
                                       "json_schema":SHOT_PATCH_SCHEMA}
                }
                response = request(CRITIC_MODEL,payload,account,token)
            else:
                response = request(MODEL, {"messages":[{"role":"user",
                    "content":request_text}],
                    "max_tokens":350 if repair_local else max(500,len(batch)*250),
                    "temperature":0.1}, account, token)
            attempted_repair_local = repair_local
            attempted_previous_batch = previous_batch
            attempted_duplicate_reference = duplicate_reference
            try:
                # The schema-constrained REST endpoint may return a parsed
                # object in the response envelope instead of a JSON string.
                # Only the schema-patch path unwraps this specific shape.
                if (constrained_patch and isinstance(response,dict) and
                    isinstance(response.get("response"),dict)):
                    parsed = response["response"]
                elif (constrained_patch and isinstance(response,dict) and
                      {"subject","visible_action"}.issubset(response)):
                    parsed = response
                else:
                    parsed = parse_reply(_extract_text(response))
                if repair_local is not None:
                    original=previous_batch["shots"][repair_local-1]
                    # Some models repeat the original shot's metadata instead
                    # of returning only the two requested fields. Accept that
                    # redundant wrapper ONLY if all frozen metadata matches.
                    if isinstance(parsed,dict) and set(parsed)=={"shots"}:
                        arr=parsed["shots"]
                        if not isinstance(arr,list) or len(arr)!=1:
                            raise ValueError("Single-shot batch repair returned invalid fields")
                        parsed=arr[0]
                    elif isinstance(parsed,dict) and set(parsed)=={"shot"}:
                        parsed=parsed["shot"]
                    if not isinstance(parsed,dict):
                        raise ValueError("Single-shot batch repair returned invalid fields")
                    frozen={"scene","scale","angle","role"}
                    editable={"subject","visible_action"}
                    # Accept an explicitly matching absolute scene index on
                    # a resumed documentary, but never a moved or missing
                    # scene or any changed camera metadata.
                    scene_id = parsed.get("scene",original["scene"])
                    if scene_id not in (original["scene"],start+original["scene"]):
                        raise ValueError("Single-shot batch repair returned invalid fields")
                    if (not editable.issubset(parsed) or
                        set(parsed)-editable-frozen or
                        any(parsed.get(k)!=original[k]
                            for k in frozen-{"scene"} if k in parsed) or
                        not all(isinstance(parsed[k],str) for k in editable)):
                        raise ValueError("Single-shot batch repair returned invalid fields")
                    repaired = {"shots":[dict(item) for item in previous_batch["shots"]]}
                    repaired["shots"][repair_local-1].update({
                        key:parsed[key] for key in editable})
                    parsed = repaired
                if isinstance(parsed,dict) and isinstance(parsed.get("shots"),list):
                    if len(parsed["shots"]) != len(batch):
                        raise ValueError("Shot count mismatch: expected "+
                                         str(len(batch))+", received "+
                                         str(len(parsed["shots"])))
                    # When a resumed model uses absolute scene indices
                    # instead of requested local indices, only a complete
                    # exact ascending match may be normalized. Any missing,
                    # repeated, shuffled or invented indices still fail.
                    got = [x.get("scene") if isinstance(x,dict) else None
                           for x in parsed["shots"]]
                    absolute = list(range(start+1,start+len(batch)+1))
                    if start > 0 and got == absolute:
                        parsed = {"shots":[dict(item,scene=i)
                                           for i,item in enumerate(parsed["shots"],1)]}
                # A camera tuple may be repeated by the text planner even
                # when the described physical action is distinct. Resolve
                # only CAMERA ANGLE on unapproved shots with the same scale
                # and narrative role; never touch any accepted shots or the
                # proposed scene content. Then run every original validator.
                if isinstance(parsed,dict) and isinstance(parsed.get("shots"),list):
                    proposed=[dict(item,scene=start+item["scene"])
                              for item in parsed["shots"]
                              if isinstance(item,dict) and type(item.get("scene")) is int]
                    if len(proposed)==len(batch):
                        normalized=_fix_only_current_camera_angle_collisions(
                            accepted+proposed,len(accepted))
                        parsed={"shots":[dict(item,scene=i+1)
                                         for i,item in enumerate(normalized[len(accepted):])]}
                local = validate_plan(parsed,chunk_story)
                current = [dict(item,scene=start+item["scene"]) for item in local]
                candidate = accepted+current
                prefix_story = {"scenes":scenes[:len(candidate)]}
                validate_plan({"shots":candidate},prefix_story)
                check_explicit_story_constraints(story,candidate)
                review_story_consistency(chunk_story,local,request,account,token)
                if on_accepted is not None:
                    on_accepted(candidate, chunk_size)
                accepted = candidate
                break
            except ValueError as exc:
                reason = exc
                # A well-formed but wrongly shaped patch is not approval.
                # Keep the same frozen source shot for ONE strict correction.
                if (attempt == 2 and
                    str(exc) == "Single-shot batch repair returned invalid fields" and
                    attempted_repair_local is not None and
                    attempted_previous_batch is not None):
                    repair_local = attempted_repair_local
                    previous_batch = attempted_previous_batch
                    duplicate_reference = attempted_duplicate_reference
                    attempts = 3
                    continue
                # Only a well-formed, correctly numbered batch can undergo
                # a surgical content repair; malformed plans stay rejected.
                repair_local = None
                previous_batch = None
                duplicate_reference = None
                match = re.search(
                    r"^Scene (\d+): Shot visible_action",str(exc))
                local_index = int(match.group(1)) if match else None
                # A structured factual contradiction points to the LOCAL
                # scene number in this reviewed batch. Repair only that
                # shot's wording, then independently review the full batch
                # again. Never reinterpret an invalid verdict as approval.
                grounding = re.search(
                    r"^Story-grounding review FAIL: scene (\d+):",
                    str(exc))
                if grounding and local_index is None:
                    local_index = int(grounding.group(1))
                presentation = re.search(
                    r"^Scene (\d+): (?:Forbidden diagram or graphic|Unnarrated human presenter|Abstract explanation)\b",
                    str(exc))
                if presentation and local_index is None:
                    index = int(presentation.group(1))
                    if 1 <= index <= len(batch):
                        local_index = index
                    elif start < index <= start+len(batch):
                        local_index = index-start
                # Localize a deterministic contradiction using the absolute
                # scene number. Previously this fell back to rewriting the
                # whole batch, often preserving the forbidden surface.
                contradiction = re.search(
                    r"^Scene (\d+) (?:implies|introduces)\b", str(exc))
                if contradiction and local_index is None:
                    global_scene = int(contradiction.group(1))
                    if start < global_scene <= start+len(batch):
                        local_index = global_scene-start
                repeated = re.search(
                    r"^Near-duplicate visible action in scenes (\d+) and (\d+);",
                    str(exc))
                repeated_subject = re.search(
                    r"^Repeated central subject in scenes (\d+) and (\d+);",
                    str(exc))
                if repeated_subject and local_index is None:
                    prior_index = int(repeated_subject.group(1))
                    repeated_index = int(repeated_subject.group(2))
                    if start < repeated_index <= start+len(batch):
                        local_index = repeated_index-start
                        if prior_index <= len(accepted):
                            duplicate_reference=accepted[prior_index-1]
                        elif start < prior_index <= start+len(batch):
                            if isinstance(parsed,dict) and isinstance(parsed.get("shots"),list):
                                duplicate_reference=parsed["shots"][prior_index-start-1]
                if repeated:
                    prior_index = int(repeated.group(1))
                    repeated_index = int(repeated.group(2))
                    if (start < repeated_index <= start+len(batch) and
                        prior_index < repeated_index):
                        local_index = repeated_index-start
                        if prior_index <= len(accepted):
                            duplicate_reference = accepted[prior_index-1]
                        elif start < prior_index <= start+len(batch):
                            if isinstance(parsed,dict) and isinstance(parsed.get("shots"),list):
                                duplicate_reference = parsed["shots"][prior_index-start-1]
                if (local_index is not None and
                    1 <= local_index <= len(batch) and
                    isinstance(parsed,dict) and
                    isinstance(parsed.get("shots"),list) and
                    len(parsed["shots"])==len(batch) and
                    all(isinstance(item,dict) and item.get("scene")==j
                        for j,item in enumerate(parsed["shots"],1))):
                    repair_local=local_index
                    previous_batch=parsed
                    # When the model's first correction is still too short,
                    # allow ONE additional two-field correction. This applies
                    # only to the exact, numbered, structurally parseable
                    # candidate; never to invented facts, ambiguous critics,
                    # incorrect JSON or other failures.
                    if (attempt == 2 and
                        (re.match(r"^Scene \d+: Shot visible_action",str(exc)) or
                         repeated is not None or
                         repeated_subject is not None or
                         grounding is not None)):
                        # One last schema-constrained repair is appropriate
                        # for a strictly named factual critic rejection too.
                        # Preserve camera grammar and re-run ALL checks.
                        attempts = 3
        else:
            # A malformed two-shot JSON response cannot be trusted or
            # reconstructed. Instead ask for ONE scene at a time, preserving
            # every previously approved shot and all cross-scene safeguards.
            # This fallback is bounded: single-scene mode never recurses.
            if chunk_size == 2 and "invalid JSON" in str(reason):
                return _build_plan_chunks(
                    story, request, account, token, chunk_size=1,
                    initial_accepted=accepted, start_at=start,
                    on_accepted=on_accepted)
            raise ValueError(
                f"Shot batch {start//chunk_size+1} failed twice; no image generation: "+
                str(reason))
    # Recheck all global structural and explicit narrative constraints.
    result = validate_plan({"shots":accepted},story)
    check_explicit_story_constraints(story,result)
    return result

def shot_context(shot):
    return (f"SHOT PLAN, mandatory: {shot['scale']} camera scale; {shot['angle']} viewpoint; "
            f"narrative role {shot['role']}; subject {shot['subject']}; "
            f"visible event {shot['visible_action']}. "
            "Do not replace this with an abstract or generic spiral.")

def plan_file(story_path,out,request,account,token,checkpoint_path=None):
    story=json.loads(Path(story_path).read_text(encoding="utf-8"))
    shots=build_plan(story,request,account,token,checkpoint_path=checkpoint_path)
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
    p.add_argument("--checkpoint",default=None)
    a=p.parse_args()
    account=os.environ.get("CLOUDFLARE_ACCOUNT_ID","")
    token=os.environ.get("CLOUDFLARE_API_TOKEN","")
    if not account or not token:
        raise ValueError("Cloudflare secrets missing")
    result=plan_file(a.story,a.out,_request,account,token,checkpoint_path=a.checkpoint)
    print(json.dumps({"scenes":len(result["shots"]),"new_images":0,
                      "plan_valid":True,"visual_signatures":[
                          "-".join((s["scale"],s["angle"],s["role"])) for s in result["shots"]]},
                     ensure_ascii=False))

if __name__=="__main__":
    main()
