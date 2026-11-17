"""Local eSpeak NG only. Never calls an audio service or silently substitutes silence."""
from pathlib import Path
import ctypes
import shutil
import subprocess
import wave


def synthesize(text: str, target: Path, *, speed: int = 145) -> dict:
    if not isinstance(text, str) or not text.strip() or len(text) > 4000:
        raise ValueError('Narration must contain 1–4000 characters.')
    if not 100 <= speed <= 200:
        raise ValueError('Speech speed must be between 100 and 200 words/minute.')
    target.parent.mkdir(parents=True, exist_ok=True)
    executable = shutil.which('espeak-ng')
    if executable:
        subprocess.run([executable, '-v', 'es', '-s', str(speed), '-w', str(target), '--stdin'], input=text, text=True, check=True, timeout=90)
        return {'engine': 'eSpeak NG CLI', 'voice': 'es', 'words_per_minute': speed, 'network_requests': 0}
    try:
        import espeakng_loader
    except ImportError as exc:
        raise RuntimeError('Install espeak-ng, or install requirements-local.txt. No silent fallback is allowed.') from exc
    lib = espeakng_loader.load_library()
    if lib is None:
        raise RuntimeError('The bundled eSpeak NG library could not load.')
    lib.espeak_Initialize.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
    lib.espeak_Initialize.restype = ctypes.c_int
    lib.espeak_SetVoiceByName.argtypes = [ctypes.c_char_p]
    lib.espeak_SetVoiceByName.restype = ctypes.c_int
    lib.espeak_SetParameter.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
    lib.espeak_SetParameter.restype = ctypes.c_int
    callback_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)
    lib.espeak_SetSynthCallback.argtypes = [callback_type]
    lib.espeak_Synth.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
    lib.espeak_Synth.restype = ctypes.c_int
    lib.espeak_Synchronize.restype = ctypes.c_int
    chunks = []
    @callback_type
    def receive(samples, count, events):
        if samples and count > 0:
            chunks.append(ctypes.string_at(samples, count * ctypes.sizeof(ctypes.c_short)))
        return 0
    # The library resolves the espeak-ng-data subdirectory from its parent path.
    rate = lib.espeak_Initialize(2, 0, str(Path(espeakng_loader.get_data_path()).parent).encode(), 0)
    if rate <= 0:
        raise RuntimeError('eSpeak NG initialization failed.')
    try:
        if lib.espeak_SetVoiceByName(b'es') != 0 or lib.espeak_SetParameter(1, speed, 0) != 0:
            raise RuntimeError('Spanish voice or speaking rate unavailable.')
        lib.espeak_SetSynthCallback(receive)
        encoded = text.encode('utf-8') + b'\0'
        buffer = ctypes.create_string_buffer(encoded)
        if lib.espeak_Synth(buffer, len(encoded), 0, 1, 0, 1 | 0x100, None, None) != 0:
            raise RuntimeError('eSpeak NG synthesis failed.')
        if lib.espeak_Synchronize() != 0 or not chunks:
            raise RuntimeError('eSpeak NG did not return speech samples.')
        with wave.open(str(target), 'wb') as output:
            output.setnchannels(1); output.setsampwidth(2); output.setframerate(rate)
            output.writeframes(b''.join(chunks))
    finally:
        lib.espeak_Terminate()
    return {'engine': 'eSpeak NG shared library (espeakng-loader 0.2.4)', 'voice': 'es', 'sample_rate': rate, 'words_per_minute': speed, 'network_requests': 0}
