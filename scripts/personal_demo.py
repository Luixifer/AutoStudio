"""Real AutoStudio Alex demo using eight existing ORIGINAL aurora images.

The text is an editorial demonstration, NOT independently reviewed science.
Assets are authored in this repository; no external photo licensing or AI API.
"""
import argparse
import json
import shutil
from pathlib import Path

from scripts.neural_narration import NeuralNarrator
from scripts.personal_studio import sha256_file

ROOT=Path(__file__).resolve().parents[1]
AURORA_LINES=[
    ("¿Y si el cielo nocturno empezara a bailar sobre nuestras cabezas?","zoom_in"),
    ("Las auroras parecen magia, pero su origen está en el Sol.","pan_right"),
    ("Su actividad impulsa partículas cargadas que viajan a través del espacio.","focus"),
    ("El campo magnético terrestre desvía muchas de ellas hacia los polos.","pan_left"),
    ("Allí, algunas interactúan con los gases de nuestra atmósfera.","zoom_in"),
    ("Esa energía termina transformándose en destellos de luz de distintos colores.","zoom_out"),
    ("El oxígeno puede producir luces verdes y rojas; el nitrógeno, tonos azulados y violetas.","pan_right"),
    ("Y así, una noche cualquiera, el cielo se convierte en un espectáculo cósmico.","zoom_out"),
]


def create_demo(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    voice=NeuralNarrator()
    scenes=[]
    for i,(text,movement) in enumerate(AURORA_LINES,1):
        source=ROOT/f"assets/science_v04/auroras/auroras_{i:02}.jpg"
        target=out/f"aurora_{i:02}.jpg"
        if not source.is_file():raise RuntimeError("Missing original illustration.")
        shutil.copy2(source,target)
        wav=out/f"alex_{i:02}.wav"
        result=voice.synthesize(text,wav)
        if result["voice"]!="em_alex":raise RuntimeError("Expected Alex voice.")
        scenes.append({
            "heading":"¿POR QUÉ BRILLAN LAS AURORAS?",
            "image":target.name,"audio":wav.name,
            "narration":text,
            "timed_words":result["words"],
            "source_type":"illustration",
            "rights":{"license":"own_creation","credit":"Ilustración original AutoStudio"},
            "camera":{"movement":movement,"zoom":1.08,"target":[.5,.5]},
        })
    bundle={"schema":2,"title":"¿Por qué brilla el cielo? El misterio de las auroras",
            "format":"short","language":"es","editorial_approved":False,
            "youtube":{"enabled":False},"scenes":scenes}
    project_path=out/"auroras-personal.json"
    project_path.write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return project_path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    from scripts.personal_editor import produce
    config=create_demo(args.out/"input")
    report=produce(config,args.out/"render")
    print("AURORA_DEMO_FORMAT",report["size"])
    print("AURORA_DEMO_DURATION",report["seconds"])
    print("AURORA_DEMO_SCENES",len(report["shots"]))
    print("AURORA_DEMO_SHA256",report["sha256"])
    print("AURORA_DEMO_TECHNICAL_PASS",report["technical_passed"])
    if not report["technical_passed"] or report["ready_to_publish"]:
        raise RuntimeError("Cannot approve broken or unreviewed video.")

if __name__=="__main__":main()
