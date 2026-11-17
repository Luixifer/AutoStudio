"""Generate short attributed extractive voice candidates from source leads.

These are direct excerpts, NOT an original script, independent fact checking or
permission to synthesize/publish narration. Wikipedia CC BY-SA attribution is kept.
No generative model or paid API is used.
"""
import re
import unicodedata

MAX_CANDIDATES = 6
MAX_QUOTE_CHARS = 190
MIN_QUOTE_CHARS = 45
CC_LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/deed.es"


def _sentences(excerpt):
    if not isinstance(excerpt, str):
        return []
    clean = " ".join(excerpt.replace("\n", " ").split())
    # Only complete candidate sentences; never invent omitted endings.
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑÜ¿¡0-9])", clean)
    return [s for s in sentences if s.endswith((".", "?", "!"))]


def _eligible(sentence):
    if not MIN_QUOTE_CHARS <= len(sentence) <= MAX_QUOTE_CHARS:
        return False
    if any(ch in sentence for ch in "{}[]<>|"):
        return False
    words = sentence.split()
    return 8 <= len(words) <= 32 and not sentence.startswith(("Véase", "Referencias", "Categoría"))


def narration_candidates(dossier, max_candidates=MAX_CANDIDATES):
    if not isinstance(dossier, dict):
        raise ValueError("Expediente inválido.")
    if dossier.get("can_render"):
        return {"status": "existing_catalog", "candidates": [], "approved": False}
    leads = dossier.get("sources", [])
    if not isinstance(leads, list):
        raise ValueError("Referencias inválidas.")
    max_candidates = max(0, min(MAX_CANDIDATES, int(max_candidates)))
    pools = []
    for source in leads[:3]:
        if not isinstance(source, dict) or source.get("evidence_level") != "secondary_lead_only":
            continue
        url = source.get("url")
        if not isinstance(url, str) or not url.startswith("https://es.wikipedia.org/wiki/"):
            continue
        snippets = [s for s in _sentences(source.get("excerpt")) if _eligible(s)]
        if snippets:
            pools.append((source, snippets))
    candidates = []
    # Round robin: avoid six claims from one loosely related search result.
    seen = set()
    cursor = 0
    while pools and len(candidates) < max_candidates:
        source, snippets = pools[cursor % len(pools)]
        sentence = snippets.pop(0) if snippets else None
        if sentence:
            key = unicodedata.normalize("NFKD", sentence).casefold()
            if key not in seen:
                seen.add(key)
                candidates.append({
                    "scene_id": f"draft-{len(candidates)+1:02}",
                    "source_excerpt_exact": sentence,
                    "origin": "extractive_quote_wikipedia_es",
                    "source_title": source.get("title", ""),
                    "source_url": source["url"],
                    "license": "CC BY-SA 4.0 (comprobar licencia específica de la página)",
                    "license_url": CC_LICENSE,
                    "approved": False,
                    "factual_verification": "pending_independent_source",
                    "narration_ready": False,
                })
        else:
            pools.pop(cursor % len(pools))
            if not pools:
                break
            cursor -= 1
        cursor += 1
    return {
        "status": "extractive_candidates_unverified" if candidates else "no_usable_sentences",
        "candidates": candidates,
        "approved": False,
        "can_render": False,
        "note": (
            "Las frases son citas textuales atribuidas a Wikipedia, no guion original. "
            "Requieren comprobación independiente, revisión y respeto de CC BY-SA."
        ),
    }
