"""Safe, explicit personal-video manifest and YouTube production profiles.

Validates intent and media provenance; it does NOT claim scientific or editorial
verification. Projects cannot publish to YouTube automatically.
"""
import hashlib
import json
import re
from pathlib import Path

PROFILES={
    "short":{"size":[720,1280],"fps":25,"hard_seconds":[10,180],
             "recommended_seconds":[35,55],"min_scenes":2,"max_scenes":45},
    "documentary":{"size":[1280,720],"fps":25,"hard_seconds":[180,1800],
                   "recommended_seconds":[480,720],"min_scenes":8,"max_scenes":180},
    "lab":{"size":[720,1280],"fps":25,"hard_seconds":[3,180],
           "recommended_seconds":[35,55],"min_scenes":2,"max_scenes":45},
}
MOVEMENTS={"zoom_in","zoom_out","pan_left","pan_right","focus","static"}
ALLOWED_IMAGE={".png",".jpg",".jpeg",".webp"}
ALLOWED_AUDIO={".wav"}
SHA256=re.compile(r"[0-9a-f]{64}")
LICENSES={"original_user","own_creation","cc0","public_domain_verified",
          "cc_by_4","cc_by_sa_4","other_verified"}
MAX_CONFIG=1_000_000


def secure_file(root,relative,extensions):
    if not isinstance(relative,str) or not relative or len(relative)>240:
        raise ValueError("Ruta de recurso no válida.")
    p=Path(relative)
    if p.is_absolute() or p.drive or any(q in ("..",".") for q in p.parts):
        raise ValueError("Las rutas deben estar dentro del proyecto.")
    candidate=(Path(root)/p).resolve(strict=True)
    base=Path(root).resolve(strict=True)
    if base not in candidate.parents or not candidate.is_file() or candidate.is_symlink():
        raise ValueError("Recurso fuera del directorio del proyecto.")
    if candidate.suffix.lower() not in extensions:
        raise ValueError("Formato de recurso no permitido.")
    if candidate.stat().st_size>32*1024*1024:
        raise ValueError("Recurso demasiado grande.")
    return candidate


def sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(65536),b""):
            h.update(chunk)
    return h.hexdigest()


