"""Create a source-linked editorial storyboard brief; never a publishable script.

Inputs: a research dossier. Outputs: scene briefs with unanswered questions,
citations to candidate sources, and explicit missing visual/narration assets.
No paid APIs or arbitrary model-generated factual assertions.
"""
import argparse
import json
from pathlib import Path

from scripts.topic_research import research_topic

MAX_SCENES = 8


def draft_storyboard(dossier):
    if not isinstance(dossier, dict) or not dossier.get("topic"):
        raise ValueError("Expediente de investigación inválido.")
    topic = dossier["topic"]
    if dossier.get("can_render"):
        return {
            "schema": 1, "topic": topic, "status": "already_curated",
            "can_render": True, "scenes": [],
            "note": "El tema usa el guion publicado; no se sustituye por un borrador.",
        }
    leads = dossier.get("sources", [])
    if not isinstance(leads, list):
        raise ValueError("El expediente debe incluir una lista de referencias.")
    scenes = []
    scene_templates = [
        ("Apertura", "¿Qué pregunta concreta despierta curiosidad sobre «{topic}» sin sugerir un hecho no probado?"),
        ("Contexto", "¿Qué es «{topic}» según fuentes fiables, y qué conceptos necesitan definición?"),
        ("Mecanismo", "¿Cómo funciona o por qué sucede? Distinguir observación de hipótesis."),
        ("Evidencia", "¿Qué observaciones, experimentos o documentos sustentan cada afirmación?"),
        ("Matiz", "¿Qué no sabemos todavía y qué interpretaciones deben evitarse?"),
        ("Conclusión", "¿Cuál es la explicación más útil que permiten las fuentes confirmadas?"),
    ]
    references = [
        {"title": item.get("title", ""), "url": item.get("url", ""),
         "evidence_level": item.get("evidence_level", "unverified")}
        for item in leads if isinstance(item, dict) and isinstance(item.get("url"), str)
    ]
    for i, (role, question) in enumerate(scene_templates[:MAX_SCENES], 1):
        scenes.append({
            "scene_id": f"draft-{i:02}",
            "role": role,
            "editorial_question": question.format(topic=topic),
            "candidate_references": references,
            "verified_claims": [],
            "narration": None,
            "visual_brief": None,
            "visual_asset": None,
            "approved": False,
        })
    return {
        "schema": 1,
        "topic": topic,
        "status": "editorial_draft",
        "can_render": False,
        "human_review_required": True,
        "source_count": len(references),
        "sources_verified": 0,
        "scenes": scenes,
        "youtube_enabled": False,
        "paid_api_allowed": False,
        "note": "Preguntas de planificación, NO guion narrable. Requiere fuentes independientes, afirmaciones verificadas y recursos visuales.",
    }


def main():
    parser = argparse.ArgumentParser(description="Prepara un storyboard editorial sin inventar ciencia.")
    parser.add_argument("topic")
    parser.add_argument("--out", help="Archivo JSON opcional")
    args = parser.parse_args()
    result = draft_storyboard(research_topic(args.topic))
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
