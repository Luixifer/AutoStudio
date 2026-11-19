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

def _final_answer(result):
    """Read only a final answer, not thought/reasoning fields."""
    answer = _extract_text(result)
    if answer:
        return answer
    if not isinstance(result, dict):
        return ""
    choices = result.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return ""
    first = choices[0]
    if isinstance(first.get("text"), str) and first["text"].strip():
        return first["text"].strip()
    for key in ("message", "delta"):
        msg = first.get(key)
        if not isinstance(msg, dict):
            continue
        c = msg.get("content")
        if isinstance(c, str):
            return c.strip()
        if isinstance(c, list):
            return "\n".join(part["text"] for part in c if isinstance(part, dict)
                              and part.get("type") in ("text", "output_text")
                              and isinstance(part.get("text"), str)).strip()
    return ""

def _safe_shape(result):
    """Metadata only: no image, token, model thoughts, or user text."""
    if not isinstance(result, dict):
        return {"result_type": type(result).__name__}
    out = {"keys": sorted(str(k)[:40] for k in result.keys())[:20]}
    choices = result.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        ch = choices[0]
        out["choice_keys"] = sorted(str(k)[:40] for k in ch.keys())[:20]
        out["finish_reason"] = str(ch.get("finish_reason", ""))[:40]
        msg = ch.get("message")
        if isinstance(msg, dict):
            out["message_keys"] = sorted(str(k)[:40] for k in msg.keys())[:20]
            for k in ("content", "reasoning_content"):
                item = msg.get(k)
                out[k + "_type"] = type(item).__name__
                out[k + "_length"] = len(item) if isinstance(item, (str, list)) else 0
    usage = result.get("usage") or result.get("metrics")
    if isinstance(usage, dict):
        out["usage_keys"] = sorted(str(k)[:40] for k in usage.keys())[:16]
    return out

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
        "max_tokens": 1600,
        "temperature": 0,
        "reasoning_effort": "none"
    }, account, token)
    answer = _final_answer(result)
    verdict = _parse_verdict(answer)
    verdict["model"] = GEMMA_VISION_MODEL
    if verdict["decision"] == "UNSURE":
        verdict["response_keys"] = sorted(str(k)[:50] for k in result.keys()) if isinstance(result, dict) else []
        verdict["response_shape"] = _safe_shape(result)
    return verdict
