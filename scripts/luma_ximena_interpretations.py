"""Luma: Ximena alternative prosodic takes. Keep approved original untouched.

Not emotional neural style transfer: variations in punctuated text, rate and pitch
to see which take sounds more affectionate, dreamy, or expressive.
"""
import asyncio, json
from pathlib import Path
import edge_tts

OUT=Path("out/luma-ximena-entonaciones")
VOICE="es-ES-XimenaNeural"
TAKES=[
    {
        "name":"01_ximena_ternura",
        "label":"Tierna, intimista",
        "rate":"-11%",
        "pitch":"-4Hz",
        "text":(
            "Érase una vez, en un bosque lleno de secretos, una pequeña luciérnaga llamada Luma. "
            "Vivía en una acogedora casita escondida entre las raíces de un viejo roble. "
            "Cada noche, Luma contemplaba las estrellas desde una colina. "
            "¡Qué bonitas eran! "
            "Y siempre deseaba lo mismo: poder brillar tanto como ellas."
        ),
    },
    {
        "name":"02_ximena_sonadora",
        "label":"Soñadora y maravillada",
        "rate":"-14%",
        "pitch":"+2Hz",
        "text":(
            "Érase una vez... en un bosque lleno de secretos, una pequeña luciérnaga llamada Luma. "
            "Vivía en una acogedora casita, escondida entre las raíces de un viejo roble. "
            "Cada noche, Luma contemplaba las estrellas desde una colina... "
            "¡Qué bonitas eran! "
            "Y siempre deseaba lo mismo... poder brillar tanto como ellas."
        ),
    },
    {
        "name":"03_ximena_expresiva",
        "label":"Narradora expresiva",
        "rate":"-9%",
        "pitch":"-1Hz",
        "text":(
            "Érase una vez, en un bosque lleno de secretos... una pequeña luciérnaga llamada Luma. "
            "Vivía en una acogedora casita escondida entre las raíces de un viejo roble. "
            "Cada noche, Luma contemplaba las estrellas desde una colina. "
            "¡Qué bonitas eran! "
            "Y siempre deseaba lo mismo: ¡poder brillar tanto como ellas!"
        ),
    },
]
async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    catalog=await edge_tts.list_voices()
    assert any(v.get("ShortName")==VOICE and v.get("Locale")=="es-ES" for v in catalog)
    done=[]
    for take in TAKES:
        name=take["name"]
        try:
            path=OUT/f"{name}.mp3"
            await edge_tts.Communicate(take["text"],voice=VOICE,rate=take["rate"],pitch=take["pitch"]).save(str(path))
            if not path.is_file() or path.stat().st_size<30000:raise RuntimeError("Audio short or missing")
            print("AUDIO_OK",name,path.stat().st_size)
            done.append({**take,"file":path.name,"bytes":path.stat().st_size})
        except Exception as exc:print("AUDIO_FAILED",name,repr(exc))
    if not done:raise RuntimeError("No voice samples generated")
    (OUT/"manifest.json").write_text(json.dumps({"source_voice":VOICE,"interpretations":done},ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":asyncio.run(main())
