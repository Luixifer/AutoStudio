"""Offline voice-only export for the ten-scene personal KELT-9b Short.

No reliance on generated art in GitHub, uploads or voice APIs.
Exports one WAV per scene with SHA-256 and timing metadata for local editing.
"""
import argparse
import hashlib
import json
import wave
from pathlib import Path

SCENES=[
    ("El planeta más infernal","¿Te imaginas un planeta tan caliente que supera la temperatura de algunas estrellas?"),
    ("KELT nueve be","Se llama KELT nueve be. Es un gigante gaseoso, y parece salido del mismísimo infierno."),
    ("Un horno cósmico","En su cara iluminada, la temperatura ronda los cuatro mil trescientos grados Celsius."),
    ("Sin suelo de lava","No hay océanos de lava que pisar: es un mundo gigante hecho principalmente de gas."),
    ("Moléculas destruidas","El calor es tan brutal que puede separar las moléculas de hidrógeno en átomos."),
    ("Atmósfera en fuga","La radiación de su estrella es tan intensa que parte de su atmósfera escapa al espacio."),
    ("Un año imposible","Y aquí viene otra locura: su año dura poco menos de un día y medio terrestre."),
    ("Más allá del día","En su hemisferio nocturno, parte del hidrógeno puede volver a formar moléculas."),
    ("Demasiado cerca","KELT nueve be recibe miles de veces más energía estelar que nuestro propio planeta."),
    ("Un mundo extremo","Así es uno de los planetas más infernales que conocemos. ¿Te atreverías a acercarte?"),
]

def produce(directory):
    from scripts.neural_narration import NeuralNarrator
    narrator=NeuralNarrator()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    outputs=[]
    for idx,(title,line) in enumerate(SCENES,1):
        path=directory/f"voz-alex-{idx:02}.wav"
        synthesis=narrator.synthesize(line,path)
        if synthesis["voice"]!="em_alex":raise RuntimeError("Expected chosen Alex voice.")
        with wave.open(str(path),"rb") as w:
            duration=w.getnframes()/w.getframerate()
        if not 1.5<=duration<=20:raise RuntimeError("Abnormal scene duration.")
        outputs.append({
            "scene":idx,"title":title,"narration":line,"file":path.name,
            "seconds":round(duration,3),"words":synthesis["words"],
            "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "voice":"em_alex","speed":synthesis["speed"],
            "human_reviewed":False,
        })
        print("KELT9B_ALEX_SCENE",idx,round(duration,3))
    report={"status":"unreviewed_voice_only","language":"es","voice":"em_alex",
            "source":"KELT-9b original ten-scene script","scene_count":len(outputs),
            "total_voice_seconds":round(sum(s["seconds"] for s in outputs),3),
            "scientifically_approved":False,"youtube_enabled":False,
            "scenes":outputs}
    (directory/"alex-scene-manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    report=produce(args.out)
    assert len(report["scenes"])==10
    print("KELT9B_ALEX_TOTAL_SECONDS",report["total_voice_seconds"])

if __name__=="__main__":main()
