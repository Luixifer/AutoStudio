"""Pruebas de voces es-ES con distinción c/z frente a s. Solo evaluación privada."""
import asyncio
import json
from pathlib import Path
import edge_tts

OUT=Path("out/luma-castellano")
TEXT=("Érase una vez, en un bosque lleno de secretos, una pequeña luciérnaga llamada Luma. "
      "Vivía en una acogedora casita escondida entre las raíces de un viejo roble. "
      "Cada noche miraba las estrellas y sonreía. ¡Qué bonita era su luz!")
VOICES=[
    ("01_alvaro_castellano", "es-ES-AlvaroNeural", "-12%", "-3Hz"),
    ("02_arnau_castellano", "es-ES-ArnauNeural", "-9%", "+0Hz"),
    ("03_dario_castellano", "es-ES-DarioNeural", "-10%", "-2Hz"),
    ("04_irene_castellana", "es-ES-IreneNeural", "-12%", "-2Hz"),
]
async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for name,voice,rate,pitch in VOICES:
        target=OUT/(name+".mp3")
        try:
            await edge_tts.Communicate(TEXT,voice=voice,rate=rate,pitch=pitch).save(str(target))
        except Exception as exc:
            print("VOICE_FAILED",name,type(exc).__name__,str(exc))
            continue
        if target.stat().st_size < 2000:
            raise RuntimeError("Audio ausente "+name)
        manifest.append(dict(name=name,voice=voice,rate=rate,pitch=pitch,bytes=target.stat().st_size))
        print("VOICE_OK",name,target.stat().st_size)
    if not manifest:
        raise RuntimeError("Ninguna voz produjo audio")
    (OUT/"manifest.json").write_text(json.dumps({"text":TEXT,"samples":manifest},ensure_ascii=False,indent=2))
if __name__=="__main__":
    asyncio.run(main())
