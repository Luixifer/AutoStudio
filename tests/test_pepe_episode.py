"""Real episode contracts; no invented pictures, licences, voice or render approval."""
import json,unittest,tempfile
from pathlib import Path
import numpy as np
from scripts.pepe.prepare import CUTS,BRIEFS
from scripts.pepe.sound import score,effect,save,RATE
from scripts.director.subshots import ranges
ROOT=Path(__file__).resolve().parents[1]
class PepeEpisodeTests(unittest.TestCase):
 def test_source_has_thirteen_unchanged_paragraphs_and_twenty_six_unique_briefs(self):
  text=(ROOT/'content/pepe-el-gallo-travieso-episodio-1/guion.txt').read_text();paras=text.strip().split('\n\n');self.assertEqual(len(paras),13);self.assertEqual(len(CUTS),13);self.assertEqual(len(BRIEFS),26);self.assertEqual(len(set(b[0] for b in BRIEFS)),26)
  for p,cut in zip(paras,CUTS):
   split=p.index(cut)+len(cut);left,right=p[:split].strip(),p[split:].strip();s={'narration':p,'subshots':[{'start_phrase':part,'end_phrase':part} for part in (left,right)]};r=ranges(s);self.assertEqual(r[0][0],0);self.assertEqual(r[-1][1],len(p.split()));self.assertEqual(r[0][1],r[1][0])
 def test_story_keeps_pio_stranded_and_helped_by_original_friends(self):
  p=(ROOT/'content/pepe-el-gallo-travieso-episodio-1/guion.txt').read_text();self.assertIn('se quedó al otro lado',p);self.assertIn('Lola, la oveja, y a Nube',p);self.assertIn('orilla segura',p);self.assertIn('la tabla era corta',p)
 def test_partial_last_music_bar_never_overruns_and_is_original_deterministic(self):
  for duration in (.10,1.,3.1,9.3):
   a=score(duration);self.assertEqual(a.shape,(round(duration*RATE),2));self.assertTrue(np.isfinite(a).all());self.assertLess(abs(a).max(),.85);self.assertTrue(np.array_equal(a,score(duration)))
 def test_gentle_original_foley_is_finite_bounded_and_has_no_hard_start(self):
  for kind in ('stream','chick','rooster','steps','flutter','wood','clap','wonder'):
   a=effect(kind);self.assertTrue(np.isfinite(a).all());self.assertLessEqual(abs(a).max(),.85);self.assertAlmostEqual(float(a[0]),0,places=5);self.assertTrue(np.array_equal(a,effect(kind)))
 def test_real_wav_write_has_real_duration_and_two_channels(self):
  import wave
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'score.wav';save(path,score(1.25))
   with wave.open(str(path),'rb') as w:self.assertEqual(w.getnchannels(),2);self.assertEqual(w.getframerate(),RATE);self.assertEqual(w.getnframes(),30000)
 def test_portable_archive_inside_story_directory_cannot_include_itself(self):
  import zipfile
  from scripts.pepe.assemble import bundle
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)/'input';root.mkdir();story=Path(td)/'story';story.mkdir();(story/'guion.txt').write_text('Original test story');(story/'ENCARGO.md').write_text('Archive-only fixture, not approved episode assets.')
   required=['project.json','shots.json','audio-provenance.json','input-quality.json','denoise.json','motion-provenance.json','typography.json','master-audit.json']
   for name in required:(root/name).write_text('{}')
   (root/'raw').mkdir();(root/'media').mkdir()
   from PIL import Image
   for i in range(1,27):Image.new('RGB',(8,8),(i*7,80,100)).save(root/'media'/f'shot-{i:02}.png')
   for i in (1,26):Image.new('RGB',(8,8),(20,80,100)).save(root/'raw'/f'shot-{i:02}.png')
   for i in range(1,14):folder=root/f'voice-{i:02}';folder.mkdir();(folder/'metadata.json').write_text('{}')
   target=story/'prepared.zip';report=bundle(root,target,include_master=False,story_dir=story)
   self.assertLess(report['bytes'],4*1024**2)
   with zipfile.ZipFile(target) as z:self.assertIsNone(z.testzip());self.assertFalse(any(n.endswith('.zip') for n in z.namelist()));self.assertIn('content/pepe-el-gallo-travieso-episodio-1/guion.txt',z.namelist())
   self.assertRaises(ValueError,bundle,root,root/'project.json',False,story)
 def test_actual_ffmpeg_reader_checks_more_than_130_frames_without_dropping_samples(self):
  import subprocess
  from scripts.director.correspondence import frames
  with tempfile.TemporaryDirectory() as td:
   movie=Path(td)/'proof.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=160x90:r=30:d=6','-c:v','libx264','-pix_fmt','yuv420p',str(movie)],check=True)
   selected=frames(movie,list(range(160))+[3,6]);self.assertEqual(sorted(selected),list(range(160)));self.assertFalse(np.array_equal(selected[0],selected[159]))
 def test_final_mix_recognizes_limiter_latency_but_rejects_wrong_voice_or_bad_sync(self):
  from scripts.pepe.verify import voice_alignment
  rng=np.random.default_rng(31);voice=rng.normal(size=2400);a=1000
  for offset,expected in ((80,True),(240,False)):
   mixed=np.zeros(6000);mixed[a+offset:a+offset+len(voice)]=voice*.7
   result=voice_alignment(voice,mixed,a);self.assertEqual(result['passed'],expected);self.assertEqual(result['offset_seconds'],offset/16000)
  wrong=rng.normal(size=6000);self.assertFalse(voice_alignment(voice,wrong,a)['passed'])
