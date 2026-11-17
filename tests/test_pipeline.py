import json,math,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.publish_result import main as publish_main,verified_bundle
from scripts.render import load_story,cues_for,srt_time
from scripts.artwork import wrap_pixels,font,SceneArtwork
from scripts.validate_video import inspect_video

ROOT=Path(__file__).resolve().parents[1]
class ScriptTests(unittest.TestCase):
    def test_authored_story_loads(self):
        story=load_story(ROOT/'scripts/ocean.json');self.assertEqual(len(story['scenes']),3);self.assertEqual(story['language'],'es')
    def invalid(self,change):
        story=json.loads((ROOT/'scripts/ocean.json').read_text());change(story)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'story.json';p.write_text(json.dumps(story))
            with self.assertRaises(ValueError):load_story(p)
    def test_unknown_visual_rejected(self):self.invalid(lambda d:d['scenes'][0].update(visual='not_a_real_visual'))
    def test_empty_narration_rejected(self):self.invalid(lambda d:d['scenes'][0].update(voice=' '))
    def test_missing_sources_rejected(self):self.invalid(lambda d:d.update(sources=[]))
    def test_source_credentials_rejected(self):self.invalid(lambda d:d['sources'][0].update(url='https://secret:secret@example.org/'))
    def test_output_id_traversal_rejected(self):self.invalid(lambda d:d.update(id='../elsewhere'))
    def test_scene_budget(self):self.invalid(lambda d:d.update(scenes=d['scenes']*3))
    def test_subtitle_coverage(self):
        text='Un guion de prueba con suficientes palabras para verificar la continuidad y los tiempos de los subtítulos.'
        cues=cues_for(text,12.3);self.assertEqual(' '.join(c['text'] for c in cues),text)
        for a,b in zip(cues,cues[1:]):self.assertAlmostEqual(a['end'],b['start'])
        self.assertLess(cues[-1]['end'],12.3);self.assertTrue(all(c['end']>c['start'] for c in cues))
    def test_srt_rounding(self):self.assertEqual(srt_time(59.9996),'00:01:00,000')
    def test_unicode_fits_pixels(self):
        lines=wrap_pixels('Quimiosíntesis: energía química, no luz local.',font(31),608);self.assertTrue(all(font(31).getlength(s)<=608 for s in lines))
    def test_oversized_word_fails(self):
        with self.assertRaises(ValueError):wrap_pixels('x'*100,font(31),608)
    def test_all_frames_change_and_keep_dimensions(self):
        for i,s in enumerate(load_story(ROOT/'scripts/ocean.json')['scenes'],1):
            art=SceneArtwork(s,i,3);a=art.frame(.3,12,'Texto de prueba.');b=art.frame(2.1,12,'Texto de prueba.')
            self.assertEqual(a.size,(720,1280));self.assertNotEqual(a.tobytes(),b.tobytes())
    def test_publisher_refuses_standalone_execution(self):
        with patch.dict('os.environ',{'GITHUB_ACTIONS':'false'}):
            with self.assertRaises(RuntimeError):publish_main()
    def test_publisher_rejects_output_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'latest.json';p.write_text(json.dumps({'directory':directory}))
            with self.assertRaises(ValueError):verified_bundle(p,'owner/repo','123','abc')
    def test_validator_rejects_missing_file(self):
        with self.assertRaises(ValueError):inspect_video(Path('/tmp/autostudio-missing-file-do-not-create.mp4'))
    def test_validator_rejects_real_silent_audio_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'silent_test_fixture.mp4'
            subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','color=c=black:s=720x1280:r=25','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t','4','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(p)],check=True,timeout=60)
            result=inspect_video(p);self.assertFalse(result['passed']);self.assertTrue(any('silent' in e for e in result['errors']))
if __name__=='__main__':unittest.main()
