"""Free provenance-first source leads for AutoStudio science research.

Official NASA pages are curated links, not automatically extracted facts.
Crossref provides publication METADATA, not peer-review certification or
permission to reproduce article text. No API keys, models or media downloads.
"""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from scripts.source_quality import black_hole_question, clean

CROSSREF_URL = "https://api.crossref.org/works"
AGENT = "AutoStudio-Research/0.4 (educational; repository Luixifer/AutoStudio)"
MAX_RESPONSE = 350_000

# Exact, official pages selected for the black-hole question. No article
# content or scientific assertions are embedded in the output.
NASA_BLACK_HOLE_PAGES = (
    ("Anatomy of a Black Hole — NASA", "https://science.nasa.gov/universe/black-holes/anatomy/"),
    ("What Happens When Something Gets Too Close to a Black Hole? — NASA",
     "https://science.nasa.gov/universe/what-happens-when-something-gets-too-close-to-a-black-hole/"),
    ("New NASA Black Hole Visualization Takes Viewers Beyond the Brink",
     "https://science.nasa.gov/universe/black-holes/new-nasa-black-hole-visualization-takes-viewers-beyond-the-brink/"),
)

def agency_leads(topic):
    """Conservative exact domain/subject registry; not a universal NASA search."""
    if not black_hole_question(topic):
        return []
    return [{
        "provider": "NASA Science",
        "title": name,
        "url": url,
        "evidence_level": "institutional_page_lead_unreviewed",
        "content_fetched": False,
        "excerpt": "",
        "license_note": "No se han copiado contenidos. Verificar condiciones y exactitud antes de usarlos.",
    } for name, url in NASA_BLACK_HOLE_PAGES]


def crossref_query(topic):
    if black_hole_question(topic):
        return "black hole event horizon interior general relativity"
    return topic


def crossref_leads(topic, opener=urlopen):
    """Search scholarly metadata; be selective and fail closed on suspect titles."""
    params = urlencode({"query.title": crossref_query(topic), "rows": 8,
                        "select": "DOI,title,type,published,container-title"})
    req = Request(CROSSREF_URL+"?"+params,
                  headers={"User-Agent": AGENT, "Accept": "application/json"})
    with opener(req, timeout=12) as response:
        raw = response.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("Crossref ha devuelto demasiados datos.")
    data=json.loads(raw.decode("utf-8"))
    works=data.get("message",{}).get("items",[])
    if not isinstance(works,list):
        raise ValueError("Respuesta académica inválida.")
    items=[]
    for item in works:
        if not isinstance(item,dict):
            continue
        titles=item.get("title",[])
        title=titles[0] if isinstance(titles,list) and titles else None
        doi=item.get("DOI","")
        if not isinstance(title,str) or not isinstance(doi,str):
            continue
        if len(title)>300 or not re.fullmatch(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+",doi,re.I):
            continue
        norm=clean(title)
        if any(fragment in norm for fragment in ("stargate","fiction","white hole","agujero blanco")):
            continue
        if black_hole_question(topic) and not ("black hole" in norm or "event horizon" in norm):
            continue
        url="https://doi.org/"+doi
        items.append({
            "provider": "Crossref (metadatos bibliográficos)",
            "title": title,
            "url": url,
            "doi": doi,
            "evidence_level": "academic_metadata_lead_unreviewed",
            "content_fetched": False,
            "excerpt": "",
            "license_note": "Solo metadatos; no se ha leído ni verificado el artículo y no se ha comprobado su revisión por pares.",
        })
        if len(items)>=4:
            break
    return items


def external_leads(topic, crossref=crossref_leads):
    """NASA references always available for scoped topic; bibliographic API best effort."""
    leads=agency_leads(topic)
    try:
        return leads+crossref(topic), None
    except (HTTPError,URLError,TimeoutError,OSError,ValueError,json.JSONDecodeError) as exc:
        return leads, type(exc).__name__