def validate_project(root,document,allow_lab=False):
    from PIL import Image
    from wave import open as wave_open
    if not isinstance(document,dict) or document.get("schema")!=2:
        raise ValueError("Se requiere schema 2.")
    kind=document.get("format")
    if kind not in PROFILES or kind=="lab" and not allow_lab:
        raise ValueError("Formato no autorizado.")
    profile=PROFILES[kind]
    if document.get("language")!="es" or document.get("youtube",{}).get("enabled") is not False:
        raise ValueError("Idioma español y YouTube desactivado obligatorios.")
    title=document.get("title")
    if not isinstance(title,str) or not 5<=len(title)<=140 or any(ord(c)<32 for c in title):
        raise ValueError("Título inválido.")
    if document.get("editorial_approved") is not True:
        raise ValueError("El usuario debe aprobar contenido y fuentes antes del render publicable.")
    scenes=document.get("scenes")
    if not isinstance(scenes,list) or not profile["min_scenes"]<=len(scenes)<=profile["max_scenes"]:
        raise ValueError("Número de escenas fuera de límites.")
    image_hashes=set();audio_hashes=set();enriched=[]
    for i,scene in enumerate(scenes,1):
        if not isinstance(scene,dict):raise ValueError("Escena inválida.")
        voice=scene.get("narration")
        if not isinstance(voice,str) or not 12<=len(voice)<=600 or any(ord(c)<32 and c not in "\n" for c in voice):
            raise ValueError("Narración de escena inválida.")
        shot=scene.get("camera",{})
        if not isinstance(shot,dict) or shot.get("movement") not in MOVEMENTS:
            raise ValueError("Movimiento de cámara inválido.")
        target=shot.get("target",[.5,.5])
        if not isinstance(target,list) or len(target)!=2 or any(not isinstance(v,(int,float)) or isinstance(v,bool) or not .05<=v<=.95 for v in target):
            raise ValueError("Punto de interés fuera de la imagen.")
        zoom=shot.get("zoom",1.08)
        if not isinstance(zoom,(int,float)) or isinstance(zoom,bool) or not 1<=zoom<=1.2:
            raise ValueError("Zoom excesivo o no válido.")
        rights=scene.get("rights",{})
        if not isinstance(rights,dict) or rights.get("license") not in LICENSES:
            raise ValueError("Licencia de imagen no declarada.")
        if rights["license"] not in {"original_user","own_creation"}:
            if not isinstance(rights.get("source_url"),str) or not rights["source_url"].startswith("https://"):
                raise ValueError("Recurso ajeno sin procedencia HTTPS.")
            if not isinstance(rights.get("credit"),str) or not rights["credit"].strip():
                raise ValueError("Recurso ajeno sin autor o crédito.")
        picture=secure_file(root,scene.get("image"),ALLOWED_IMAGE)
        with Image.open(picture) as picture_file:
            picture_file.verify()
        with Image.open(picture) as picture_file:
            if picture_file.width<400 or picture_file.height<250:
                raise ValueError("Imagen insuficiente para la composición.")
        digest=sha256_file(picture)
        if digest in image_hashes:
            raise ValueError("La misma imagen exacta se ha reutilizado en varias escenas.")
        image_hashes.add(digest)
        audio=secure_file(root,scene.get("audio"),ALLOWED_AUDIO)
        with wave_open(str(audio),"rb") as wav:
            if wav.getnchannels()!=1 or wav.getsampwidth()!=2 or not 16000<=wav.getframerate()<=48000:
                raise ValueError("Audio debe ser WAV PCM mono de 16 bits.")
            seconds=wav.getnframes()/wav.getframerate()
        if not 1<=seconds<=90:raise ValueError("Audio por escena fuera de límites.")
        audio_hash=sha256_file(audio)
        if audio_hash in audio_hashes:raise ValueError("Audio idéntico reutilizado.")
        audio_hashes.add(audio_hash)
        timings=scene.get("timed_words")
        if not isinstance(timings,list) or len(timings)!=len(voice.split()):
            raise ValueError("Subtítulos sin cobertura exacta por palabra.")
        previous=-1
        for word_token,actual in zip(voice.split(),timings):
            if not isinstance(actual,dict) or actual.get("word")!=word_token:
                raise ValueError("Texto de subtítulo no coincide con narración.")
            start,end=actual.get("start"),actual.get("end")
            if any(not isinstance(v,(float,int)) or isinstance(v,bool) for v in (start,end)) or not previous-0.005<=start<end<=seconds+.04:
                raise ValueError("Tiempos de palabras inválidos.")
            previous=end
        enriched.append({"scene":i,"image_path":str(picture),"audio_path":str(audio),
                         "image_sha256":digest,"audio_sha256":audio_hash,
                         "voice_seconds":seconds,"timed_words":timings,
                         "narration":voice,"camera":shot,"rights":rights})
    total=sum(e["voice_seconds"] for e in enriched)+0.25*len(enriched)
    lower,upper=profile["hard_seconds"]
    if not lower<=total<=upper:
        raise ValueError(f"Duración de {total:.1f} s fuera del perfil {kind} ({lower}-{upper}).")
    warnings=[]
    lo,hi=profile["recommended_seconds"]
    if not lo<=total<=hi:
        warnings.append(f"Duración fuera de objetivo editorial recomendado ({lo}-{hi} s).")
    return {"profile":profile,"format":kind,"title":title,"scenes":enriched,
            "estimated_seconds":round(total,2),"warnings":warnings,
            "scientific_review_claimed":False,"youtube_enabled":False}


def load_project(path,allow_lab=False):
    p=Path(path)
    if not p.is_file() or p.stat().st_size>MAX_CONFIG:raise ValueError("Manifest ausente o excesivo.")
    data=json.loads(p.read_text(encoding="utf-8"))
    return validate_project(p.parent,data,allow_lab=allow_lab)


def summarize_project(project):
    return {"format":project["format"],"title":project["title"],
            "estimated_seconds":project["estimated_seconds"],
            "scene_count":len(project["scenes"]),
            "warnings":project["warnings"],"youtube_enabled":False}
