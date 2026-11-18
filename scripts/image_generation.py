"""Opt-in, budget-limited image generation. No credentials or billable fallback."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import urllib.error
import urllib.request

MODEL = "@cf/black-forest-labs/flux-1-schnell"
ENDPOINT = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/" + MODEL
MAX_SCENES = 24
MAX_VARIANTS = 3
MAX_BYTES = 12_000_000

def scene_prompts(story):
    if not isinstance(story, dict):
        raise ValueError("Storyboard must be a JSON object")
    scenes = story.get("scenes")
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= MAX_SCENES:
        raise ValueError("Storyboard requires 1-24 scenes")
    style = "Photorealistic premium scientific documentary still, cinematic lighting, natural textures, coherent physical scale, 16:9 composition, generous safe margins for slow camera motion, no captions, no letters, no watermark, no sketch, no concept art."
    results = []
    for i, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise ValueError("Invalid scene")
        visual = next((scene[k] for k in ("image_prompt", "visual_prompt", "prompt", "visual_brief", "description") if isinstance(scene.get(k), str) and scene[k].strip()), None)
        if visual is None:
            # Fail closed rather than inventing an unrelated picture from narration.
            raise ValueError(f"Scene {i} has no explicit visual description")
        if len(visual) > 5000:
            raise ValueError("Visual description too long")
        prompt = f"{style} Subject and composition: {visual.strip()}"
        results.append({"scene": i, "prompt": prompt[:6000]})
    return results

def png_dimensions(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 24:
        raise ValueError("Provider returned no valid PNG")
    w, h = struct.unpack(">II", data[16:24])
    if not 512 <= w <= 4096 or not 512 <= h <= 4096:
        raise ValueError("Image dimensions outside allowed range")
    return w, h

def generate_cloudflare(prompt, account, token, timeout=90):
    if not re.fullmatch(r"[a-fA-F0-9]{32}", account):
        raise ValueError("Invalid Cloudflare account identifier")
    if not token or len(token) > 4096:
        raise ValueError("Missing/invalid Cloudflare token")
    body = json.dumps({"prompt": prompt, "num_steps": 4}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT.format(account=account), data=body, method="POST",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                raise RuntimeError("Image provider rejected request")
            payload = resp.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        # Never include response bodies: they can contain sensitive provider metadata.
        raise RuntimeError(f"Image provider HTTP {exc.code}") from None
    if len(payload) > MAX_BYTES:
        raise ValueError("Provider response too large")
    obj = json.loads(payload)
    if not obj.get("success", False):
        raise RuntimeError("Image provider did not confirm success")
    result = obj.get("result") or {}
    encoded = result.get("image") if isinstance(result, dict) else None
    if not isinstance(encoded, str):
        raise ValueError("Image provider response lacks base64 PNG")
    raw = base64.b64decode(encoded, validate=True)
    png_dimensions(raw)
    return raw

def build(story_path, output, variants=1, live=False, max_requests=24):
    if not 1 <= variants <= MAX_VARIANTS:
        raise ValueError("variants must be between 1 and 3")
    story = json.loads(Path(story_path).read_text(encoding="utf-8"))
    prompts = scene_prompts(story)
    planned = len(prompts) * variants
    if planned > max_requests or max_requests > 72 or max_requests < 1:
        raise ValueError("Request budget exceeded; no requests made")
    account = os.getenv("CLOUDFLARE_ACCOUNT_ID", "") if live else ""
    token = os.getenv("CLOUDFLARE_API_TOKEN", "") if live else ""
    if live and (not account or not token):
        raise ValueError("Live generation requires Cloudflare secrets; no requests made")
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": 1, "provider": "cloudflare-flux-schnell" if live else "dry-run",
                "model": MODEL, "planned_requests": planned, "completed_requests": 0,
                "automatic_quality_approval": False, "scenes": []}
    try:
        for item in prompts:
            entry = {**item, "candidates": []}
            manifest["scenes"].append(entry)
            for variant in range(1, variants + 1):
                if not live:
                    entry["candidates"].append({"variant": variant, "status": "planned"})
                    continue
                raw = generate_cloudflare(item["prompt"], account, token)
                path = out / f"scene_{item['scene']:02d}_v{variant}.png"
                path.write_bytes(raw)
                entry["candidates"].append({"variant": variant, "status": "generated",
                    "file": path.name, "sha256": hashlib.sha256(raw).hexdigest(),
                    "dimensions": list(png_dimensions(raw))})
                manifest["completed_requests"] += 1
    finally:
        (out / "image-generation-manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest

def main():
    p = argparse.ArgumentParser(description="Opt-in image generator; dry-run by default")
    p.add_argument("--story", required=True)
    p.add_argument("--out", default="output/generated-images")
    p.add_argument("--variants", type=int, default=1)
    p.add_argument("--max-requests", type=int, default=24)
    p.add_argument("--live", action="store_true")
    args = p.parse_args()
    result = build(args.story, args.out, args.variants, args.live, args.max_requests)
    print(json.dumps({"planned": result["planned_requests"],
                      "completed": result["completed_requests"], "live": args.live}))

if __name__ == "__main__":
    main()
