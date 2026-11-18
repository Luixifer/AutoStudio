"""Second Cloudflare vision provider: Gemma 4. Never approve unverifiable output.

Uses Workers AI image_url message parts and the same model's image comprehension
(not a second text-only model pretending to have inspected an image).
"""
from __future__ import annotations
import base64
import re

from scripts.image_generation import image_dimensions
from scripts.visual_autopilot import _request, _extract_text

GEMMA_VISION_MODEL = "@cf/google/gemma-4-26b-a4b-it"

def _parse_verdict(answer):
    if not isinstance(answer, str):
        answer = ""
    # Deliberately accept only the documented 2-line decision; ambiguous replies
    # stay UNSURE, avoiding unsafe optimistic approvals.
    decision = re.search(r"(?im)^\s*DECISION:\s*(PASS|FAIL|UNSURE)\s*$", answer)
    evidence = re.search(r"(?im)^\s*EVIDENCE:\s*(.{8,380})\s*$", answer)
    if not decision or not evidence:
        return {"decision": "UNSURE", "evidence": "Unparseable Gemma vision response.",
                "raw_excerpt": answer[:220], "method": "gemma4_unparseable"}
    return {"decision": decision.group(1).upper(),
            "evidence": evidence.group(1).strip(), "method": "gemma4_multimodal"}

def evaluate_gemma(image_bytes, narration, scene_prompt, account, token):
    _, _, ext = image_dimensions(image_bytes)
    mime = "image/png" if ext == ".png" else "image/jpeg"
    image_uri = "data:" + mime + ";base64," + base64.b64encode(image_bytes).decode("ascii")
    instruction = (
        "You are inspecting the ATTACHED IMAGE, not imagining the intended scene. "
        "Judge visual match to the planned shot. Distinguish actual visible evidence "
        "from speculative science. Mark FAIL only when an obvious mismatch is visible: "
        "different main object, wrong solid versus gaseous environment, lettering or "
        "watermarks, or rough sketch instead of completed cinematic art. "
        "Mark UNSURE when the image or scene is ambiguous. Do not invent facts. "
        "Output EXACTLY TWO LINES, no formatting or commentary:\n"
        "DECISION: PASS or FAIL or UNSURE\n"
        "EVIDENCE: one sentence of observable visual evidence.\n"
        "Narration: " + narration[:560] + "\n"
        "Intended shot: " + scene_prompt[:800]
    )
    result = _request(GEMMA_VISION_MODEL, {
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": instruction},
            {"type": "image_url", "image_url": {"url": image_uri}}
        ]}],
        "max_tokens": 200,
        "temperature": 0
    }, account, token)
    answer = _extract_text(result)
    verdict = _parse_verdict(answer)
    verdict["model"] = GEMMA_VISION_MODEL
    if verdict["decision"] == "UNSURE":
        verdict["response_keys"] = sorted(str(k)[:50] for k in result.keys()) if isinstance(result, dict) else []
    return verdict
