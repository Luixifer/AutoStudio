"""Luma: complete 14-page story with Ximena Expressive, 3% slower.

Private review only; does not authorize commercial publication. All 14 spoken
pages are kept separately and assembled into a single MP3 with page gaps.
"""
import asyncio
import json
import subprocess
import tempfile
import wave
from pathlib import Path

import edge_tts

VOICE = "es-ES-XimenaNeural"
RATE = "-9%"
PITCH = "-1Hz"
TEMPO = 0.97
SAMPLE_RATE = 24000
PAGE_GAP_SECONDS = 1.20
OUT = Path("out/luma-cuento-completo-ximena")
PAGES = [
    "Érase una vez, en un bosque lleno de secretos... una pequeña luciérnaga llamada Luma. Vivía en una acogedora casita escondida entre las raíces de un viejo roble.",
    "Cada noche, Luma contemplaba las estrellas desde una colina. ¡Qué bonitas eran! Y siempre deseaba lo mismo: ¡poder brillar tanto como ellas!",
    "Una noche vio una luz dorada detrás de las montañas. ¡Parecía una estrella caída! Luma abrió mucho los ojos y decidió ir a buscarla.",
    "Agitó sus pequeñas alas, tomó impulso y salió volando. Pasó entre las ramas, esquivó las hojas y se adentró en un lugar del bosque que nunca había visitado.",
    "Llegó a un jardín donde las flores eran más altas que los árboles de su casa. De repente, escuchó una vocecita: —¡Socorro! ¿Hay alguien ahí?",
    "Detrás de un rosal encontró a una polilla atrapada entre las espinas. Se llamaba Nuba. Luma olvidó por un momento su estrella y corrió a ayudarla.",
    "Luma empujó una ramita con todas sus fuerzas. Una vez, dos veces... ¡y a la tercera consiguió apartarla! Nuba pudo extender de nuevo sus alas.",
    "—¡Gracias, Luma! —exclamó Nuba. Y justo entonces ocurrió algo extraño: la pequeña luz de Luma brilló un poquito más. ¡Qué sorpresa se llevó!",
    "Pero cuando las dos amigas emprendieron el regreso, una espesa niebla cubrió el bosque. Los árboles desaparecieron entre las sombras y Nuba empezó a temblar.",
    "—No tengas miedo —susurró Luma. Aunque ella también estaba asustada, respiró profundamente, levantó sus antenas y comenzó a iluminar el camino.",
    "Pronto, un conejito perdido siguió su luz. Después llegó un erizo y, más atrás, dos pequeños escarabajos. Todos caminaron juntos detrás de Luma.",
    "Y cuanto más ayudaba Luma, más intensa se volvía su luz. Hasta que, de pronto, el sendero entero resplandeció y la niebla comenzó a desaparecer.",
    "Al llegar a casa, Luma comprendió algo maravilloso: la luz era muy importante para todos, porque les ayudaba a ver, a encontrar el camino y a no sentirse solos en la oscuridad. Por primera vez, se sintió orgullosa de su pequeña luz.",
    "Aquella noche, Luma miró las estrellas y sonrió. Ya no deseaba brillar más que ellas, porque había descubierto algo mucho más importante: no hacía falta tener la luz más grande del mundo para iluminar el corazón de los demás. Y colorín colorado, este cuento se ha acabado.",
]

def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *map(str,args)], check=True)

async def synthesize(text, destination):
    error = None
    for attempt in range(3):
        try:
            await edge_tts.Communicate(text, voice=VOICE, rate=RATE, pitch=PITCH).save(str(destination))
            if destination.stat().st_size < 4000:
                raise RuntimeError("Audio unexpectedly small")
            return
        except Exception as exc:
            error = exc
            print("TTS_RETRY", attempt + 1, repr(exc))
            if attempt < 2:
                await asyncio.sleep(2 + attempt * 3)
    raise RuntimeError("Failed synthesis: " + repr(error))

async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = await edge_tts.list_voices()
    if not any(v.get("ShortName") == VOICE and v.get("Locale") == "es-ES" for v in catalog):
        raise RuntimeError("Ximena es-ES unavailable")
    story = bytearray()
    entries = []
    pcm_rate = SAMPLE_RATE * 2
    gap = bytes(int(PAGE_GAP_SECONDS * pcm_rate))
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for idx, text in enumerate(PAGES, 1):
            source = root / f"page_{idx:02d}_source.mp3"
            pcm = root / f"page_{idx:02d}.pcm"
            target = OUT / f"pagina_{idx:02d}_ximena.mp3"
            await synthesize(text, source)
            # Tempo adjustment is applied *after* the native voice synthesis,
            # matching the approved 3%-slower expressive example.
            ffmpeg("-i", source, "-af", f"atempo={TEMPO}", "-ac", "1",
                   "-ar", str(SAMPLE_RATE), "-f", "s16le", pcm)
            samples = pcm.read_bytes()
            if len(samples) < SAMPLE_RATE * 2 * 3:
                raise RuntimeError("Page too short to be valid: " + str(idx))
            ffmpeg("-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1",
                   "-i", pcm, "-codec:a", "libmp3lame", "-qscale:a", "3", target)
            if idx > 1:
                story.extend(gap)
            start = round(len(story) / pcm_rate, 3)
            story.extend(samples)
            seconds = round(len(samples) / pcm_rate, 3)
            entries.append({"page":idx,"file":target.name,"start_seconds":start,
                            "duration_seconds":seconds,"text":text})
            print("PAGE_OK", idx, seconds, target.stat().st_size, flush=True)
        if len(entries) != 14:
            raise RuntimeError("Expected fourteen pages")
        complete_raw = root / "complete.pcm"
        complete_raw.write_bytes(story)
        master = OUT / "luma_cuento_completo_ximena_expresiva_lenta.mp3"
        ffmpeg("-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1",
               "-i", complete_raw, "-codec:a", "libmp3lame", "-qscale:a", "3", master)
    manifest = {
        "title": "La pequeña luciérnaga que quería brillar más",
        "voice": VOICE, "rate": RATE, "pitch": PITCH, "post_tempo":TEMPO,
        "page_gap_seconds":PAGE_GAP_SECONDS,
        "whole_audio":master.name,
        "total_seconds":round(len(story)/pcm_rate,3),
        "pages":entries,
        "publication_status":"private review only; commercial voice rights not verified"
    }
    (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/"guion_completo.txt").write_text("\n\n".join(f"PÁGINA {i}\n{p}" for i,p in enumerate(PAGES,1))+"\n",encoding="utf-8")
    print("FINAL_OK",master,manifest["total_seconds"],master.stat().st_size,flush=True)

if __name__=="__main__":
    asyncio.run(main())
