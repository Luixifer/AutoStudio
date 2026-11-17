"""Production orchestration contracts; fixtures are not presented as real renders."""
import hashlib,json,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
from scripts.production import build_plan,request_id
from scripts.providers import get_script_provider,LocalImageProvider,ChatGPTProvider
from scripts.publish_job import make_result
ROOT=Path(__file__).resolve().parents[1];ID='1a'*16

class ProductionTests(unittest.TestCase):
    def test_free_provider_covers_supported_topic(self):
        story,plan=build_plan('Quimiosíntesis en el océano profundo',ID)
        self.assertEqual(story['production']['request_id'],ID);self.assertEqual(len(plan['scenes']),8);self.assertFalse(plan['paid_api_allowed']);self.assertFalse(plan['youtube']['enabled'])
    def test_scene_contracts_have_stable_unique_ids_and_real_assets(self):
        story,plan=build_plan('Fuentes hidrotermales',ID);self.assertEqual([s['id'] for s in plan['scenes']],[f's{i:02}' for i in range(1,9)])
        for scene in plan['scenes']:
            self.assertIn('narration',scene);self.assertIn('duration',scene);self.assertIn('effects',scene);self.assertIn('transition',scene);self.assertEqual(scene['subtitles']['max_words'],3)
            media=scene['media'];self.assertEqual(hashlib.sha256((ROOT/media['file']).read_bytes()).hexdigest(),media['sha256'])
    def test_provider_does_not_modify_the_functional_story(self):
        p=ROOT/'scripts/ocean_v02.json';before=p.read_bytes();a,_=build_plan('Océano profundo',ID);a['scenes'][0]['voice']='changed in memory';b,_=build_plan('Océano profundo',ID);self.assertNotEqual(a['scenes'][0]['voice'],b['scenes'][0]['voice']);self.assertEqual(before,p.read_bytes())
    def test_unknown_theme_does_not_silently_use_ocean(self):
        with self.assertRaisesRegex(ValueError,'Tema aún no disponible'):build_plan('La superficie de Marte',ID)
    def test_topic_is_data_not_shell(self):
        topic='Océano $(touch /tmp/autostudio-should-not-exist)';story,plan=build_plan(topic,ID);self.assertEqual(plan['topic'],topic);self.assertFalse(Path('/tmp/autostudio-should-not-exist').exists())
    def test_bad_topic_lengths(self):
        for topic in [None,'ab','x'*161]:
            with self.assertRaises(ValueError):build_plan(topic,ID)
    def test_topic_control_characters_rejected(self):
        with self.assertRaises(ValueError):build_plan('Océano\ncontenido',ID)
    def test_ids_prevent_directory_traversal(self):
        for value in ['../files',None,'a'*31,'x'*32,'A'*32]:
            with self.assertRaises(ValueError):request_id(value)
    def test_documentaries_are_not_falsely_enabled(self):
        with self.assertRaises(ValueError):build_plan('Océano',ID,format='documentary')
    def test_chatgpt_cannot_make_network_calls(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('No paid/network call allowed')):
            with self.assertRaises(RuntimeError):get_script_provider(ChatGPTProvider.id).create('Océano')
    def test_unknown_provider_rejected(self):
        with self.assertRaises(ValueError):get_script_provider('remote-paid-model')
    def test_unknown_visual_resource_rejected(self):
        with self.assertRaises(ValueError):LocalImageProvider().resolve('../not-an-asset')
    def test_failed_job_cannot_claim_a_video(self):
        result=make_result(ID,'123','abc','Luixifer/AutoStudio','failed');self.assertNotIn('video',result);self.assertEqual(result['request_id'],ID);self.assertFalse(result['youtube_published'])
    def test_output_correlation_rejects_another_request(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);(p/'metadata.json').write_text(json.dumps({'production':{'request_id':'2a'*16}}));(p/'validation.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'does not match'):make_result(ID,'123','abc','Luixifer/AutoStudio','completed',p)
    def test_android_exposes_only_the_launcher(self):
        ns='{http://schemas.android.com/apk/res/android}';root=ET.parse(ROOT/'android/app/AndroidManifest.xml').getroot();app=root.find('application')
        self.assertEqual(app.get(ns+'allowBackup'),'false');self.assertEqual(app.get(ns+'usesCleartextTraffic'),'false')
        exported=[a.get(ns+'name') for a in app.findall('activity') if a.get(ns+'exported')=='true'];self.assertEqual(exported,['com.luixifer.autostudio.MainActivity'])
    def test_apk_does_not_request_storage_or_recording_permissions(self):
        ns='{http://schemas.android.com/apk/res/android}';root=ET.parse(ROOT/'android/app/AndroidManifest.xml').getroot();permissions={p.get(ns+'name') for p in root.findall('uses-permission')};self.assertEqual(permissions,{'android.permission.INTERNET','android.permission.ACCESS_NETWORK_STATE'})
    def test_secret_and_signing_key_files_are_not_bundled(self):
        self.assertFalse(any(p.suffix in {'.keystore','.jks'} for p in (ROOT/'android').rglob('*')))
    def test_baseline_mode_is_still_present(self):
        self.assertTrue((ROOT/'scripts/artwork.py').is_file());self.assertTrue((ROOT/'scripts/narration.py').is_file());self.assertTrue((ROOT/'scripts/ocean.json').is_file())
if __name__=='__main__':unittest.main()
