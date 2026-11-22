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
