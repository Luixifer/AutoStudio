"""Single command for free-topic research and storyboard preparation.

No synthetic narration, generated imagery, paid inference or public upload.
A new topic always results in an UNAPPROVED editorial dossier.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from scripts.topic_research import research_topic
from scripts.storyboard_draft import draft_storyboard
from scripts.narration_candidates import narration_candidates
from scripts.nasa_reading import fetch_nasa_evidence

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "output" / "research"


def prepare_research_package(topic, researcher=research_topic, nasa_reader=None):
    dossier = researcher(topic)
    outline = draft_storyboard(dossier)
    excerpt_candidates = narration_candidates(dossier)
    if nasa_reader is None and researcher is research_topic:
        nasa_reader = fetch_nasa_evidence
    nasa_evidence = (nasa_reader(dossier['topic']) if nasa_reader is not None and not dossier.get('can_render')
                     else {'status':'not_requested','passages':[],'errors':[]})
    if dossier.get("can_render"):
        state = "existing_catalog"
    elif dossier.get("research", {}).get("status") == "unavailable":
        state = "research_unavailable"
    else:
        state = "editorial_review_required"
    return {
        "schema": 1,
        "topic": dossier["topic"],
        "key": dossier["key"],
        "state": state,
        "safe_for_render": bool(dossier.get("can_render", False)),
        "existing_topic_id": dossier.get("topic_id"),
        "dossier": dossier,
        "storyboard": outline,
        "narration_candidates": excerpt_candidates,
        "nasa_evidence": nasa_evidence,
        "paid_api_allowed": False,
        "youtube_enabled": False,
        "disclaimer": (
            "Expediente de investigación, no vídeo. Las frases preliminares son "
            "extractos textuales atribuidos; no son guion original ni afirmaciones "
            "científicamente comprobadas. Falta verificación, revisión y arte visual."
        ),
    }


def write_package(package, root=OUTPUT_ROOT):
    """Write only below controlled output directory, without using raw topic as path."""
    key = package.get("key")
    if not isinstance(key, str) or not key or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in key):
        raise ValueError("Identificador de tema inválido.")
    base = Path(root)
    base.mkdir(parents=True, exist_ok=True)
    target = base / (key + ".json")
    payload = json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    # Atomic replacement so interruptions do not leave a partial JSON file.
    temporary = base / (key + ".partial")
    try:
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def main():
    parser = argparse.ArgumentParser(description="Investigación preliminar + storyboard (sin vídeo).")
    parser.add_argument("topic")
    parser.add_argument("--out-dir", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    package = prepare_research_package(args.topic)
    file = write_package(package, args.out_dir)
    print(json.dumps({
        "topic": package["topic"],
        "state": package["state"],
        "safe_for_render": package["safe_for_render"],
        "file": str(file),
        "source_leads": len(package["dossier"].get("sources", [])),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
