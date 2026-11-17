"""Three explicit, authored personal science topics; never claim arbitrary AI video.

The original illustrations already exist in AutoStudio. Every narration is
editorial draft needing fact checking before public upload.
"""
import argparse
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOPICS={
"auroras":{
    "title":"Auroras: por qué el cielo parece cobrar vida",
    "keywords":["aurora","auroras","luces del norte"],
    "scenes":[
      "¿Y si una noche el cielo empezara a bailar sobre nuestras cabezas?",
      "Las auroras parecen magia, pero su origen está en la actividad del Sol.",
      "El viento solar transporta partículas cargadas por el espacio que rodea nuestro planeta.",
      "El campo magnético terrestre ayuda a guiarlas hacia las regiones polares.",
      "Allí algunas partículas transfieren energía a los gases de la atmósfera.",
      "Cuando esa energía se libera, el cielo puede iluminarse con colores extraordinarios.",
      "El oxígeno contribuye a los tonos verdes y rojos; el nitrógeno, a tonos azules y violetas.",
      "Es una auténtica danza de luz, nacida de la relación entre la Tierra y el Sol."
    ]
},
"dna":{
    "title":"ADN: el lenguaje invisible de la vida",
    "keywords":["adn","dna","genetica","genética","genes"],
    "scenes":[
      "Dentro de nuestras células existe una molécula que guarda instrucciones increíbles.",
      "Se llama ADN, y contiene información hereditaria utilizada por los seres vivos.",
      "Su forma característica recuerda a una escalera retorcida: la doble hélice.",
      "Sus peldaños están formados por parejas de bases químicas complementarias.",
      "El orden de esas bases puede codificar instrucciones para producir proteínas.",
      "Las células leen y utilizan esa información mediante procesos extraordinariamente precisos.",
      "Pequeñas diferencias en las secuencias pueden contribuir a nuestra diversidad biológica.",
      "Y todo ese lenguaje químico cabe, organizado, en el interior de nuestras células."
    ]
},
"volcanoes":{
    "title":"Volcanes: el poder oculto bajo nuestros pies",
    "keywords":["volcan","volcán","volcanes","erupcion","erupción","lava"],
    "scenes":[
      "Bajo nuestros pies se esconde una fuerza capaz de transformar paisajes enteros.",
      "Los volcanes permiten que material fundido del interior de la Tierra alcance la superficie.",
      "Bajo tierra lo llamamos magma; cuando sale al exterior, recibe el nombre de lava.",
      "Algunas erupciones avanzan con coladas de lava; otras expulsan ceniza y gases.",
      "La presión y la composición del magma influyen en cómo se desarrolla una erupción.",
      "Cada volcán tiene su historia, y no todos estallan de la misma manera.",
      "Aunque pueden resultar peligrosos, también construyen nuevas rocas, montañas e islas.",
      "Son una muestra espectacular de que nuestro planeta sigue geológicamente activo."
    ]
}
}

def resolve_topic(query):
    if not isinstance(query,str) or not query.strip() or len(query)>140:
        raise ValueError("Tema vacío o demasiado largo.")
    q=query.casefold()
    matches=[key for key,entry in TOPICS.items()
             if any(keyword in q for keyword in entry["keywords"])]
    if len(matches)!=1:
        raise ValueError("Tema todavía no soportado. Disponibles: auroras, ADN, volcanes.")
    return matches[0]


def create_bundle(topic,output):
    key=resolve_topic(topic)
    entry=TOPICS[key]
    out=Path(output)
    out.mkdir(parents=True,exist_ok=True)
    scenes=[]
    for i,text in enumerate(entry["scenes"],1):
        filename=f"{key}_{i:02}.jpg"
        source=ROOT/"assets"/"science_v04"/key/filename
        if not source.is_file():raise ValueError("Falta la ilustración original: "+filename)
        destination=out/filename
        shutil.copy2(source,destination)
        scenes.append({
            "heading":entry["title"],
            "image":filename,
            "narration":text,
            "source_type":"illustration",
            "rights":{"license":"own_creation","credit":"AutoStudio: ilustración original Blender"},
        })
    board={"schema":3,"title":entry["title"],
           "format":"short","language":"es","youtube":{"enabled":False},
           "editorial_approved":False,
           "catalog_topic_id":key,
           "note":"Guion original del catálogo; no validado por revisión científica humana.",
           "scenes":scenes}
    path=out/"storyboard.json"
    path.write_text(json.dumps(board,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return path


def main():
    p=argparse.ArgumentParser()
    p.add_argument("topic",help="Auroras, ADN o volcanes")
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--render",action="store_true")
    args=p.parse_args()
    board=create_bundle(args.topic,args.out/"storyboard")
    print("CATALOG_STORYBOARD",board)
    if args.render:
        from scripts.personal_prepare import prepare
        from scripts.personal_editor import produce
        ready=prepare(board,args.out/"prepared")
        report=produce(ready,args.out/"render")
        print("CATALOG_REAL_VIDEO",report["video"],report["sha256"],report["status"])

if __name__=="__main__":main()
