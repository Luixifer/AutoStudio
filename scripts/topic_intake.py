"""Preparación segura de temas libres: no genera ciencia inventada ni promete MP4."""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalize_topic(topic):
    if not isinstance(topic, str):
        raise ValueError("El tema debe ser texto.")
    # Reject control characters before whitespace normalisation: otherwise
    # newlines and tabs silently disappear and bypass the validation contract.
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in topic):
        raise ValueError("El tema no puede contener caracteres de control.")
    value = " ".join(topic.split())
    if not 3 <= len(value) <= 160:
        raise ValueError("El tema debe tener entre 3 y 160 caracteres.")
    return value


def topic_key(topic):
    value = unicodedata.normalize("NFKD", normalize_topic(topic)).casefold()
    value = "".join(c for c in value if not unicodedata.combining(c))
    slug = re.sub(r"[^a-z0-9]+", "-", value).strip("-")[:52].strip("-")
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{slug or 'tema'}-{digest}"


def prepare_topic(topic, catalog_path=None):
    value = normalize_topic(topic)
    path = Path(catalog_path) if catalog_path else ROOT / "content/catalog.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    normalized = unicodedata.normalize("NFKD", value).casefold()
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    matches = []
    for item in catalog["topics"]:
        if not item.get("published", False):
            continue
        aliases = [item["id"], item["name"], *item.get("examples", [])]
        for alias in aliases:
            alias = "".join(c for c in unicodedata.normalize("NFKD", alias).casefold()
                            if not unicodedata.combining(c))
            if alias == normalized:
                matches.append(item)
                break
    if len(matches) > 1:
        raise ValueError("Tema ambiguo: elige una entrada precisa.")
    if matches:
        return {
            "schema": 1, "topic": value, "key": topic_key(value),
            "status": "published_catalog", "topic_id": matches[0]["id"],
            "can_render": True, "paid_api_allowed": False, "youtube_enabled": False,
        }
    return {
        "schema": 1, "topic": value, "key": topic_key(value),
        "status": "research_required", "topic_id": None,
        "can_render": False, "paid_api_allowed": False, "youtube_enabled": False,
        "requirements": [
            "Localizar al menos dos fuentes científicas o históricas verificables.",
            "Redactar y revisar un guion propio con afirmaciones trazables a las fuentes.",
            "Crear un storyboard con escenas y narración correspondientes al tema.",
            "Producir o licenciar recursos visuales para cada escena; registrar atribuciones.",
            "Validar narración, vídeo y subtítulos antes de habilitar el render.",
        ],
        "sources": [],
        "scenes": [],
        "note": "Solicitud preparada; NO se han generado guion, imágenes ni MP4.",
    }


def main():
    parser = argparse.ArgumentParser(description="Prepara expediente de tema libre sin inferencia pagada.")
    parser.add_argument("topic", help="Tema solicitado")
    parser.add_argument("--out", help="Ruta opcional donde guardar el expediente JSON")
    args = parser.parse_args()
    result = prepare_topic(args.topic)
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")


if __name__ == "__main__":
    main()
