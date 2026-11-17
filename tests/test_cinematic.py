"""Product checks for the new profile, without network/model downloads in unit tests."""
import hashlib,json,tempfile,unittest,wave
from pathlib import Path
from types import SimpleNamespace as T
from unittest.mock import patch
from PIL import ImageChops,ImageStat
from scripts.neural_narration import words_from_phonemes,NeuralNarrator
from scripts.subtitles import group_words,caption_at
from scripts.cinematic import verify_assets,CinematicArtwork,caption_layout
from scripts.render import load_story
from scripts.soundscape import write_ambience
ROOT=Path(__file__).resolve().parents[1]

def tokens():
    return [T(phoneme='o',start=.1,end=.2),T(phoneme='l',start=.2,end=.3),T(phoneme='a',start=.3,end=.4),T(phoneme=' ',start=.4,end=.4),T(phoneme='m',start=.5,end=.6),T(phoneme='u',start=.6,end=.7),T(phoneme='n',start=.7,end=.8),T(phoneme='d',start=.8,end=.9),T(phoneme='o',start=.9,end=1)]

class CinematicTests(unittest.TestCase):
    def test_phoneme_timing_uses_acoustic_boundaries(self):
        words=words_from_phonemes('Hola mundo.',tokens());self.assertEqual(words,[{'word':'Hola','start':.1,'end':.4},{'word':'mundo.','start':.5,'end':1}])
    def test_unalignable_transcript_refuses_estimates(self):
        with self.assertRaises(ValueError):words_from_phonemes('Hola maravilloso mundo.',tokens())
    def test_word_without_audio_rejected(self):
        with self.assertRaises(ValueError):words_from_phonemes('Hola',[T(phoneme='a',start=0,end=0)])
    def test_punctuation_not_extra_word(self):
        spoken=tokens()+[T(phoneme=' ',start=1,end=1),T(phoneme='.',start=1,end=1.1)]
        self.assertEqual(len(words_from_phonemes('Hola mundo.',spoken)),2)
    def words(self):return [{'word':w,'start':i*.5,'end':i*.5+.4} for i,w in enumerate('Aquí no llega el Sol y hay vida'.split())]
    def test_short_captions_preserve_transcript(self):
        groups=group_words(self.words());self.assertLessEqual(max(len(g['words']) for g in groups),3);self.assertEqual(' '.join(g['text'] for g in groups),'Aquí no llega el Sol y hay vida')
    def test_word_highlight_changes_at_true_boundary(self):
        groups=group_words(self.words());self.assertEqual(caption_at(groups,.1)['active'],0);self.assertEqual(caption_at(groups,.6)['active'],1);self.assertIsNone(caption_at(groups,20))
    def test_caption_does_not_cross_sentence_boundary(self):
        words=[{'word':'Hola.','start':0,'end':.3},{'word':'Adiós.','start':.4,'end':.8}]
        self.assertEqual([g['text'] for g in group_words(words)],['Hola.','Adiós.'])
    def test_overlap_is_rejected(self):
        words=self.words();words[1]['start']=.2
        with self.assertRaises(ValueError):group_words(words)
    def test_negative_time_rejected(self):
        words=self.words();words[0]['start']=-1
        with self.assertRaises(ValueError):group_words(words)
    def test_no_paragraph_size_captions(self):
        with self.assertRaises(ValueError):group_words(self.words(),9)
    def test_all_authored_captions_fit_safe_area(self):
        for scene in load_story(ROOT/'scripts/ocean_v02.json')['scenes']:
            words=[{'word':w,'start':i*.5,'end':i*.5+.4} for i,w in enumerate(scene['voice'].split())]
            for group in group_words(words):self.assertLessEqual(len(caption_layout(group['words'])),2)
    def test_source_assets_are_complete_original_and_unchanged(self):
        assets=verify_assets();self.assertEqual(set(assets),{'seabed_wide','vent_close','community','closing','microbes'})
        self.assertTrue(all('not actual footage' in a['type'] for a in assets.values()))
    def test_each_shot_moves_and_remains_vertical(self):
        assets=verify_assets()
        for i,scene in enumerate(load_story(ROOT/'scripts/ocean_v02.json')['scenes'],1):
            art=CinematicArtwork(scene,i,8,assets);a=art.visual(0,5);b=art.visual(4.96,5)
            self.assertEqual(a.size,(720,1280));self.assertGreater(sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3,.25)
    def test_bad_camera_rejected(self):
        scene=load_story(ROOT/'scripts/ocean_v02.json')['scenes'][0];scene['camera']='typo'
        with self.assertRaises(ValueError):CinematicArtwork(scene,1,8)
    def test_missing_voice_model_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeError):NeuralNarrator(directory)
    def test_tampered_voice_model_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/'kokoro-v1.0.onnx').write_bytes(b'not a neural model')
            with self.assertRaises(ValueError):NeuralNarrator(directory)
    def test_soundscape_is_reproducible_stereo_and_finite(self):
        with tempfile.TemporaryDirectory() as directory:
            a=Path(directory)/'a.wav';b=Path(directory)/'b.wav';write_ambience(a,1,[.5]);write_ambience(b,1,[.5]);self.assertEqual(a.read_bytes(),b.read_bytes())
            with wave.open(str(a)) as f:self.assertEqual((f.getnchannels(),f.getframerate(),f.getnframes()),(2,48000,48000))
    def test_hook_is_in_first_scene_not_after_intro(self):
        story=load_story(ROOT/'scripts/ocean_v02.json');self.assertEqual(story['scenes'][0]['headline'],'AQUÍ NO LLEGA EL SOL');self.assertTrue(story['scenes'][0]['voice'].startswith('Aquí no llega el Sol.'))
if __name__=='__main__':unittest.main()
