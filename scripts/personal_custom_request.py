"""Validate public GitHub request assets before invoking the pinned video engine.

The GitHub Actions input is a UUID only. User JSON, text and images are DATA,
never shell code. Public repository history is persistent even after deletion.
"""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

REQUEST_ID=re.compile(r"[a-f0-9]{32}\Z")
SHA=re.compile(r"[a-f0-9]{64}\Z")
MAX_IMAGE_BYTES=1400000
MAX_JSON_BYTES=36000

def load_request(root,request_id,out):
    from PIL import Image,ImageOps
    if not REQUEST_ID.fullmatch(request_id):
        raise ValueError("Identificador UUID inválido.")
    root=Path(root).resolve(strict=True)
    request=root/"requests"/request_id
    if not request.is_dir() or request.is_symlink():
        raise ValueError("La solicitud no existe.")
    file=request/"storyboard.json"
    if file.is_symlink() or file.stat().st_size>MAX_JSON_BYTES:
        raise ValueError("El manifiesto no es válido.")
    document=json.loads(file.read_text(encoding="utf-8"))
    if document.get("request_id")!=request_id or document.get("schema")!=3:
        raise ValueError("La solicitud no corresponde a este render.")
    if document.get("format")!="short" or document.get("language")!="es":
        raise ValueError("Solo se admite Short en español en este laboratorio.")
    if document.get("youtube",{}).get("enabled") is not False:
        raise ValueError("YouTube debe estar desactivado.")
    title=document.get("title")
    if not isinstance(title,str) or not 8<=len(title)<=110:
        raise ValueError("Título inválido.")
    scenes=document.get("scenes")
    if not isinstance(scenes,list) or not 2<=len(scenes)<=12:
        raise ValueError("Se requieren entre 2 y 12 escenas.")
    if len(set(s["image"] for s in scenes if isinstance(s,dict)))!=len(scenes):
        raise ValueError("Las imágenes deben ser distintas.")
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    source_shas=[]
    for i,scene in enumerate(scenes,1):
        if not isinstance(scene,dict):
            raise ValueError("Escena no válida.")
        wanted=f"imagen-{i:02}.jpg"
        if scene.get("image")!=wanted or scene.get("source_type")!="illustration":
            raise ValueError("Nombre de imagen inesperado.")
        phrase=scene.get("narration")
        if not isinstance(phrase,str) or not 16<=len(phrase)<=450 or any(ord(c)<32 for c in phrase):
            raise ValueError("El guion contiene escenas inválidas.")
        rights=scene.get("rights")
        if rights!={"license":"original_user"}:
            raise ValueError("La imagen debe estar autorizada por su propietario.")
        expected=scene.get("image_sha256")
        if not isinstance(expected,str) or not SHA.fullmatch(expected):
            raise ValueError("Falta SHA-256 de una imagen.")
        image=request/wanted
        if image.is_symlink() or not image.is_file() or image.stat().st_size>MAX_IMAGE_BYTES:
            raise ValueError("Imagen ausente o excesiva.")
        digest=hashlib.sha256(image.read_bytes()).hexdigest()
        if digest!=expected:
            raise ValueError("La imagen no coincide con el envío.")
        with Image.open(image) as obj:
            obj.verify()
        with Image.open(image) as obj:
            if obj.format!="JPEG" or obj.width<400 or obj.height<500 or obj.width>4096 or obj.height>4096:
                raise ValueError("Imagen no compatible.")
        source_shas.append(digest)
        shutil.copy2(image,out/wanted)
    if len(set(source_shas))!=len(scenes):
        raise ValueError("No se permiten imágenes repetidas.")
    # This copy is clean and does not embed auth tokens, repository metadata
    # or user-submitted extra fields.
    safe={
        "schema":3,"title":title,"format":"short",
        "language":"es","editorial_approved":False,
        "youtube":{"enabled":False},"scenes":[
            {"heading":title,"narration":scene["narration"],
             "image":scene["image"],"source_type":"illustration",
             "rights":{"license":"original_user"}}
            for scene in scenes
        ]
    }
    target=out/"storyboard.json"
    target.write_text(json.dumps(safe,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return target

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("request_id")
    parser.add_argument("--source-root",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    board=load_request(args.source_root,args.request_id,args.out)
    print("REQUEST_VALIDATED",args.request_id,board)

if __name__=="__main__":main()
