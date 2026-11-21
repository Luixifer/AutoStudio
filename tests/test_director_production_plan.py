import copy,json,tempfile,unittest
from pathlib import Path
from PIL import Image
from scripts.director.production_plan import readiness,compile_plan
from scripts.director.project import digest
ROOT=Path(__file__).resolve().parents[1]
class ProductionPlanTests(unittest.TestCase):
 def test_hessdalen_is_explicitly_blocked_and_does_not_invent_script_or_assets(self):
  path=ROOT/'content/projects/hessdalen/chapter01.plan.json';p=json.loads(path.read_text());errors=readiness(p,path.parent)
  self.assertEqual(len(p['shots']),30);self.assertEqual(len(p['blocks']),7);self.assertTrue(errors);self.assertFalse(p['script']['approved'])
  self.assertTrue(all(s['media']['path'] is None and s['start_phrase'] is None for s in p['shots']))
 def test_compile_keeps_approved_paragraph_and_requires_complete_phrase_coverage(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   for i,color in enumerate(('red','blue')):Image.new('RGB',(40,40),color).save(root/f'{i}.png')
   narration='Primer plano. Segundo plano.'
   shots=[{'id':f'p{i}','scene_id':'paragraph','start_phrase':phrase,'end_phrase':phrase,'classification':'recreation','media':{'kind':'image','path':f'{i}.png','rights':{'license':'own_creation','credit':'Owned fixture'}}} for i,phrase in enumerate(('Primer plano.','Segundo plano.'))]
   p={'schema':'autostudio-director/1','title':'Approved fixture','format':'horizontal','fps':30,'youtube_enabled':False,'chapters':[{'id':'chapter','scenes':[{'id':'paragraph','narration':narration}]}]}
   plan={'schema':'autostudio-production-plan/1','youtube_enabled':False,'shots':shots}
   result=compile_plan(plan,p,root);self.assertEqual(result['chapters'][0]['scenes'][0]['narration'],narration);self.assertNotIn('subshots',p['chapters'][0]['scenes'][0])
   (root/'project.json').write_text(json.dumps(result));plan['script']={'path':'project.json','approved':True,'sha256':digest(root/'project.json')};self.assertEqual(readiness(plan,root),[])
   broken=copy.deepcopy(plan);broken['shots'][1]['scene_id']='does-not-exist';self.assertTrue(readiness(broken,root))
   broken=copy.deepcopy(plan);broken['shots'][0]['end_phrase']='Segundo plano.';self.assertTrue(readiness(broken,root))
 def test_script_hash_and_path_must_match(self):
  with tempfile.TemporaryDirectory() as td:
   p={'schema':'autostudio-production-plan/1','script':{'path':'../outside.json','approved':True},'shots':[],'youtube_enabled':False}
   self.assertTrue(any('fuera' in e for e in readiness(p,td)))
