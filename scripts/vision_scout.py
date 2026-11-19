"""Independent Llama 4 Scout image QA. It cannot authorize publication.

Unlike generic aesthetic review, this requests observable evidence about the
specific target object. A vague or malformed reply is UNSURE, never PASS.
"""
from __future__ import annotations

import base64
import re

from scripts.image_generation import image_dimensions
from scripts.visual_autopilot import _request
from scripts.vision_gemma import _final_answer

SCOUT_MODEL = "@cf/meta/llama-4-scout-17b-16e-instruct"
_ALLOWED = frozenset(("PASS", "FAIL", "UNSURE"))


def parse_scout(answer):
    if not isinstance(answer, str):
        answer = ""
    patterns = {
        key: re.findall(r"(?im)^\s*" + key +
                        r":\s*(PASS|FAIL|UNSURE|YES|NO)\s*$", answer)
        for key in ("DECISION", "STAR", "GAS_PLANET")
    }
    evidence = re.findall(r"(?im)^\s*EVIDENCE:\s*(.{12,350})\s*$", answer)
    if (len(patterns["DECISION"]) != 1 or not evidence or
            len(evidence) != 1 or patterns["DECISION"][0] not in _ALLOWED):
        return {"decision": "UNSURE", "evidence": "Unparseable Scout verdict.",
                "method": "llama4_scout_unparseable"}
    decision = patterns["DECISION"][0]
    # If a requested astronomical comparison omits the two object checks,
    # do not silently trust a one-line PASS.
    if any(len(patterns[key]) != 1 for key in ("STAR", "GAS_PLANET")):
        decision = "UNSURE"
    elif "NO" in (patterns["STAR"][0], patterns["GAS_PLANET"][0]):
        decision = "FAIL"
    elif any(patterns[key][0] == "UNSURE" for key in ("STAR", "GAS_PLANET")):
        decision = "UNSURE" if decision == "PASS" else decision
    return {"decision": decision, "evidence": evidence[0].strip(),
            "star_visible": patterns["STAR"][0] if len(patterns["STAR"]) == 1 else "UNSURE",
            "gas_planet_visible": patterns["GAS_PLANET"][0] if len(patterns["GAS_PLANET"]) == 1 else "UNSURE",
            "method": "llama4_scout_multimodal"}


def evaluate_scout(image_bytes, narration, expected_visual, account, token):
    """Inspect the actual pixels; compare star and planet explicitly."""
    _, _, ext = image_dimensions(image_bytes)
    uri = ("data:image/png;base64," if ext == ".png" else "data:image/jpeg;base64,") + (
        base64.b64encode(image_bytes).decode("ascii"))
    instruction = (
        "Inspect the ATTACHED image, not the desired image. Be skeptical. "
        "This is an orbital astronomy scene that MUST contain TWO distinct "
        "celestial objects: (1) a genuinely star-like, luminous host STAR "
        "with self-emitting brilliant light and (2) a smaller GASEOUS PLANET "
        "with an atmosphere, not a rocky sphere. A bright blue ball resembling "
        "a second planet is NOT automatically a star. Do not infer a missing "
        "star from the caption, prompt or generic space aesthetic. "
        "If one object is missing or visibly wrong mark FAIL. "
        "If uncertain, UNSURE, never PASS. "
        "Answer EXACTLY four lines:\n"
        "STAR: YES or NO or UNSURE\n"
        "GAS_PLANET: YES or NO or UNSURE\n"
        "DECISION: PASS or FAIL or UNSURE\n"
        "EVIDENCE: a concrete visible observation (12-200 characters).\n"
        "Original narration: " + narration[:520] + "\n"
        "Desired visual (not evidence): " + expected_visual[:700]
    )
    response = _request(SCOUT_MODEL, {
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": instruction},
            {"type": "image_url", "image_url": {"url": uri}}
        ]}],
        "temperature": 0, "max_tokens": 360, "stream": False
    }, account, token)
    result = parse_scout(_final_answer(response))
    result["model"] = SCOUT_MODEL
    return result


def independent_gate(gemma, scout):
    """Never interpret two model PASS results as final editorial permission."""
    g = gemma.get("decision") if isinstance(gemma, dict) else None
    s = scout.get("decision") if isinstance(scout, dict) else None
    if "FAIL" in (g, s):
        result = "FAIL"
    elif g == "PASS" and s == "PASS":
        result = "AUTOMATED_PASS_ONLY"
    else:
        result = "UNSURE"
    return {"automated_result": result,
            "human_visual_approved": False,
            "scientific_facts_verified": False,
            "ready_to_publish": False,
            "youtube_enabled": False}
