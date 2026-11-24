"""Tres interpretaciones de Álex para el cuento Luma; no publica ni cambia el motor principal."""
import json
import wave
from pathlib import Path
import numpy as np
import onnxruntime as rt
import espeakng_loader
from kokoro_onnx import Kokoro, EspeakConfig
from scripts.fetch_voice import fetch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "luma-voice-comparison"
TEXT = (
    "Érase una vez, en un bosque lleno de secretos, una pequeña luciérnaga llamada Luma. "
    "Vivía en una acogedora casita escondida entre las raíces de un viejo roble. "
    "Cada noche, Luma contemplaba las estrellas desde una colina. "
    "¡Qué bonitas eran! Y siempre deseaba lo mismo: poder brillar tanto como ellas."
)
PRESETS = [
    ("01_alex_cuentacuentos", 0.94, 0.30, 0.12),
    ("02_alex_aventura", 1.04, 0.18, 0.06),
    ("03_alex_clasica", 0.99, 0.22, 0.09),
]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assets = fetch(ROOT / ".cache" / "voice")
    rt.disable_telemetry_events()
    options = rt.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = rt.InferenceSession(str(assets / "kokoro-v1.0.onnx"), sess_options=options, providers=["CPUExecutionProvider"])
    engine = Kokoro.from_session(session, str(assets / "voices-v1.0.bin"), EspeakConfig(lib_path=espeakng_loader.get_library_path(), data_path=espeakng_loader.get_data_path()))
    if "em_alex" not in engine.get_voices():
        raise RuntimeError("No aparece la voz em_alex")
    manifest = {"voice": "em_alex", "model": "Kokoro v1.0", "text": TEXT, "samples": []}
    for name, speed, sentence_pause, clause_pause in PRESETS:
        audio, rate, _ = engine.create_timed(TEXT, voice="em_alex", lang="es", speed=speed, trim=True, sentence_pause=sentence_pause, clause_pause=clause_pause)
        if not len(audio) or not np.all(np.isfinite(audio)):
            raise RuntimeError("Audio inválido en " + name)
        target = OUT / (name + ".wav")
        with wave.open(str(target), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            wav.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
        manifest["samples"].append({"file": target.name, "speed": speed, "sentence_pause": sentence_pause, "clause_pause": clause_pause, "seconds": round(len(audio)/rate, 3)})
        print("SAMPLE_OK", name, round(len(audio)/rate, 2), "seconds")
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
