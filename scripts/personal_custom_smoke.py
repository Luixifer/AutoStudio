"""End-to-end reproducible sample of custom mobile request (no personal uploads)."""
import hashlib
import json
import tempfile
from pathlib import Path
from PIL import Image,ImageDraw

from scripts.personal_custom_request import load_request
from scripts.personal_prepare import prepare
from scripts.personal_editor import produce


def create_fixture(base,request_id="d1234567890abcdef1234567890abcde"):
    directory=Path(base)/"requests"/request_id
    directory.mkdir(parents=True,exist_ok=True)
    text=[
        "¿Te imaginas un planeta donde la noche esconde una belleza inimaginable?",
        "El universo conserva secretos que la ciencia estudia a través de la luz.",
        "Las imágenes de este vídeo son ilustraciones artísticas, no fotografías reales.",
    ]
    scenes=[]
    for i,line in enumerate(text,1):
        path=directory/f"imagen-{i:02}.jpg"
        image=Image.new("RGB",(720,1280),(14,26+i*16,56+i*18))
        d=ImageDraw.Draw(image)
        d.ellipse((90+i*14,250-i*12,620-i*12,820+i*8),fill=(40+i*50,82+i*24,150))
        d.ellipse((240,540,480,780),outline=(240,200-i*20,110),width=24)
        image.save(path,quality=89)
        scenes.append({
            "image":path.name,"image_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "narration":line,"rights":{"license":"original_user"},
            "source_type":"illustration",
        })
    manifest={
        "schema":3,"request_id":request_id,
        "title":"Tres misterios visuales del universo",
        "format":"short","language":"es",
        "editorial_approved":False,"youtube":{"enabled":False},
        "scenes":scenes,
    }
    (directory/"storyboard.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    return request_id


def main():
    with tempfile.TemporaryDirectory(prefix="autostudio-custom-") as root:
        request_id=create_fixture(root)
        board=load_request(root,request_id,Path(root)/"approved")
        ready=prepare(board,Path(root)/"prepared")
        report=produce(ready,Path(root)/"render")
        assert report["technical_passed"] and not report["ready_to_publish"]
        assert not report["youtube_enabled"]
        assert report["visual_audit"]["shots_checked"]==3
        assert report["subtitle_words"]>20
        print("CUSTOM_UPLOAD_VIDEO_OK",report["sha256"],report["seconds"])

if __name__=="__main__":main()
