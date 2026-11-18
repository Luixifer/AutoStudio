"""Cost-limited optional FLUX image generation for AutoStudio. Dry-run by default."""
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
MAX_PROMPT = 2048

def scene_prompts(story):
    if not isinstance(story, dict):
        raise ValueError("Storyboard must be a JSON object")
    scenes = story.get("scenes")
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= MAX_SCENES:
        raise ValueError("Storyboard requires 1-24 scenes")
    style = ("Photorealistic premium scientific documentary still; dramatic yet realistic cinematic lighting, "
             "highly detailed natural textures, correct physical scale, beautiful cinematic composition, "
             "clear main subject, no text, no logos, no watermark, no drawing, no sketch.")
    results = []
    for i, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise ValueError("Invalid scene")
        visual = next((scene[k] for k in ("image_prompt", "visual_prompt", "prompt", "visual_brief", "description")
                       if isinstance(scene.get(k), str) and scene[k].strip()), None)
        if visual is None:
            raise ValueError(f"Scene {i} has no explicit visual description")
        if len(visual) > 5000:
            raise ValueError("Visual description too long")
        prompt = f"{style} Subject and composition: {visual.strip()}"
        results.append({"scene": i, "prompt": prompt[:MAX_PROMPT]})
    return results

def image_dimensions(data):
    """Read PNG or JPEG dimensions with bounded header parsing, before Pillow full-decode at render."""
    if len(data) < 24 or len(data) > MAX_BYTES:
        raise ValueError("Image size outside supported bounds")
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        if data[12:16] != b"IHDR":
            raise ValueError("Invalid PNG header")
        width, height = struct.unpack(">II", data[16:24])
        ext = ".png"
    elif data.startswith(b"\xff\xd8"):
        ext = ".jpg"
        width = height = None
        pos = 2
        while pos + 4 <= len(data):
            if data[pos] != 0xff:
                raise ValueError("Malformed JPEG marker")
            while pos < len(data) and data[pos] == 0xff:
                pos += 1
            if pos >= len(data):
                break
            marker = data[pos]
            pos += 1
            if marker in (0xd8, 0xd9):
                continue
            if marker == 0xda:
                break
            if pos + 2 > len(data):
                break
            size = int.from_bytes(data[pos:pos+2], "big")
            if size < 2 or pos + size > len(data):
                raise ValueError("Malformed JPEG segment")
            if marker in (0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf):
                if size < 7:
                    raise ValueError("Malformed JPEG frame")
                height = int.from_bytes(data[pos+3:pos+5], "big")
                width = int.from_bytes(data[pos+5:pos+7], "big")
                break
            pos += size
        if width is None:
            raise ValueError("JPEG dimensions not found")
    else:
        raise ValueError("Provider returned unsupported image format")
    if not 256 <= width <= 4096 or not 256 <= height <= 4096:
        raise ValueError("Image dimensions outside allowed range")
    return width, height, ext

def generate_cloudflare(prompt, account, token, timeout=90):
    if not re.fullmatch(r"[a-fA-F0-9]{32}", account):
        raise ValueError("Invalid Cloudflare account identifier")
    if not token or len(token) > 4096:
        raise ValueError("Missing/invalid Cloudflare token")
    # FLUX.1 Schnell uses 'steps', not 'num_steps'; 8 maximum.
    body = json.dumps({"prompt": prompt[:MAX_PROMPT], "steps": 4}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT.format(account=account), data=body, method="POST",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                raise RuntimeError("Image provider rejected request")
            payload = resp.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Image provider HTTP {exc.code}") from None
    if len(payload) > MAX_BYTES:
        raise ValueError("Provider response too large")
    obj = json.loads(payload)
    if not obj.get("success", False):
        raise RuntimeError("Image provider did not confirm success")
    result = obj.get("result") or {}
    encoded = result.get("image") if isinstance(result, dict) else None
    if not isinstance(encoded, str):
        raise ValueError("Image provider response lacks base64 image")
    raw = base64.b64decode(encoded, validate=True)
    image_dimensions(raw)
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
                width, height, ext = image_dimensions(raw)
                path = out / f"scene_{item['scene']:02d}_v{variant}{ext}"
                path.write_bytes(raw)
                entry["candidates"].append({"variant": variant, "status": "generated",
                    "file": path.name, "sha256": hashlib.sha256(raw).hexdigest(),
                    "dimensions": [width, height], "format": ext[1:]})
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
