"""One-command path: storyboard + original image files -> Alex voice -> MP4.

No research claims, image generation, YouTube posting or paid providers.
User (or another pipeline) supplies original text and appropriately licensed art.
"""
import argparse
import json
import shutil
from pathlib import Path

from scripts.personal_studio import ALLOWED_IMAGE,PROFILES,secure_file
from scripts.personal_camera import suggest_focal_point,visual_similarity_warnings

MOVEMENT_SEQUENCE=("zoom_in","pan_right","focus","zoom_out","pan_left",
                   "zoom_in","pan_right","zoom_out","focus","pan_left")

def camera_for(index,scene,image_path=None):
    override=scene.get("camera")
    if override is not None:
        if not isinstance(override,dict):raise ValueError("Movimiento personalizado inválido.")
        return override
    focal=scene.get("focal_point")
    if focal is None and image_path is not None:
        focal=suggest_focal_point(image_path)["target"]
    if focal is None:focal=[.5,.5]
    return {"movement":MOVEMENT_SEQUENCE[index%len(MOVEMENT_SEQUENCE)],
            "zoom":1.09,"target":focal}


def prepare(source_json,out,narrator=None):
    source=Path(source_json);out=Path(out)
    if not source.is_file() or source.stat().st_size>500000:
        raise ValueError("Falta storyboard o es demasiado grande.")
    storyboard=json.loads(source.read_text(encoding="utf-8"))
    if storyboard.get("schema")!=3 or storyboard.get("format") not in PROFILES:
        raise ValueError("El storyboard debe ser schema 3 con formato válido.")
    if storyboard["format"]=="lab":
        raise ValueError("LAB solo se permite en pruebas internas.")
    if storyboard.get("language")!="es" or storyboard.get("youtube",{}).get("enabled") is not False:
        raise ValueError("Solo español y YouTube desactivado.")
    scenes=storyboard.get("scenes",[])
    profile=PROFILES[storyboard["format"]]
    if not isinstance(scenes,list) or not profile["min_scenes"]<=len(scenes)<=profile["max_scenes"]:
        raise ValueError("Número de escenas incorrecto.")
    if narrator is None:
        from scripts.neural_narration import NeuralNarrator
        narrator=NeuralNarrator()
    out.mkdir(parents=True,exist_ok=True)
    result=[]
    source_images=[]
    camera_audits=[]
    seen=set()
    for i,scene in enumerate(scenes):
        if not isinstance(scene,dict):raise ValueError("Escena inválida.")
        line=scene.get("narration","")
        if not isinstance(line,str) or not 12<=len(line)<=600:
            raise ValueError("Narración demasiado corta o larga.")
        original=secure_file(source.parent,scene.get("image"),ALLOWED_IMAGE)
        from scripts.personal_studio import sha256_file
        checksum=sha256_file(original)
        if checksum in seen:raise ValueError("Fotografía o imagen repetida.")
        seen.add(checksum)
        source_images.append(original)
        if scene.get("focal_point") is None and scene.get("camera") is None:
            audit=suggest_focal_point(original)
        else:
            audit={"target":scene.get("focal_point",scene.get("camera",{}).get("target")),
                   "confidence":"user_supplied","method":"provided_target"}
        camera_audits.append({"scene":i+1,**audit})
        picture=out/f"image_{i+1:03}{original.suffix.lower()}"
        shutil.copy2(original,picture)
        wav=out/f"voice_{i+1:03}.wav"
        voice=narrator.synthesize(line,wav)
        if voice.get("voice")!="em_alex":
            raise ValueError("La voz seleccionada Álex no se ha utilizado.")
        result.append({
            "heading":scene.get("heading",storyboard.get("title","")),
            "narration":line,"image":picture.name,"audio":wav.name,
            "timed_words":voice["words"],
            "rights":scene.get("rights",{}),
            "source_type":scene.get("source_type","illustration"),
            "camera":camera_for(i,scene,original),
        })
    complete={
        "schema":2,"title":storyboard.get("title"),
        "format":storyboard["format"],
        "language":"es",
        "editorial_approved":bool(storyboard.get("editorial_approved",False)),
        "youtube":{"enabled":False},
        "scenes":result,
        "camera_audits":camera_audits,
        "visual_similarity_warnings":visual_similarity_warnings(source_images),
    }
    path=out/"studio-ready.json"
    path.write_text(json.dumps(complete,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    # Ensure the actual audio, timed subtitles, imagery and declared rights
    # form a valid production before handing anything to FFmpeg.
    from scripts.personal_studio import validate_project
    validate_project(out,complete)
    return path


def main():
    p=argparse.ArgumentParser()
    p.add_argument("storyboard",type=Path)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--render",action="store_true")
    args=p.parse_args()
    result=prepare(args.storyboard,args.out/"input")
    if args.render:
        from scripts.personal_editor import produce
        report=produce(result,args.out/"render")
        print("STUDIO_RESULT",report["status"],report["video"])
    else:
        print("STUDIO_READY",result)

if __name__=="__main__":main()
