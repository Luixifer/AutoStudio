"""Editorial visual director for original-image science videos.

Produces an actionable, *unverified* scene-by-scene visual brief and filenames.
No external APIs, no image generation, no claims of factual verification.
The draft is for a human/image generator to work from, not a source of science.
"""
import json
import re
from pathlib import Path

LENSES=(
    ("gran plano general","composición épica, escala y atmósfera"),
    ("plano medio","sujeto dominante con detalles del entorno"),
    ("primer plano","detalles espectaculares del fenómeno"),
    ("plano de perspectiva","profundidad visual, capas y parallax natural"),
    ("plano conceptual","comparación visual clara sin números inventados"),
    ("plano detalle","texturas físicas y contrastes de iluminación"),
)
STYLE=("visualización cinematográfica científica, ilustración original, "
       "composición vertical 9:16, colores equilibrados, iluminación volumétrica "
       "sutil, profundidad, formas legibles, alto nivel de detalle, sin texto")
NEGATIVE=("texto, rótulos, marcas de agua, logotipos, rostros identificables, "
          "manos sobrantes, elementos duplicados, símbolos científicos falsos, "
          "números dibujados, interfaz, collage, cuadrículas, bordes, "
          "captura de pantalla")
TOPICS=(
    (("planeta","exoplaneta","órbita","orbita"),"cuerpo planetario y su entorno espacial"),
    (("estrella","sol","solar","radiación","radiacion"),"estrella luminosa y entorno espacial"),
    (("atmósfera","atmosfera","gas","hidrógeno","hidrogeno"),"capas de gas y atmósfera representadas artísticamente"),
    (("océano","oceano","agua","mar"),"agua, reflejos e inmensidad natural"),
    (("adn","célula","celula","molécula","molecula"),"estructura biológica representada a escala conceptual"),
    (("volcán","volcan","lava","magma"),"actividad volcánica y roca incandescente"),
    (("hielo","glaciar","nieve"),"hielo y contraste de temperaturas"),
)

def visual_subject(narration):
    low=narration.casefold()
    for terms,description in TOPICS:
        if any(re.search(r"(?<!\w)"+re.escape(word)+r"(?!\w)",low) for word in terms):
            return description
    return "fenómeno científico descrito en la narración, sin añadir detalles no confirmados"

def make_visual_briefs(storyboard):
    scenes=storyboard.get("scenes",[])
    title=storyboard.get("title","")
    if not isinstance(title,str) or not title.strip() or not isinstance(scenes,list) or not 2<=len(scenes)<=180:
        raise ValueError("Storyboard sin título o escenas suficientes.")
    results=[]
    for i,scene in enumerate(scenes):
        if not isinstance(scene,dict) or not isinstance(scene.get("narration"),str):
            raise ValueError("Escena sin narración.")
        narration=scene["narration"].strip()
        if not narration or len(narration)>600:
            raise ValueError("Narración inválida para dirección visual.")
        lens,hint=LENSES[i%len(LENSES)]
        subject=visual_subject(narration)
        composition=("sujeto principal bien separado del fondo, zona superior "
                     "e inferior despejada para títulos y subtítulos independientes")
        prompt=(f"{STYLE}. {lens.capitalize()}: {subject}; {hint}; {composition}. "
                f"Interpretar visualmente esta idea sin escribir sus palabras ni inventar hechos: {narration}")
        results.append({
            "scene":i+1,
            "narration":narration,
            "suggested_filename":f"imagen-{i+1:02}.jpg",
            "shot_type":lens,
            "suggested_subject":subject,
            "image_prompt":prompt,
            "avoid":NEGATIVE,
            "license_required":"original o con derechos verificados",
            "scientific_facts_verified":False,
            "image_generated":False,
        })
    return {"schema":1,"title":title,"visual_style":STYLE,
            "warnings":["Borrador artístico automático, no revisión científica.",
                        "El contenido visual debe ser coherente con el guion y no inventar datos.",
                        "La generación de imágenes no se realiza en este paso."],
            "scenes":results}

def export_briefs(storyboard_json, output_dir):
    source=Path(storyboard_json)
    if not source.is_file() or source.stat().st_size>500000:
        raise ValueError("No se encuentra el storyboard o es excesivo.")
    doc=json.loads(source.read_text(encoding="utf-8"))
    brief=make_visual_briefs(doc)
    out=Path(output_dir)
    out.mkdir(parents=True,exist_ok=True)
    (out/"direccion-visual.json").write_text(
        json.dumps(brief,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines=[f"# Dirección visual · {brief['title']}","",
           "Guía para crear o mejorar las imágenes originales de cada plano.",
           "No genera imágenes ni certifica hechos científicos.",""]
    for scene in brief["scenes"]:
        lines.extend([f"## {scene['scene']:02}. {scene['suggested_filename']}",
            f"**Narración:** {scene['narration']}",
            f"**Plano:** {scene['shot_type']}",
            f"**Prompt:** {scene['image_prompt']}",
            f"**Evitar:** {scene['avoid']}",""])
    md=out/"prompts-imagenes.md"
    md.write_text("\n".join(lines),encoding="utf-8")
    return brief

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("storyboard",type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    result=export_briefs(args.storyboard,args.out)
    print("VISUAL_BRIEFS",len(result["scenes"]),str(args.out))

if __name__=="__main__":
    main()
