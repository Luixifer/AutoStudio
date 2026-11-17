"""Select source-attributed excerpts relevant to the *question*, not merely the topic.

Rule-based filter, not semantic understanding or scientific verification.
Exact Wikipedia quotes are only editorial candidates, never original scripts.
"""
import re
import unicodedata
from urllib.parse import urlsplit

MAX_CANDIDATES = 6
MAX_QUOTE_CHARS = 190
MIN_QUOTE_CHARS = 45
CC_LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/deed.es"
STOP = frozenset("""
a al algo ante bajo como con contra cual cuando de del desde donde dos el ella ellas ellos
en entre era es esta estas este estos fue ha hay la las le lo los mas mi muy no o para
pero por porque que quien se ser si sin sobre su sus tan te tiene tu un una unas uno unos
y ya qué cómo cuál cuándo dónde dentro ocurre ocurriria pasa pasar que significa
""".split())
# Scope-aware intent cues. These are not scientific assertions.
INTENTS = (
    (("dentro", "interior", "adentro"), ("interior", "dentro", "singularidad", "horizonte", "caer", "caida", "atravesar", "cruzar", "espaciotiempo", "espacio-tiempo")),
    (("formar", "forma", "formacion", "nace", "origen"), ("formar", "formacion", "colapso", "nacer", "origen", "crear")),
    (("desaparecer", "desaparece", "desaparicion"), ("desaparecer", "desaparicion", "perder", "consecuencia", "ausencia")),
)


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFKD", str(text).casefold())
                   if not unicodedata.combining(c))


def tokens(text):
    return [t for t in re.findall(r"[a-z0-9]+", normalize(text)) if len(t) > 2 and t not in STOP]


def stem(word):
    # Conservative Spanish plural handling, not an NLP lemmatizer.
    if len(word) > 6 and word.endswith("es"):
        return word[:-2]
    if len(word) > 5 and word.endswith("s"):
        return word[:-1]
    return word


def _sentences(excerpt):
    if not isinstance(excerpt, str):
        return []
    clean = " ".join(excerpt.replace("\n", " ").split())
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑÜ¿¡0-9])", clean)
    return [p for p in parts if p.endswith((".", "?", "!"))]


def _eligible(sentence):
    if not MIN_QUOTE_CHARS <= len(sentence) <= MAX_QUOTE_CHARS:
        return False
    if any(ch in sentence for ch in "{}[]<>|"):
        return False
    return 8 <= len(sentence.split()) <= 32 and not sentence.startswith(("Véase", "Referencias", "Categoría"))


def relevance(question, sentence):
    """Score lexical topicality + a separate question-intent gate.

    A related object ('black hole') is not sufficient evidence that a phrase
    answers 'inside a black hole'. Fail closed on absent intent terms.
    """
    q = set(map(stem, tokens(question)))
    s = set(map(stem, tokens(sentence)))
    if not q or not s:
        return None
    topical = q & s
    if not topical:
        return None
    normalized_q = set(tokens(question))
    normalized_s = normalize(sentence)
    required = []
    for triggers, cues in INTENTS:
        if normalized_q.intersection(triggers):
            required.extend(cues)
    if required and not any(cue in normalized_s for cue in required):
        return None
    # Distinguish core entity match + question-angle relevance.
    return len(topical) * 10 + (6 if required else 0)


def _wiki_url(url):
    if not isinstance(url, str):
        return False
    parsed = urlsplit(url)
    return (parsed.scheme == "https" and parsed.netloc == "es.wikipedia.org"
            and parsed.path.startswith("/wiki/") and not parsed.username
            and not parsed.password and not parsed.port)


def narration_candidates(dossier, max_candidates=MAX_CANDIDATES):
    if not isinstance(dossier, dict):
        raise ValueError("Expediente inválido.")
    if dossier.get("can_render"):
        return {"status": "existing_catalog", "candidates": [], "approved": False}
    leads = dossier.get("sources", [])
    if not isinstance(leads, list):
        raise ValueError("Referencias inválidas.")
    question = dossier.get("topic", "")
    max_candidates = max(0, min(MAX_CANDIDATES, int(max_candidates)))
    ranked = []
    for source in leads[:3]:
        if not isinstance(source, dict) or source.get("evidence_level") != "secondary_lead_only":
            continue
        if not _wiki_url(source.get("url")):
            continue
        for sentence in _sentences(source.get("excerpt")):
            if not _eligible(sentence):
                continue
            score = relevance(question, sentence)
            if score is not None:
                ranked.append((score, source, sentence))
    ranked.sort(key=lambda item: -item[0])
    candidates = []
    seen = set()
    for score, source, sentence in ranked:
        key = normalize(sentence)
        if key in seen:
            continue
        seen.add(key)
        candidates.append({
            "scene_id": f"draft-{len(candidates)+1:02}",
            "source_excerpt_exact": sentence,
            "origin": "extractive_quote_wikipedia_es",
            "source_title": source.get("title", ""),
            "source_url": source["url"],
            "relevance_score_heuristic": score,
            "license": "CC BY-SA 4.0 (comprobar licencia específica de la página)",
            "license_url": CC_LICENSE,
            "approved": False,
            "factual_verification": "pending_independent_source",
            "narration_ready": False,
        })
        if len(candidates) >= max_candidates:
            break
    return {
        "status": "extractive_candidates_unverified" if candidates else "no_relevant_evidence",
        "candidates": candidates,
        "approved": False, "can_render": False,
        "note": (
            "Filtrado heurístico por tema y pregunta. La ausencia de resultados es válida. "
            "Las citas atribuidas no son guion original ni hechos contrastados."
        ),
    }
