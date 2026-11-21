"""Real FFmpeg signal fixtures. Not Hessdalen footage or human voice approval."""
import copy,json,math,shutil,struct,tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from scripts.director.project import FORMATS,validate,digest
from scripts.director.subshots import ranges,resolve
from scripts.director.engine import produce
from scripts.director.correspondence import inspect_correspondence

class AnchoredShotTests(unittest.TestCase):
 def setUp(self):
  self.scene={'id':'paragraph','narration':'Primera frase. Segunda frase. Tercera frase.','subshots':[{'id':'shot-'+str(i),'start_phrase':x+' frase.','end_phrase':x+' frase.','media':{'kind':'image','path':str(i)+'.png','rights':{'license':'own_creation'}},'camera':{'movement':'static'}} for i,x in enumerate(('Primera','Segunda','Tercera'))]}
  self.words=[{'word':word,'start':start,'end':end} for word,start,end in [('Primera',.1,.4),('frase.',.5,.8),('Segunda',1.3,1.6),('frase.',1.7,2.),('Tercera',2.5,2.8),('frase.',2.9,3.2)]]
 def test_ranges_cover_exactly_one_unchanged_paragraph(self):
  plan=ranges(self.scene);self.assertEqual([(a,b) for a,b,_ in plan],[(0,2),(2,4),(4,6)])
  resolved=resolve(self.scene,self.words,30,120);self.assertEqual(sum(p['end_frame']-p['start_frame'] for p in resolved),120)
  self.assertGreaterEqual(resolved[1]['start_frame']/30,.8);self.assertLess(resolved[1]['start_frame']/30,1.3)
 def test_ambiguous_missing_and_overlapping_anchors_fail(self):
  for kind in ('ambiguous','missing','overlap','gap'):
   s=copy.deepcopy(self.scene)
   if kind=='ambiguous':s['subshots'][0]['end_phrase']='frase.'
   elif kind=='missing':s['subshots'][0]['start_phrase']='No existe'
   elif kind=='overlap':s['subshots'][1]['start_phrase']='Primera frase.'
   else:s['subshots'][1]['start_phrase']='frase.';s['subshots'][1]['start_occurrence']=2
   with self.subTest(kind=kind):self.assertRaises(ValueError,ranges,s)
 def test_transition_must_fit_real_pause_and_never_splits_acoustic_unit(self):
  s=copy.deepcopy(self.scene);s['subshots'][0]['transition']={'type':'dissolve','seconds':.2};plan=resolve(s,self.words,30,120)
  self.assertLessEqual((plan[1]['start_frame']+plan[0]['transition_frames'])/30,1.3-1/30+.001)
  s['subshots'][0]['transition']['seconds']=.8;self.assertRaises(ValueError,resolve,s,self.words,30,120)
  words=copy.deepcopy(self.words);words[2]['start']=.81;self.assertRaises(ValueError,resolve,self.scene,words,30,120)
 def test_actual_three_shots_one_audio_and_replace_only_middle(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   for i,color in enumerate(((190,30,50),(30,180,50),(40,50,180))):Image.new('RGB',(320,180),color).save(root/f'{i}.png')
   with wave.open(str(root/'voice.wav'),'wb') as out:
    out.setnchannels(1);out.setsampwidth(2);out.setframerate(24000);out.writeframes(b''.join(struct.pack('<h',int(5000*math.sin(2*math.pi*220*i/24000))) for i in range(81600)))
   s=copy.deepcopy(self.scene);s['voice']={'mode':'file','path':'voice.wav','timed_words':self.words};s['subshots'][0]['transition']={'type':'dissolve','seconds':.2}
   p={'schema':'autostudio-director/1','scene_policy':'paragraph/1','title':'SIGNAL FIXTURE; NOT REAL CHAPTER','format':'horizontal','fps':30,'youtube_enabled':False,'subtitles':{'enabled':False},'chapters':[{'id':'chapter','scenes':[s]}]};file=root/'project.json';file.write_text(json.dumps(p));out=root/'render'
   with patch.dict(FORMATS,{'horizontal':(320,180)}):report=produce(file,out)
   self.assertTrue(report['passed'],report['errors']);timeline=json.loads((out/'timeline.json').read_text());meta=timeline['scenes'][0]
   self.assertEqual(len(timeline['scenes']),1);self.assertEqual(len(meta['subshots']),3);self.assertAlmostEqual(meta['voice_seconds'],3.4);self.assertEqual(len(meta['words']),6)
   voice_hash=digest(out/'scene-cache'/meta['key']/'spoken.wav');old=root/'old.mp4';shutil.copy2(out/'documental-REVISION.mp4',old)
   Image.new('RGB',(320,180),(180,150,20)).save(root/'1.png')
   with patch.dict(FORMATS,{'horizontal':(320,180)}):second=produce(file,out)
   current=json.loads((out/'timeline.json').read_text());changed=current['scenes'][0]
   self.assertTrue(changed['voice']['cache_reused']);self.assertEqual([v['cache_reused'] for v in changed['subshots']],[True,False,True]);self.assertEqual(voice_hash,digest(out/'scene-cache'/changed['key']/'spoken.wav'))
   # Verify an actually old wrong-shot video against the new valid associations.
   shutil.copy2(out/'narration.wav',root/'narration.wav')
   qa=inspect_correspondence(old,current['scenes'],out/'scene-cache',30,current['cues'],root)
   self.assertFalse(qa['passed']);self.assertTrue(qa['scenes'][0]['subshots'][0]['passed']);self.assertFalse(qa['scenes'][0]['subshots'][1]['passed']);self.assertTrue(qa['scenes'][0]['subshots'][2]['passed'])

 def test_real_subshot_video_after_parent_dissolve_uses_shifted_word_times(self):
  with tempfile.TemporaryDirectory() as td:
   import subprocess
   root=Path(td)
   for i,color in enumerate(('red','green','blue','purple')):Image.new('RGB',(320,180),color).save(root/f'{i}.png')
   subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=orange:s=320x180:r=30:d=3','-an','-c:v','libx264','-pix_fmt','yuv420p',str(root/'third.mp4')],check=True)
   with wave.open(str(root/'voice.wav'),'wb') as out:
    out.setnchannels(1);out.setsampwidth(2);out.setframerate(24000);out.writeframes(b''.join(struct.pack('<h',int(5000*math.sin(2*math.pi*220*i/24000))) for i in range(81600)))
   s=copy.deepcopy(self.scene);voice={'mode':'file','path':'voice.wav','timed_words':self.words};s['voice']=voice
   s['subshots'][2]['media']={'kind':'video','path':'third.mp4','rights':{'license':'own_creation'}}
   previous={'id':'previous','narration':s['narration'],'voice':voice,'media':{'kind':'image','path':'3.png','rights':{'license':'own_creation'}},'transition':{'type':'dissolve','seconds':.2}}
   p={'schema':'autostudio-director/1','scene_policy':'paragraph/1','title':'MIXED SIGNAL FIXTURE; NOT CHAPTER','subtitles':{'enabled':False},'format':'horizontal','fps':30,'youtube_enabled':False,'chapters':[{'id':'chapter','scenes':[previous,s]}]}
   path=root/'project.json';path.write_text(json.dumps(p))
   with patch.dict(FORMATS,{'horizontal':(320,180)}):report=produce(path,root/'out')
   self.assertTrue(report['passed'],report['errors']);timeline=json.loads((root/'out/timeline.json').read_text());second=timeline['scenes'][1]
   self.assertAlmostEqual(second['narration_offset'],.2+1/30);self.assertAlmostEqual(second['subshots'][0]['narration_start'],.1+.2+1/30)
   self.assertTrue(all(v['passed'] for v in report['correspondence']['scenes']))
