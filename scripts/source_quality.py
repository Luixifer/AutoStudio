"""Conservative guardrails for scientific source discovery.

These are negative filters, NOT independent fact checking or an open-domain
scientific classifier. For astrophysical black-hole queries, reject fiction,
white holes and unrelated astronomy pages even if a search engine ranks them.
"""
import re
import unicodedata

FICTION_SIGNALS = (
    "stargate", "star trek", "star wars", "ciencia ficcion",
    "videojuego", "serie de television", "pelicula", "ficcion",
    "comic", "anime", "universo ficticio", "franquicia",
)


def clean(text):
    value=unicodedata.normalize("NFKD",str(text).casefold())
    return "".join(c for c in value if not unicodedata.combining(c))


def black_hole_question(topic):
    text=clean(topic)
    return bool(re.search(r"\bagujeros? negros?\b", text))


def valid_science_lead(topic, title, excerpt):
    """Fail closed for a known dangerous confusion, not a global authority score."""
    if not isinstance(title,str) or not isinstance(excerpt,str):
        return False
    if not black_hole_question(topic):
        return True
    name=clean(title).replace("_"," ")
    body=clean(excerpt[:1500])
    if any(signal in name for signal in FICTION_SIGNALS):
        return False
    if "agujero blanco" in name or "white hole" in name:
        return False
    # A genuine astrophysics article must focus on the relevant object,
    # phenomenon or theoretical treatment in its *title* AND text.
    title_ok=any(phrase in name for phrase in (
        "agujero negro", "horizonte de sucesos",
        "singularidad gravitacional", "radiacion de hawking",
        "relatividad general", "espaguetificacion",
    ))
    body_ok=("agujero negro" in body or "agujeros negros" in body)
    return title_ok and body_ok
