"""A slower original model performance for preschool narration, never time-stretched."""
from pathlib import Path
import wave
import numpy as np
from scripts.neural_narration import NeuralNarrator,words_from_phonemes
PERFORMANCE={'speed':.76,'sentence_pause':.30,'clause_pause':.12,'voice':'ef_dora','locale':'es-ES'}
class ChildNarrator(NeuralNarrator):
 def __init__(self):super().__init__(voice='ef_dora')
 def synthesize(self,text,target):
  audio,rate,spoken=self.engine.create_timed(text,voice=self.voice,lang='es',speed=PERFORMANCE['speed'],trim=True,sentence_pause=PERFORMANCE['sentence_pause'],clause_pause=PERFORMANCE['clause_pause']);words=words_from_phonemes(text,spoken)
  if not len(audio) or not np.isfinite(audio).all() or words[-1]['end']>len(audio)/rate+.01:raise ValueError('Invalid measured preschool narration')
  target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
  with wave.open(str(target),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes((np.clip(audio,-1,1)*32767).astype('<i2').tobytes())
  return {'engine':'Kokoro ONNX local CPU','voice':self.voice,'model_sha256':self.hashes,'locale_requested':'es-ES','phonemizer_language':'es (Castilian Spanish)','performance':PERFORMANCE,'sample_rate':rate,'words':words,'timing_method':'same-model measured phoneme durations; native slower synthesis, no post time-stretch','paid_inference_api':False,'accent_reviewed_by_human':False,'human_naturalness_approved':False}
