"""Conservative visual near-duplicate detector; never grants editorial approval.

Independent of LLM captions, requires Pillow already present in requirements.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError

MAX_IMAGES = 24
MAX_PIXELS = 25_000_000
MAX_FILE_BYTES = 15_000_000
HAMMING_CUTOFF = 5  # out of 64 bits; only flag near-identical arrangements


def fingerprint(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Missing or oversized image")
    try:
        with Image.open(path) as im:
            if im.width < 64 or im.height < 64 or im.width * im.height > MAX_PIXELS:
                raise ValueError("Unsupported image dimensions")
            if im.format not in ("PNG", "JPEG", "WEBP"):
                raise ValueError("Only PNG/JPEG/WEBP images are supported")
            img = ImageOps.exif_transpose(im).convert("L")
            # Low-information fields have too many collisions to make a useful decision.
            contrast = ImageStat.Stat(img.resize((64, 64))).stddev[0]
            tiny = img.resize((9, 8), Image.Resampling.LANCZOS)
            p = list(tiny.getdata())
            bits = 0
            for y in range(8):
                for x in range(8):
                    bits = (bits << 1) | (1 if p[y * 9 + x] > p[y * 9 + x + 1] else 0)
            return {"path": str(path), "width": im.width, "height": im.height,
                    "hash64": f"{bits:016x}", "contrast": round(contrast, 3),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Unreadable image") from exc


def audit(paths):
    paths = list(paths)
    if not 2 <= len(paths) <= MAX_IMAGES or len(set(map(str, paths))) != len(paths):
        raise ValueError("Provide 2-24 unique image paths")
    images = [fingerprint(p) for p in paths]
    pairs = []
    for i in range(len(images)):
        for j in range(i + 1, len(images)):
            left, right = images[i], images[j]
            distance = (int(left["hash64"], 16) ^ int(right["hash64"], 16)).bit_count()
            identical = left["sha256"] == right["sha256"]
            low_information = min(left["contrast"], right["contrast"]) < 7.0
            if identical:
                verdict = "DUPLICATE"
            elif low_information:
                verdict = "UNSURE"
            elif distance <= HAMMING_CUTOFF:
                verdict = "POSSIBLE_DUPLICATE"
            else:
                verdict = "DISTINCT_BY_HASH"
            pairs.append({"scene_a": i + 1, "scene_b": j + 1,
                          "hamming_distance": distance, "verdict": verdict})
    flags = [p for p in pairs if p["verdict"] in ("DUPLICATE", "POSSIBLE_DUPLICATE")]
    return {"schema": 1, "method": "perceptual-dhash-9x8", "images": images,
            "pairs": pairs, "possible_duplicate_pairs": flags,
            "editorial_approved": False, "scientific_facts_verified": False,
            "ready_to_publish": False,
            "note": "DISTINCT_BY_HASH does not prove different compositions. AI and human reviews remain mandatory."}


def main():
    parser = argparse.ArgumentParser(description="Offline image near-duplicate QA; does not publish")
    parser.add_argument("images", nargs="+")
    parser.add_argument("--out", default="output/image-duplicate-audit.json")
    args = parser.parse_args()
    report = audit(args.images)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Images: {len(report['images'])}, flagged pairs: {len(report['possible_duplicate_pairs'])}; editorial approval: false")


if __name__ == "__main__":
    main()
