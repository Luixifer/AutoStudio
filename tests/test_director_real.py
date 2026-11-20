"""Small real FFmpeg integration fixtures. Tones are NOT narration quality tests."""
import json,math,struct,tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch
from PIL import Image,ImageDraw
from scripts.director.project import SCHEMA,FORMATS,digest
from scripts.director.engine import produce,render_scene

class DirectorRealFFmpegTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  Image.new('RGB',(320,180),(60,100,170)).save(self.root/'image.webp')
  im=Image.new('RGBA',(320,180),(0,0,0,0));ImageDraw.Draw(im).ellipse((130,60,190,120),fill=(220,180,40,160));im.save(self.root/'layer.png')
  with wave.open(str(self.root/'voice.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b''.join(struct.pack('<h',int(5000*math.sin(2*math.pi*200*i/24000))) for i in range(24000)))
  own={'license':'own_creation'}
  self.scene={'id':'s1','narration':'Audio de ensayo','voice':{'mode':'file','path':'voice.wav','timed_words':[{'word':'Audio','start':0,'end':.25},{'word':'de','start':.3,'end':.45},{'word':'ensayo','start':.5,'end':.95}]},'media':{'kind':'image','path':'image.webp','rights':own,'layers':[{'path':'layer.png','rights':own,'from':[-.01,0],'to':[.01,0]}]},'transition':{'type':'dissolve','seconds':.2}}
  self.p={'schema':SCHEMA,'title':'ENSAYO DE SEÑAL, NO VOZ HUMANA','format':'horizontal','fps':30,'youtube_enabled':False,'chapters':[{'id':'c1','scenes':[self.scene,{**self.scene,'id':'s2'}]},{'id':'c2','scenes':[{**self.scene,'id':'s3'}]}],'music':{'path':'voice.wav','gain':.05,'rights':own}}
 def tearDown(self):self.tmp.cleanup()
 def test_actual_multichapter_fades_audio_subtitles_and_resume(self):
  p=self.root/'project.json';p.write_text(json.dumps(self.p));out=self.root/'out'
  with patch.dict(FORMATS,{'horizontal':(320,180)}):r=produce(p,out)
  self.assertTrue(r['passed'],r['errors']);self.assertAlmostEqual(r['duration'],3.6,delta=.1);self.assertEqual(r['caption_count'],3);self.assertTrue(r['full_decode']);self.assertFalse(r['black_intervals'])
  timeline=json.loads((out/'timeline.json').read_text());self.assertAlmostEqual(timeline['scenes'][1]['start'],1.2);self.assertAlmostEqual(timeline['scenes'][2]['start'],2.4);self.assertEqual(len(timeline['chapters']),2)
  # A completed scene must be reused without touching the real encoded file.
  cache=out/'scene-cache';m=next(cache.glob('*/complete.json'));data=json.loads(m.read_text());video=m.parent/'visual.mp4';before=video.stat().st_mtime_ns
  with patch.dict(FORMATS,{'horizontal':(320,180)}):work,info=render_scene(self.scene,self.p,self.root,cache,{})
  self.assertEqual(before,video.stat().st_mtime_ns);self.assertTrue(info['files'])
 def test_clip_requires_explicit_loop_if_short(self):
  import subprocess
  subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=s=320x180:r=24:d=0.5','-c:v','libx264',str(self.root/'clip.mp4')],check=True)
  self.scene['media']={'kind':'video','path':'clip.mp4','rights':{'license':'own_creation'}}
  with patch.dict(FORMATS,{'horizontal':(320,180)}):self.assertRaises(ValueError,render_scene,self.scene,self.p,self.root,self.root/'cache',{})
  self.scene['media']['loop']=True
  with patch.dict(FORMATS,{'horizontal':(320,180)}):work,r=render_scene(self.scene,self.p,self.root,self.root/'cache',{})
  self.assertTrue((work/'visual.mp4').is_file());self.assertGreater(r['visual_seconds'],1)
