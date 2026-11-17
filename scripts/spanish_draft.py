"""Conservative Spanish *editorial* draft from traceable NASA excerpts.

This is a narrow, deterministic prototype, NOT an open-ended writing model:
templates are only emitted when explicit English evidence cues are present.
No scientific fact is ever marked verified without editorial checking.
"""
import re
from scripts.source_quality import black_hole_question
from scripts.external_sources import NASA_BLACK_HOLE_PAGES

# A sentence is emitted only if all evidence groups match one same NASA excerpt.
# Order is intended narrative flow, not chronology of physical events.
RULES = (
    ("Apertura", (("event horizon",), ("black hole",)),
     "Los agujeros negros tienen una frontera decisiva: el horizonte de sucesos. ¿Qué podemos afirmar sobre lo que hay más allá?"),
    ("Frontera", (("event horizon",), ("boundary", "point of no return")),
     "El horizonte de sucesos delimita una región de la que no podemos recibir señales como desde el espacio exterior."),
    ("Luz", (("black hole",), ("light",), ("cannot escape", "can't escape", "no light escapes")),
     "La luz también está sometida a esta frontera gravitatoria: desde el interior no puede escapar hacia fuera."),
    ("Alrededores", (("accretion disk",), ("gas", "matter", "light")),
     "Alrededor de algunos agujeros negros, el material forma un disco de acreción. Esto ocurre fuera de la frontera, no en su interior."),
    ("Límites", (("singularity",), ("relativity", "theory", "predicts", "physics")),
     "Las teorías físicas permiten describir parte del fenómeno, pero no tenemos una imagen observada directamente del centro de un agujero negro."),
)

def _words(text):
    return " ".join(str(text).casefold().replace("’", "'").split())

def _has_evidence(excerpt, groups):
    low=_words(excerpt)
    return all(any(re.search(r"(?<![a-z])"+re.escape(token)+r"(?![a-z])",low) for token in alternatives)
               for alternatives in groups)

def draft_spanish_narration(topic, evidence):
    """Return max 5 short original Spanish paragraphs with provenance and blockers."""
    if not black_hole_question(topic):
        return {
            "status": "unsupported_subject", "scenes":[],
            "approved":False,"can_render":False,
            "note":"Redactor experimental limitado a preguntas sobre agujeros negros.",
        }
    passages=evidence.get("passages",[]) if isinstance(evidence,dict) else []
    trusted_urls=frozenset(url for _,url in NASA_BLACK_HOLE_PAGES)
    if not isinstance(passages,list):
        raise ValueError("Pasajes inválidos.")
    scenes=[]
    for role, cue_groups, narration in RULES:
        matched=None
        for source in passages:
            if not isinstance(source,dict) or not source.get("content_fetched"):
                continue
            excerpt=source.get("excerpt_original_en","")
            link=source.get("source_url","")
            if not isinstance(excerpt,str) or link not in trusted_urls:
                continue
            if _has_evidence(excerpt,cue_groups):
                matched=source
                break
        if matched:
            scenes.append({
                "role": role,
                "narration_draft_es": narration,
                "reference_url": matched["source_url"],
                "reference_title": matched.get("source_title","NASA Science"),
                "source_excerpt_en": matched["excerpt_original_en"][:240],
                "approval": "human_scientific_review_required",
                "visual_asset":None,
            })
    return {
        "status":"partial_source_linked_draft" if scenes else "insufficient_evidence",
        "scenes":scenes,
        "approved":False,"can_render":False,"youtube_enabled":False,
        "word_count":sum(len(scene["narration_draft_es"].split()) for scene in scenes),
        "note":(
            "Borrador original en español compuesto mediante plantillas conservadoras. "
            "No es IA generativa libre ni está científicamente verificado; "
            "cada escena necesita revisión de hechos y recursos visuales."
        ),
    }
