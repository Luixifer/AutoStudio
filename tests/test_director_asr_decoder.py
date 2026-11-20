import unittest,tempfile,wave,math,struct
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from scripts.director.engine import narrate
class ImportedAudioDecoderTests(unittest.TestCase):
 def test_whisper_receives_actual_pcm_array_not_a_filename(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);audio=root/'voice.wav';out=root/'out';out.mkdir()
   with wave.open(str(audio),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b''.join(struct.pack('<h',int(5000*math.sin(2*math.pi*200*i/24000))) for i in range(24000)))
   class Model:
    def transcribe(this,data,**options):
     self.assertIsInstance(data,np.ndarray);self.assertEqual(data.dtype,np.float32);self.assertEqual(len(data),16000)
     words=[SimpleNamespace(word='Audio',start=0.,end=.3),SimpleNamespace(word='de',start=.32,end=.5),SimpleNamespace(word='ensayo',start=.52,end=.95)]
     return [SimpleNamespace(words=words)],None
   scene={'id':'s1','narration':'Audio de ensayo','voice':{'mode':'file','path':'voice.wav'}}
   raw,words,info=narrate(scene,{},root,out,{'whisper':Model()})
   self.assertEqual(len(words),3);self.assertTrue(raw.is_file());self.assertIn('FFmpeg PCM',info['decoder'])
 def test_bounded_retry_preserves_exact_matching_and_records_failure(self):
  from unittest.mock import patch
  import json
  for retry_matches in (True,False):
   with self.subTest(retry_matches=retry_matches),tempfile.TemporaryDirectory() as directory:
    root=Path(directory);out=root/'out';out.mkdir()
    with wave.open(str(root/'voice.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b'\0\0'*24000)
    calls=[]
    class Model:
     def __init__(this,name,word):this.name=name;this.word=word
     def transcribe(this,data,**options):
      calls.append(this.name)
      return [SimpleNamespace(words=[SimpleNamespace(word=this.word,start=.1,end=.8)])],None
    scene={'narration':'Sesenta','voice':{'mode':'file','path':'voice.wav'}}
    models={'whisper':Model('base','treinta'),'whisper-small':Model('small','60' if retry_matches else 'veinte')}
    if retry_matches:
     _,words,_=narrate(scene,{},root,out,models);self.assertEqual(words[0]['word'],'Sesenta')
    else:self.assertRaisesRegex(ValueError,'dos modelos CPU',narrate,scene,{},root,out,models)
    self.assertEqual(calls,['base','small'])
    evidence=json.loads((out/'alignment-diagnostic.json').read_text());self.assertFalse(evidence['attempts'][0]['passed']);self.assertEqual(evidence['attempts'][1]['passed'],retry_matches)
