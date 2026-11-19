"""Controlled A/B quality check: archived 4B vs one fresh 9B image.

One new FLUX request maximum, at most four vision inspections, no publication.
The existing 4B frame and prompt come from a previous signed GitHub artifact.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path

from scripts.flux2_klein_9b import generate_klein9b
from scripts.image_generation import image_dimensions
from scripts.vision_gemma import evaluate_gemma
from scripts.vision_scout import evaluate_scout, independent_gate

MAX_NEW_IMAGE_REQUESTS = 1


def compare(reference_dir, output_dir, narration, account, token,
            *, live=False, generator=generate_klein9b,
            gemma=evaluate_gemma, scout=evaluate_scout):
    source = Path(reference_dir)
    spec_file = source / "orbit-qa.json"
    if not spec_file.is_file():
        raise ValueError("Source 4B provenance manifest missing")
    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    if spec.get("scene") != 8 or spec.get("image_generated") is not True:
        raise ValueError("Reference scene 8 is not verified")
    prompt = spec.get("prompt")
    filename = spec.get("file")
    if not isinstance(prompt, str) or not 20 <= len(prompt) <= 2000:
        raise ValueError("Reference prompt unavailable")
    if not isinstance(filename, str) or Path(filename).name != filename:
        raise ValueError("Unsafe reference file")
    source_image = source / filename
    if not source_image.is_file():
        raise ValueError("Archived 4B image is missing")
    original = source_image.read_bytes()
    w, h, _ = image_dimensions(original)
    if [w, h] != spec.get("dimensions"):
        raise ValueError("Reference image dimensions do not match manifest")
    if hashlib.sha256(original).hexdigest() != spec.get("sha256"):
        raise ValueError("Reference image SHA mismatch")
    if live and (not account or not token):
        raise ValueError("Cloudflare credentials missing")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    data = {
        "schema": 1, "scene": 8, "prompt": prompt,
        "new_image_request_ceiling": MAX_NEW_IMAGE_REQUESTS,
        "new_image_requests_attempted": 0, "results": [],
        "human_visual_approved": False,
        "scientific_facts_verified": False,
        "ready_to_publish": False, "youtube_enabled": False
    }

    def quality(label, pixels, image_model, name):
        entry = {
            "model": image_model, "label": label, "file": name,
            "sha256": hashlib.sha256(pixels).hexdigest(),
            "dimensions": list(image_dimensions(pixels)[:2]),
            "gemma": {"decision": "UNSURE"},
            "scout": {"decision": "UNSURE"}
        }
        data["results"].append(entry)
        if not live:
            entry["inspection"] = independent_gate(entry["gemma"],entry["scout"])
            return
        for key, evaluator in (("gemma", gemma), ("scout", scout)):
            try:
                verdict = evaluator(pixels, narration, prompt, account, token)
                if (not isinstance(verdict, dict) or
                        verdict.get("decision") not in ("PASS", "FAIL", "UNSURE")):
                    raise ValueError("Unsupported verdict")
                entry[key] = verdict
            except Exception as exc:
                entry[key] = {"decision": "UNSURE",
                              "evidence": "Inspection unavailable: " + type(exc).__name__}
        entry["inspection"] = independent_gate(entry["gemma"],entry["scout"])

    try:
        (out / "comparison_4b.jpg").write_bytes(original)
        quality("archived_4b", original, "@cf/black-forest-labs/flux-2-klein-4b",
                "comparison_4b.jpg")
        if live:
            # Exactly one new image call; the counter increments BEFORE it.
            data["new_image_requests_attempted"] = 1
            pixels = generator(prompt, account, token)
            size = image_dimensions(pixels)
            (out / ("comparison_9b" + size[2])).write_bytes(pixels)
            quality("new_9b", pixels, "@cf/black-forest-labs/flux-2-klein-9b",
                    "comparison_9b" + size[2])
    except Exception as exc:
        data["error"] = type(exc).__name__ + ": " + str(exc)[:160]
        # Never translate the API rejection into a success verdict.
        raise
    finally:
        (out / "comparison-results.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    return data


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reference", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--story", required=True)
    p.add_argument("--live", action="store_true")
    p.add_argument("--max-new-images", type=int, default=1)
    a = p.parse_args()
    if a.max_new_images != 1:
        raise ValueError("Only one new image may be requested")
    story = json.loads(Path(a.story).read_text(encoding="utf-8"))
    narration = story["scenes"][7]["narration"]
    answer = compare(a.reference, a.out, narration,
                     os.environ.get("CLOUDFLARE_ACCOUNT_ID", ""),
                     os.environ.get("CLOUDFLARE_API_TOKEN", ""),
                     live=a.live)
    print("A_B_COMPLETED", len(answer["results"]), "NEW_REQUESTS",
          answer["new_image_requests_attempted"], "PUBLISH_ALLOWED", False)


if __name__ == "__main__":
    main()
