"""Cloudflare FLUX cinematic pilot: three opt-in images, review only, never publish.

Uses authenticated text-preflight checkpoint, original narration and existing
FLUX/Gemma providers. Explicit per-run ceiling; all image output is a draft.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from scripts.image_generation import generate_cloudflare, image_dimensions
from scripts.shot_preflight import _read_checkpoint, _scene_list, validate_plan, check_explicit_story_constraints

MAX_PILOT_REQUESTS = 3
PILOT_SCENES = (1, 6, 8)

ART_DIRECTION = {
    1: ("Very wide cinematic deep-space view, the luminous gaseous exoplanet "
        "KELT-9b clearly visible beside the brilliant parent star. Establish "
        "the scale and extreme day-side heat with a believable atmospheric "
        "glow, not a rocky or molten surface."),
    6: ("Scientific CGI reconstruction at molecular scale: two bonded hydrogen "
        "atoms in an H2 molecule separating into two neutral hydrogen atoms "
        "as the surrounding gas becomes very hot. Distinct atoms, neutral "
        "molecules only; NOT stripped electrons, NOT ionization. Avoid "
        "planetary terrain, invented laboratory settings and typography."),
    8: ("Very wide three-quarter orbital relationship view: the gas giant "
        "KELT-9b extremely close to its much larger, bright host star, "
        "emphasizing the compact orbit; the narration explains its roughly "
        "36-hour year. Do not invent visible orbit lines, clock faces, "
        "time labels, Earth or infographic elements.")
}


def image_prompt(scene_number, narration, shot):
    if scene_number not in PILOT_SCENES:
        raise ValueError("Only the three approved pilot scenes can be generated")
    if not isinstance(narration, str) or len(narration) < 12:
        raise ValueError("Narration missing")
    if shot.get("scene") != scene_number:
        raise ValueError("Scene/shot mismatch")
    return (
        "Premium astronomy documentary, original cinematic CGI still, "
        "natural physically plausible lighting, richly detailed, highly "
        "legible subject hierarchy, spacious widescreen 16:9 composition "
        "with central crop safety, consistent deep-space art direction. "
        "No humans, no charts, no captions, no typography, no watermark, "
        "no fictional solid terrain on a gas giant. "
        + ART_DIRECTION[scene_number] + " "
        "Validated film shot: " + shot["subject"] + ". "
        "Narrated physical event: " + shot["visible_action"] + "."
    )[:2000]


def pilot(story, checkpoint_path, out_dir, account, token, live=False,
          generator=generate_cloudflare, reviewer=None, scout_reviewer=None):
    """Always preserve a manifest; never interpret AI QA as publishing approval."""
    if live and (not account or not token):
        raise ValueError("Live pilot needs existing Cloudflare secrets")
    scenes = _scene_list(story)
    if len(scenes) < max(PILOT_SCENES):
        raise ValueError("Storyboard missing pilot scenes")
    shots, _ = _read_checkpoint(checkpoint_path, story, token)
    if len(shots) != len(scenes):
        raise ValueError("Full authenticated plan not approved; FLUX disabled")
    validate_plan({"shots": shots}, story)
    check_explicit_story_constraints(story, shots)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": 1, "pilot": "KELT-9b cinematic three-shot",
        "mode": "live" if live else "dry-run",
        "scene_indices": list(PILOT_SCENES),
        "max_image_requests": MAX_PILOT_REQUESTS,
        "completed_image_requests": 0, "scenes": [],
        "human_visual_approved": False,
        "scientific_facts_verified": False,
        "ready_to_publish": False, "youtube_enabled": False
    }
    # Two actual image inspectors by default in live mode; injection disables
    # accidental network calls in offline tests.
    if reviewer is None and live:
        from scripts.vision_gemma import evaluate_gemma
        from scripts.vision_scout import evaluate_scout
        reviewer = evaluate_gemma
        if scout_reviewer is None:
            scout_reviewer = evaluate_scout
    try:
        for number in PILOT_SCENES:
            narration = scenes[number - 1]["narration"]
            shot = shots[number - 1]
            prompt = image_prompt(number, narration, shot)
            entry = {"scene": number, "narration": narration, "prompt": prompt,
                     "image_generated": False, "vision": {
                         "decision": "NOT_EVALUATED"}}
            result["scenes"].append(entry)
            if not live:
                continue
            if result["completed_image_requests"] >= MAX_PILOT_REQUESTS:
                raise RuntimeError("Image request budget exhausted")
            # Count requests BEFORE calling an external provider so failures
            # cannot trigger hidden retries outside the explicit ceiling.
            result["completed_image_requests"] += 1
            raw = generator(prompt, account, token)
            width, height, ext = image_dimensions(raw)
            name = f"kelt9b_pilot_scene_{number:02d}{ext}"
            (out / name).write_bytes(raw)
            entry.update({"image_generated": True, "file": name,
                          "sha256": hashlib.sha256(raw).hexdigest(),
                          "dimensions": [width, height]})
            if reviewer:
                try:
                    evaluation = reviewer(raw, narration, prompt, account, token)
                    if not isinstance(evaluation, dict) or evaluation.get("decision") not in (
                            "PASS", "FAIL", "UNSURE"):
                        raise ValueError("Vision response is unverified")
                    entry["vision"] = evaluation
                except Exception as exc:
                    entry["vision"] = {"decision": "UNSURE",
                                       "evidence": "Vision evaluation unavailable: " +
                                       type(exc).__name__}
            entry["scout"] = {"decision": "UNSURE",
                              "evidence": "Independent model not evaluated"}
            if scout_reviewer:
                try:
                    # H2 scientific reconstruction is inspected differently
                    # from scenes that require a luminous star plus gas giant.
                    kind = "hydrogen" if number == 6 else "orbit"
                    verdict = scout_reviewer(raw, narration, prompt, account, token,
                                             scene_kind=kind)
                    if not isinstance(verdict, dict) or verdict.get("decision") not in (
                            "PASS", "FAIL", "UNSURE"):
                        raise ValueError("Scout verdict malformed")
                    entry["scout"] = verdict
                except Exception as exc:
                    entry["scout"] = {"decision": "UNSURE",
                                      "evidence": "Scout unavailable: " + type(exc).__name__}
            from scripts.vision_scout import independent_gate
            entry["independent_review"] = independent_gate(
                entry["vision"], entry["scout"])
    finally:
        (out / "cinematic-pilot-manifest.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description="Safe three-scene cinematic test")
    parser.add_argument("--story", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--image-model",
                        choices=("flux1-schnell", "flux2-klein-4b", "flux2-klein-9b"),
                        default="flux1-schnell")
    parser.add_argument("--max-requests", type=int, default=3)
    args = parser.parse_args()
    if args.max_requests != MAX_PILOT_REQUESTS:
        raise ValueError("This pilot requires an explicit three-image ceiling")
    story = json.loads(Path(args.story).read_text(encoding="utf-8"))
    if args.image_model == "flux1-schnell":
        generator = generate_cloudflare
    elif args.image_model == "flux2-klein-4b":
        from scripts.flux2_klein import generate_klein
        generator = generate_klein
    else:
        from scripts.flux2_klein_9b import generate_klein9b
        generator = generate_klein9b
    output = pilot(story, args.checkpoint, args.out,
                   os.getenv("CLOUDFLARE_ACCOUNT_ID", ""),
                   os.getenv("CLOUDFLARE_API_TOKEN", ""), live=args.live,
                   generator=generator)
    print(json.dumps({
        "mode": output["mode"],
        "completed_requests": output["completed_image_requests"],
        "generated": sum(x["image_generated"] for x in output["scenes"]),
        "ready_to_publish": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
