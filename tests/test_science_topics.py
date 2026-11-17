"""Phase A acceptance: semantics, media identity, rights, motion and old-client compatibility."""
import hashlib,json,itertools,re,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
from scripts.providers import LocalScriptProvider,LocalImageProvider
from scripts.production import build_plan
from scripts.cinematic import verify_assets,CinematicArtwork,caption_layout
from scripts.render import load_story
from scripts.subtitles import group_words
ROOT=Path(__file__).resolve().parents[1];NEW=['auroras','dna','volcanoes'];ID='aa'*16

def catalog():return {t['id']:t for t in json.loads((ROOT/'content/catalog.json').read_text())['topics'] if t.get('published',True)}
class ScienceTopicTests(unittest.TestCase):
    def test_published_catalog_has_old_and_three_new_topics(self):self.assertEqual(set(catalog()),{'ocean-life',*NEW})
    def test_domains_are_genuinely_different(self):
        domains={load_story(ROOT/catalog()[t]['story'])['science_domain'] for t in NEW};self.assertEqual(len(domains),3)
    def test_provider_selects_each_authored_story(self):
        for topic in NEW:
            story=LocalScriptProvider().create(catalog()[topic]['name']);self.assertEqual(story['topic_id'],topic);self.assertEqual(len(story['scenes']),8)
    def test_old_android_03_request_still_works(self):
        story,plan=build_plan('Quimiosíntesis: vida sin Sol en el océano profundo',ID);self.assertEqual(story['id'],'ocean_v02');self.assertEqual(plan['topic_id'],'ocean-life');self.assertEqual(plan['scenes'][0]['media']['asset_id'],'seabed_wide')
    def test_unsupported_free_topic_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError,'Tema aún no disponible'):LocalScriptProvider().create('La superficie de Marte')
    def test_ambiguous_topic_is_not_silently_chosen(self):
        with self.assertRaisesRegex(ValueError,'ambiguo'):LocalScriptProvider().create('Auroras y volcanes')
    def test_new_themes_never_reuse_ocean_assets(self):
        old={a['sha256'] for a in verify_assets().values()}
        for topic in NEW:
            _,plan=build_plan(catalog()[topic]['name'],ID);self.assertFalse(old & {s['media']['sha256'] for s in plan['scenes']})
    def test_each_new_theme_has_disjoint_visual_files_and_hashes(self):
        plans={t:build_plan(catalog()[t]['name'],ID)[1] for t in NEW}
        for a,b in itertools.combinations(NEW,2):
            self.assertFalse({s['media']['sha256'] for s in plans[a]['scenes']} & {s['media']['sha256'] for s in plans[b]['scenes']})
            self.assertFalse({s['media']['file'] for s in plans[a]['scenes']} & {s['media']['file'] for s in plans[b]['scenes']})
    def test_scripts_are_more_than_title_substitutions(self):
        stories={t:LocalScriptProvider().create(catalog()[t]['name']) for t in NEW}
        for a,b in itertools.combinations(NEW,2):
            aa=' '.join(s['voice'] for s in stories[a]['scenes']);bb=' '.join(s['voice'] for s in stories[b]['scenes']);self.assertNotEqual(aa,bb)
            tri=lambda text:set(zip(*(re.findall(r'\w+',text.lower())[i:] for i in range(3))))
            x,y=tri(aa),tri(bb);self.assertLess(len(x&y)/max(1,len(x|y)),.15)
    def test_perceptual_hero_images_differ_not_only_file_names(self):
        thumbs={}
        for t in NEW:
            s=LocalScriptProvider().create(catalog()[t]['name']);a=LocalImageProvider().resolve(s['scenes'][0]['asset']);thumbs[t]=Image.open(ROOT/a['file']).convert('RGB').resize((48,80))
        for a,b in itertools.combinations(NEW,2):self.assertGreater(sum(ImageStat.Stat(ImageChops.difference(thumbs[a],thumbs[b])).mean)/3,8)
    def test_all_new_resource_rights_and_editable_sources_exist(self):
        for t in NEW:
            story=LocalScriptProvider().create(catalog()[t]['name'])
            for a in verify_assets(story['asset_manifest']).values():
                self.assertEqual(a['topic_id'],t);self.assertEqual(a['license'],'LicenseRef-AutoStudio-Original');self.assertTrue((ROOT/a['license_file']).is_file());self.assertTrue((ROOT/a['source']).is_file());self.assertIn('not actual footage',a['type'])
    def test_scene_plan_keeps_credit_and_license(self):
        for t in NEW:
            story,plan=build_plan(catalog()[t]['name'],ID)
            for s in plan['scenes']:self.assertTrue(s['media']['credit']);self.assertTrue(s['media']['license']);self.assertTrue(s['effects']['scientific_motion'])
    def test_each_new_topic_has_actual_source_retrieval_evidence(self):
        r=json.loads((ROOT/'research/source-check-20261117.json').read_text());self.assertTrue(r['passed']);self.assertTrue(r['github_run_id'])
        for t in NEW:
            verified={p['url'] for p in r['topics'][t]['pages'] if p.get('retrieved') and p.get('status')==200}
            story=LocalScriptProvider().create(catalog()[t]['name']);self.assertTrue(all(p['url'] in verified for p in story['sources']))
    def test_all_new_captions_fit_safe_area(self):
        for t in NEW:
            story=LocalScriptProvider().create(catalog()[t]['name'])
            for scene in story['scenes']:
                words=[{'word':w,'start':i*.5,'end':i*.5+.4} for i,w in enumerate(scene['voice'].split())]
                for group in group_words(words):self.assertLessEqual(len(caption_layout(group['words'])),2)
    def test_each_new_topic_has_authored_projected_motion(self):
        for t in NEW:
            s=LocalScriptProvider().create(catalog()[t]['name']);assets=verify_assets(s['asset_manifest']);self.assertTrue(any(a.get('motion_paths') for a in assets.values()))
            art=CinematicArtwork(s['scenes'][1],2,8,assets);self.assertNotEqual(art.visual(.2,5).tobytes(),art.visual(3,5).tobytes())
    def test_missing_resource_cannot_fall_back_to_ocean(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'assets') as directory:
            p=Path(directory)/'manifest.json';p.write_text(json.dumps({'assets':[{'id':'bad','file':'assets/nonexistent-science-asset.jpg','sha256':'0'*64}]}))
            with self.assertRaises(ValueError):verify_assets(str(p.relative_to(ROOT)))
    def test_manifest_cannot_escape_asset_library(self):
        with self.assertRaises(ValueError):verify_assets('../outside.json')
if __name__=='__main__':unittest.main()
