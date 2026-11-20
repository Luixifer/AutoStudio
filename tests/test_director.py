import copy,json,tempfile,unittest,zipfile
from pathlib import Path
from PIL import Image
from scripts.director.project import SCHEMA,validate,extract_bundle,media_file
from scripts.director.engine import validate_words,ease_keys,scene_cache_key

class DirectorContractTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);Image.new('RGB',(640,360),'orange').save(self.root/'photo.jpg')
  self.p={'schema':SCHEMA,'title':'Ensayo de montaje','youtube_enabled':False,'format':'horizontal','fps':30,'voice':{'mode':'kokoro','voice':'em_alex'},'chapters':[{'id':'c1','scenes':[{'id':'s1','narration':'Una prueba con voz real.','media':{'kind':'image','path':'photo.jpg','rights':{'license':'original_user'}}}]}]}
 def tearDown(self):self.tmp.cleanup()
 def test_contract_accepts_media_and_order(self):self.assertEqual(validate(self.p,self.root),self.p)
 def test_unsupported_version(self):
  self.p['schema']='future';self.assertRaises(ValueError,validate,self.p,self.root)
 def test_youtube_disabled(self):
  self.p['youtube_enabled']=True;self.assertRaises(ValueError,validate,self.p,self.root)
 def test_rights_required(self):
  del self.p['chapters'][0]['scenes'][0]['media']['rights'];self.assertRaises(ValueError,validate,self.p,self.root)
 def test_duplicate_ids(self):
  self.p['chapters'][0]['scenes'].append(copy.deepcopy(self.p['chapters'][0]['scenes'][0]));self.assertRaises(ValueError,validate,self.p,self.root)
 def test_path_traversal(self):self.assertRaises(ValueError,media_file,self.root,'../photo.jpg',{'.jpg'})
 def test_symlink(self):
  (self.root/'alias.jpg').symlink_to(self.root/'photo.jpg');self.assertRaises(ValueError,media_file,self.root,'alias.jpg',{'.jpg'})
 def test_wrong_extension(self):self.assertRaises(ValueError,media_file,self.root,'photo.jpg',{'.mp4'})
 def test_no_remote_media(self):self.assertRaises(ValueError,media_file,self.root,'https://example.com/movie.mp4',{'.mp4'})
 def test_nan_camera(self):
  self.p['chapters'][0]['scenes'][0]['camera']={'keyframes':[{'at':0,'x':float('nan')},{'at':1}]};self.assertRaises(ValueError,validate,self.p,self.root)
 def test_out_of_order_keys(self):
  self.p['chapters'][0]['scenes'][0]['camera']={'keyframes':[{'at':1},{'at':0}]};self.assertRaises(ValueError,validate,self.p,self.root)
 def test_wrong_audio_mode(self):
  self.p['voice']={'mode':'paid-service'};self.assertRaises(ValueError,validate,self.p,self.root)
 def test_word_timings_checked(self):
  w=[{'word':'Hola','start':0,'end':.4}];self.assertEqual(validate_words(w,'Hola',1),w);self.assertRaises(ValueError,validate_words,w,'Adiós',1)
 def test_overlap_rejected(self):
  self.assertRaises(ValueError,validate_words,[{'word':'uno','start':0,'end':1},{'word':'dos','start':.2,'end':.4}],'uno dos',2)
 def test_words_beyond_audio(self):self.assertRaises(ValueError,validate_words,[{'word':'uno','start':0,'end':2}],'uno',1)
 def test_key_easing_has_endpoint_and_cosine(self):
  s=ease_keys([{'at':0,'zoom':1},{'at':1,'zoom':1.1}],'zoom',301);self.assertIn('cos(PI',s);self.assertIn('on/300',s)
 def test_cache_changes_with_media(self):
  s=self.p['chapters'][0]['scenes'][0];a=scene_cache_key(s,self.p,self.root);Image.new('RGB',(640,360),'blue').save(self.root/'photo.jpg');self.assertNotEqual(a,scene_cache_key(s,self.p,self.root))
 def test_scene_change_only_changes_own_cache(self):
  s=self.p['chapters'][0]['scenes'][0];a=scene_cache_key(s,self.p,self.root);self.p['title']='Nuevo título';self.assertEqual(a,scene_cache_key(s,self.p,self.root));s['narration']='Otra locución.';self.assertNotEqual(a,scene_cache_key(s,self.p,self.root))
 def test_safe_zip_import(self):
  z=self.root/'bundle.zip'
  with zipfile.ZipFile(z,'w') as f:f.writestr('project.json',json.dumps(self.p));f.write(self.root/'photo.jpg','photo.jpg')
  self.assertEqual(extract_bundle(z,self.root/'imported')['title'],self.p['title'])
 def test_zip_traversal_rejected_without_extraction(self):
  z=self.root/'bad.zip'
  with zipfile.ZipFile(z,'w') as f:f.writestr('../escaped','bad')
  self.assertRaises(ValueError,extract_bundle,z,self.root/'imported');self.assertFalse((self.root/'escaped').exists())
 def test_zip_duplicate_rejected(self):
  z=self.root/'bad.zip'
  with zipfile.ZipFile(z,'w') as f:f.writestr('project.json','{}');f.writestr('project.json','{}')
  self.assertRaises(ValueError,extract_bundle,z,self.root/'imported')
 def test_parallax_limits(self):
  self.p['chapters'][0]['scenes'][0]['media']['layers']=[{'path':'photo.jpg','from':[1,0]}];self.assertRaises(ValueError,validate,self.p,self.root)
