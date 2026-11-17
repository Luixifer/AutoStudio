"""Export an editable YouTube upload pack from a verified personal render.

No invented sources, automatic YouTube posts, manufactured revenue claims,
or algorithmic promises. Publishing requires a human decision.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

def safe_summary(text):
    return " ".join(text.replace("\n"," ").split()).strip()

def validate_metadata(document):
    title=safe_summary(document.get("title",""))
    if not 8<=len(title)<=100:
        raise ValueError("YouTube title outside 8-100 characters.")
    tags=document.get("tags",[])
    if not isinstance(tags,list) or len(tags)>15 or any(
        not isinstance(tag,str) or not tag.strip() or len(tag)>50 for tag in tags
    ):raise ValueError("Invalid metadata tags.")
    return title,tags


def produce_upload_pack(input_manifest,quality_report,destination):
    from scripts.personal_studio import sha256_file
    manifest=json.loads(Path(input_manifest).read_text(encoding="utf-8"))
    quality=json.loads(Path(quality_report).read_text(encoding="utf-8"))
    if not quality.get("technical_passed") or quality.get("ready_to_publish"):
        raise ValueError("The video must pass technical QA and remain in review.")
    title,_=validate_metadata(manifest)
    output=Path(destination);output.mkdir(parents=True,exist_ok=True)
    passages=[safe_summary(scene["narration"]) for scene in manifest["scenes"]]
    lead=passages[0]+" "+(passages[1] if len(passages)>1 else "")
    sources=manifest.get("sources",[])
    lines=[lead,"","Una explicación visual original, con narración Álex y recreaciones artísticas.",
           "","Fuentes y créditos:"]
    if sources:
        for entry in sources:
            if not isinstance(entry,dict) or not isinstance(entry.get("url"),str) or not entry["url"].startswith("https://"):
                raise ValueError("Source URL absent or invalid.")
            lines.append("- "+safe_summary(entry.get("title","Fuente"))+": "+entry["url"])
    else:
        lines.append("- Fuentes científicas pendientes de verificación y atribución editorial.")
    lines.extend(["","Aviso: las imágenes son recreaciones artísticas y no fotografías de los fenómenos.",
                  "","No se ha publicado automáticamente en YouTube."])
    # Shorts do not imply that a custom thumbnail is always selectable.
    text="\n".join(lines)
    suggested_title=title[:95]
    if manifest.get("format")=="short" and "#Shorts" not in suggested_title:
        suggested_title=suggested_title[:93]
    chapters=[]
    if manifest.get("format")=="documentary":
        cursor=0.
        for scene,shot in zip(manifest["scenes"],quality["shots"]):
            seconds=int(cursor)
            hh,rem=divmod(seconds,3600);mm,ss=divmod(rem,60)
            chapter=f"{hh:02d}:{mm:02d}:{ss:02d} {safe_summary(scene.get('heading','Escena'))[:80]}"
            chapters.append(chapter)
            cursor+=float(shot["seconds"])
        if len(chapters)<3:
            chapters=[]
        if chapters:
            text+="\n\nCapítulos sugeridos (revisar):\n"+"\n".join(chapters)
    bundle={
        "title_suggestion":suggested_title,
        "description":text,
        "content_type":manifest["format"],
        "language":"es-ES",
        "audience":"general",
        "synthetic_visual_disclosure_review_required":True,
        "upload_status":"manual_review_only",
        "youtube_published":False,
        "revenue_estimate":None,
        "technical_sha256":quality["sha256"],
        "scientific_sources_verified_by_exporter":False,
        "human_voice_acceptance_by_exporter":False,
        "chapters_suggestions":chapters,
        "warnings":quality.get("warnings",[]),
    }
    (output/"youtube-draft.json").write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (output/"youtube-draft.txt").write_text(
        suggested_title+"\n\n"+text+"\n\n"
        +"Antes de publicar: comprobar hechos, atribuciones, voz, imágenes y declaración de contenido sintético.\n",
        encoding="utf-8")
    video=Path(quality["video"])
    if video.is_file() and sha256_file(video)==quality["sha256"]:
        thumb=output/"miniatura-revision.jpg"
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                        "-ss","1","-i",str(video),"-frames:v","1","-q:v","3",
                        str(thumb)],check=True,timeout=45)
    return bundle


def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest",type=Path)
    p.add_argument("quality",type=Path)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    package=produce_upload_pack(args.manifest,args.quality,args.out)
    print("YOUTUBE_DRAFT_ONLY",package["title_suggestion"],package["upload_status"])

if __name__=="__main__":main()
