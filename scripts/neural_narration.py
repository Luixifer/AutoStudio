"""Local CPU neural Spanish narration; phoneme times come from the same model inference."""
import hashlib,json,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def words_from_phonemes(text,spoken):
    """Map explicit spoken word boundaries, never estimate from character counts."""
    groups=[];current=[]
    for token in spoken:
        if token.phoneme.isspace():
            if current:groups.append(current);current=[]
        else:current.append(token)
    if current:groups.append(current)
    # A punctuation-only token belongs to its neighbouring word, not an extra word.
    actual=[]
    for group in groups:
        if not any(t.phoneme.isalpha() for t in group):
            if actual:actual[-1].extend(group)
        else:actual.append(group)
    words=text.split()
    if len(actual)!=len(words):raise ValueError(f'Phoneme/text alignment mismatch ({len(actual)} vs {len(words)}); refusing guessed subtitles.')
    result=[]
    for word,group in zip(words,actual):
        sounds=[t for t in group if t.end>t.start]
        if not sounds:raise ValueError('Word has no acoustic duration: '+word)
        result.append({'word':word,'start':min(t.start for t in sounds),'end':max(t.end for t in sounds)})
    return result

# Selected by the user after listening to three voices of KELT-9b.
# A voice preference does not imply human-review approval of every rendition.
DEFAULT_VOICE="em_alex"
DEFAULT_SPEED=0.99
DEFAULT_SENTENCE_PAUSE=0.22
DEFAULT_CLAUSE_PAUSE=0.09

class NeuralNarrator:
    def __init__(self,directory=None):
        import numpy as np
        import onnxruntime as rt
        import espeakng_loader
        from kokoro_onnx import Kokoro,EspeakConfig
        rt.disable_telemetry_events();directory=Path(directory or ROOT/'.cache/voice')
        self.hashes={}
        for item in json.loads((ROOT/'assets/voice-models.json').read_text()):
            p=directory/item['file']
            if not p.is_file():raise RuntimeError('Missing neural model; run scripts/fetch_voice.py first.')
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            if digest!=item['sha256']:raise ValueError('Neural model checksum mismatch.')
            self.hashes[item['file']]=digest
        options=rt.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
        session=rt.InferenceSession(str(directory/'kokoro-v1.0.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
        self.engine=Kokoro.from_session(session,str(directory/'voices-v1.0.bin'),EspeakConfig(lib_path=espeakng_loader.get_library_path(),data_path=espeakng_loader.get_data_path()))
        if not self.engine.has_timings:raise RuntimeError('Model has no durations; no fallback to estimated subtitles.')
        if DEFAULT_VOICE not in self.engine.get_voices():raise RuntimeError('Requested Spanish voice absent: '+DEFAULT_VOICE)
    def synthesize(self,text,target,*,voice=DEFAULT_VOICE,speed=DEFAULT_SPEED,sentence_pause=DEFAULT_SENTENCE_PAUSE,clause_pause=DEFAULT_CLAUSE_PAUSE):
        import numpy as np
        if not isinstance(text,str) or not text.strip():raise ValueError('Empty narration.')
        if voice not in ('em_alex','ef_dora') or voice not in self.engine.get_voices():raise ValueError('Voice unavailable or not approved for testing.')
        if not .85<=speed<=1.15 or not 0<=sentence_pause<=.5 or not 0<=clause_pause<=.3:raise ValueError('Unsafe pace parameters.')
        audio,rate,spoken=self.engine.create_timed(text,voice=voice,lang='es',speed=speed,trim=True,sentence_pause=sentence_pause,clause_pause=clause_pause)
        words=words_from_phonemes(text,spoken)
        if not np.all(np.isfinite(audio)) or not len(audio):raise ValueError('Invalid neural audio.')
        if words[-1]['end']>len(audio)/rate+.01:raise ValueError('Timings extend beyond actual audio.')
        target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
        with wave.open(str(target),'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes((np.clip(audio,-1,1)*32767).astype('<i2').tobytes())
        return {'engine':'Kokoro ONNX 0.6.1, local CPU','model':'Kokoro 82M v1.0','voice':voice,'locale_requested':'es-ES','phonemizer_language':'es (Castilian Spanish)','speed':speed,'sample_rate':rate,'timing_method':'model phoneme durations mapped at explicit word boundaries','words':words,'model_sha256':self.hashes,'accent_reviewed_by_human':False,'paid_inference_api':False}
