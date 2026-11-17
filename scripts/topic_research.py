"""Research candidate collector for arbitrary topics.

This module NEVER claims encyclopaedia excerpts alone are fact-checked science.
It only creates a research dossier for later editorial and independent verification.
No paid model, media generation or YouTube calls.
"""
import argparse
import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from scripts.topic_intake import prepare_topic
from scripts.source_quality import valid_science_lead
from scripts.external_sources import external_leads

WIKIPEDIA_API = "https://es.wikipedia.org/w/api.php"
USER_AGENT = "AutoStudio-Research/0.4 (educational; GitHub Luixifer/AutoStudio)"
MAX_BYTES = 500_000
MAX_EXCERPT = 12000


def focused_query(topic):
    """Second search targeted to the user's *angle*, not a generic synonym dump."""
    from scripts.narration_candidates import normalize
    normalized = normalize(topic)
    if not any(word in normalized.split() for word in ("dentro", "interior", "adentro")):
        return None
    # Ignore question syntax while preserving subject words.
    words = [word for word in normalized.replace("¿", " ").replace("?", " ").split()
             if word not in {"que", "ocurre", "pasa", "sucede", "en", "el", "la", "un", "una",
                             "de", "del", "dentro", "interior", "adentro"}]
    if not words:
        return None
    # For this type of question, an interior-focused query is more useful than
    # a page merely mentioning masses, distances or nearby objects.
    subject = " ".join(words[:7])
    return subject + " interior horizonte"


def fetch_wikipedia_candidates(topic, opener=urlopen):
    """Retrieve relevant encyclopaedia page leads; no independent verification."""
    def query_pages(query):
        params = {
            "action": "query", "generator": "search", "gsrsearch": query,
            "gsrlimit": 5, "prop": "extracts|info",
            "explaintext": "1", "exchars": "15000", "inprop": "url",
            "format": "json", "formatversion": "2",
        }
        url = WIKIPEDIA_API + "?" + urlencode(params)
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with opener(request, timeout=12) as response:
            data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Respuesta de investigación demasiado grande.")
        payload = json.loads(data.decode("utf-8"))
        pages = payload.get("query", {}).get("pages", [])
        if not isinstance(pages, list):
            raise ValueError("Formato inesperado del proveedor de investigación.")
        return pages

    # One extra public API query only for explicit 'inside' questions.
    queries = [topic]
    focused = focused_query(topic)
    if focused:
        queries.append(focused)
    found = []
    seen = set()
    for query in queries:
        for page in query_pages(query):
            title = page.get("title")
            link = page.get("fullurl")
            excerpt = page.get("extract", "")
            if not isinstance(title, str) or not isinstance(link, str) or not isinstance(excerpt, str):
                continue
            if not link.startswith("https://es.wikipedia.org/wiki/"):
                continue
            if link in seen or not excerpt.strip():
                continue
            if not valid_science_lead(topic, title, excerpt):
                continue
            seen.add(link)
            found.append({
                "provider": "Wikipedia en español",
                "title": title[:200], "url": link,
                "excerpt": excerpt.strip()[:MAX_EXCERPT],
                "evidence_level": "secondary_lead_only",
                "license_note": "Resumen de Wikipedia; comprobar CC BY-SA y atribución.",
                "discovery_query": query,
            })
    return found[:8]


def research_topic(topic, collector=fetch_wikipedia_candidates, external_collector=None):
    dossier = prepare_topic(topic)
    if dossier["can_render"]:
        dossier["research"] = {
            "status": "already_curated",
            "note": "El tema pertenece al catálogo existente; esta ejecución no revisa sus fuentes.",
        }
        return dossier
    wiki_error = None
    try:
        wiki_sources = collector(dossier["topic"])
        if not isinstance(wiki_sources, list):
            raise ValueError("Fuentes inválidas.")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        wiki_sources = []
        wiki_error = type(exc).__name__

    # Existing injected collector tests remain network-free. In production we
    # request institutional / bibliographic leads even when Wikipedia fails.
    external_error = None
    if external_collector is None and collector is fetch_wikipedia_candidates:
        external_collector = external_leads
    additional = []
    if external_collector is not None:
        try:
            additional, external_error = external_collector(dossier["topic"])
            if not isinstance(additional, list):
                raise ValueError("Fuentes académicas inválidas.")
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            additional = []
            external_error = type(exc).__name__

    seen = set()
    merged = []
    for item in [*additional, *wiki_sources]:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not isinstance(url, str) or not url.startswith("https://") or url in seen:
            continue
        seen.add(url)
        merged.append(item)
    dossier["sources"] = merged
    status = ("leads_found_not_verified" if merged else
              "unavailable" if wiki_error or external_error else "no_leads")
    dossier["research"] = {
        "status": status,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "note": (
            "NASA: enlaces institucionales seleccionados, no artículos leídos. "
            "Crossref: metadatos de publicaciones, no afirmaciones comprobadas. "
            "Wikipedia: extractos secundarios sin revisión. Falta contrastar hechos."
        ),
        "verified_scientific_sources": 0,
        "wikipedia_error_type": wiki_error,
        "external_error_type": external_error,
        "institutional_leads": sum(s.get("provider") == "NASA Science" for s in merged),
        "academic_metadata_leads": sum(s.get("provider", "").startswith("Crossref") for s in merged),
        "secondary_leads": sum(s.get("provider") == "Wikipedia en español" for s in merged),
    }
    dossier["can_render"] = False
    return dossier


def main():
    parser = argparse.ArgumentParser(description="Recopila pistas públicas sin autorizar un vídeo.")
    parser.add_argument("topic")
    parser.add_argument("--out", help="Ruta del JSON de investigación (no vídeo)")
    args = parser.parse_args()
    dossier = research_topic(args.topic)
    result = json.dumps(dossier, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        from pathlib import Path
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result, encoding="utf-8")
    print(result, end="")


if __name__ == "__main__":
    main()
