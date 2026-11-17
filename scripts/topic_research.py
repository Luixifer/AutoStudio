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

WIKIPEDIA_API = "https://es.wikipedia.org/w/api.php"
USER_AGENT = "AutoStudio-Research/0.4 (educational; GitHub Luixifer/AutoStudio)"
MAX_BYTES = 500_000
MAX_EXCERPT = 1200


def fetch_wikipedia_candidates(topic, opener=urlopen):
    """Collect up to three public page leads; links are NOT independent verification."""
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": topic,
        "gsrlimit": 3,
        "prop": "extracts|info",
        "exintro": "1",
        "explaintext": "1",
        "exchars": "1600",
        "inprop": "url",
        "format": "json",
        "formatversion": "2",
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
    sources = []
    for page in pages:
        title = page.get("title")
        link = page.get("fullurl")
        excerpt = page.get("extract", "")
        if not isinstance(title, str) or not isinstance(link, str) or not isinstance(excerpt, str):
            continue
        # Do not trust arbitrary URLs returned by an upstream service.
        if not link.startswith("https://es.wikipedia.org/wiki/"):
            continue
        if not excerpt.strip():
            continue
        sources.append({
            "provider": "Wikipedia en español",
            "title": title[:200],
            "url": link,
            "excerpt": excerpt.strip()[:MAX_EXCERPT],
            "evidence_level": "secondary_lead_only",
            "license_note": "Resumen textual de Wikipedia: comprobar atribución y CC BY-SA antes de reutilizar.",
        })
    return sources


def research_topic(topic, collector=fetch_wikipedia_candidates):
    dossier = prepare_topic(topic)
    if dossier["can_render"]:
        dossier["research"] = {
            "status": "already_curated",
            "note": "El tema pertenece al catálogo existente; esta ejecución no revisa sus fuentes.",
        }
        return dossier
    try:
        sources = collector(dossier["topic"])
        if not isinstance(sources, list):
            raise ValueError("Fuentes inválidas.")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        dossier["research"] = {
            "status": "unavailable",
            "error_type": type(exc).__name__,
            "note": "Fallo de consulta; sin afirmaciones científicas generadas.",
        }
        return dossier
    dossier["sources"] = sources
    dossier["research"] = {
        "status": "leads_found_not_verified" if sources else "no_leads",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Los extractos solo son pistas de investigación. Faltan fuentes científicas "
            "independientes, evaluación editorial, guion, visuales y revisión de licencias."
        ),
        "verified_scientific_sources": 0,
    }
    # No source collection can silently turn an unknown topic into a renderable video.
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
