import unittest,tempfile,wave
from pathlib import Path
from scripts.director.narration import chunks,synthesize

class ParagraphVoiceTests(unittest.TestCase):
 def test_inference_chunks_do_not_change_paragraph_words(self):
  text=('Una frase corta. '+ 'palabra '*121).strip();parts=chunks(text)
  self.assertEqual(' '.join(parts).split(),text.split());self.assertTrue(all(len(p.split())<=40 for p in parts))
 def test_pcm_offsets_are_measured_and_joined_without_new_scenes(self):
  class Model:
   def synthesize(self,text,path):
    words=text.split();n=len(words)
    with wave.open(str(path),'wb') as out:out.setnchannels(1);out.setsampwidth(2);out.setframerate(24000);out.writeframes(b'\x01\x00'*2400*n)
    return {'words':[{'word':w,'start':i*.1,'end':i*.1+.09} for i,w in enumerate(words)]}
  with tempfile.TemporaryDirectory() as td:
   text='Primera frase. Otra frase diferente.';out=Path(td)/'spoken.wav';info=synthesize(Model(),text,out)
   self.assertEqual(' '.join(w['word'] for w in info['words']),text);self.assertEqual(info['inference_fragments'],2)
   self.assertAlmostEqual(info['words'][2]['start'],.2)
   with wave.open(str(out),'rb') as audio:self.assertEqual(audio.getnframes(),12000)
 def test_failed_boundaries_retry_audio_not_estimated_word_times(self):
  class Model:
   def synthesize(self,text,path):
    if len(text.split())>1:raise ValueError('Missing acoustic boundary')
    with wave.open(str(path),'wb') as out:out.setnchannels(1);out.setsampwidth(2);out.setframerate(24000);out.writeframes(b'\x01\x00'*2400)
    return {'words':[{'word':text,'start':0.,'end':.09}]}
  with tempfile.TemporaryDirectory() as td:
   report=synthesize(Model(),'Uno dos tres',Path(td)/'spoken.wav');self.assertEqual(report['inference_fragments'],3);self.assertAlmostEqual(report['words'][2]['start'],.2)
 def test_long_pcm_decoder_passes_180_seconds_without_weakening_limits(self):
  from scripts.director.audio import pcm
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'long.wav'
   with wave.open(str(path),'wb') as out:out.setnchannels(1);out.setsampwidth(2);out.setframerate(24000);out.writeframes(b'\0\0'*(24000*181))
   samples=pcm(path,600);self.assertEqual(len(samples),16000*181)
   self.assertRaises(ValueError,pcm,path,180)
