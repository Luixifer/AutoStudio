import copy,json,tempfile,unittest,wave,math,struct
from pathlib import Path
from unittest.mock import patch
from PIL import Image,ImageDraw
from scripts.director.project import FORMATS,validate
from scripts.director.engine import produce
from scripts.director.correspondence import inspect_correspondence
from scripts.director.captions import phrases

class SceneIntegrityTests(unittest.TestCase):
 def test_phrase_captions_keep_punctuation_and_words(self):
  text='La narración debe conservar frases completas y una puntuación clara. Este es otro ejemplo.'
  words=[{'word':w,'start':i*.22,'end':i*.22+.2} for i,w in enumerate(text.split())]
  cues=phrases(words);self.assertEqual(' '.join(c['text'] for c in cues),text);self.assertGreater(len(cues[0]['text'].split()),3)
 def test_actual_five_scene_order_and_transition_quarantine(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);scenes=[]
   with wave.open(str(root/'voice.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b''.join(struct.pack('<h',int(4000*math.sin(2*math.pi*220*i/24000))) for i in range(24000)))
   for i,color in enumerate(((180,30,40),(25,180,60),(20,70,200),(180,170,30),(130,40,170))):
    image=Image.new('RGB',(320,180),color);ImageDraw.Draw(image).rectangle((25+i*30,35,55+i*30,130),fill='white');image.save(root/f'{i}.png')
    scenes.append({'id':f's{i}','narration':f'Escena número {i}.','media':{'kind':'image','path':f'{i}.png','rights':{'license':'own_creation'}},'camera':{'movement':'static'},'voice':{'mode':'file','path':'voice.wav','timed_words':[{'word':'Escena','start':.03,'end':.25},{'word':'número','start':.3,'end':.55},{'word':f'{i}.','start':.6,'end':.95}]},'transition':{'type':'dissolve','seconds':.4}})
   config={'schema':'autostudio-director/1','scene_policy':'paragraph/1','subtitles':{'enabled':False},'title':'Señal técnica; NO narración real','format':'horizontal','fps':30,'youtube_enabled':False,'chapters':[{'id':'c1','scenes':scenes}]};path=root/'project.json';path.write_text(json.dumps(config))
   with patch.dict(FORMATS,{'horizontal':(320,180)}):report=produce(path,root/'good')
   self.assertTrue(report['passed'],report['errors']);self.assertTrue(report['correspondence']['passed'])
   timeline=json.loads((root/'good/timeline.json').read_text());self.assertEqual(len(timeline['scenes']),5)
   for i,scene in enumerate(timeline['scenes']):
    self.assertEqual(scene['position'],i);self.assertAlmostEqual(scene['voice_seconds'],1)
    if i:self.assertGreaterEqual(scene['narration_start'],scene['start']+.399)
   bad=copy.deepcopy(config);bad['chapters'][0]['scenes'][0]['media'],bad['chapters'][0]['scenes'][1]['media']=bad['chapters'][0]['scenes'][1]['media'],bad['chapters'][0]['scenes'][0]['media'];path.write_text(json.dumps(bad))
   with patch.dict(FORMATS,{'horizontal':(320,180)}):produce(path,root/'swapped')
   qa=inspect_correspondence(root/'swapped/documental-REVISION.mp4',timeline['scenes'],root/'good/scene-cache',30,timeline['cues'],root)
   self.assertFalse(qa['passed']);self.assertTrue(any(not s['passed'] for s in qa['scenes'][:2]));self.assertTrue(all(s['passed'] for s in qa['scenes'][2:]))
   duplicate=copy.deepcopy(config);duplicate['chapters'][0]['scenes'][1]['media']=duplicate['chapters'][0]['scenes'][0]['media']
   self.assertRaisesRegex(ValueError,'Recurso repetido',validate,duplicate,root)
