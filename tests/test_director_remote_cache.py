import json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from scripts.director.remote_cache import RemoteCache,restore_zip

class RemoteCacheSafetyTests(unittest.TestCase):
 def test_private_cache_roundtrip_omits_source_assets_and_credentials(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);out=root/'render';node=out/'visual-cache'/('a'*64);node.mkdir(parents=True);(node/'complete.json').write_text('{}');(node/'visual.mp4').write_bytes(b'qa-cache-signal');(out/'project.json').write_text('never-cache-source');(out/'token.txt').write_text('not-a-credential')
   uploaded=[];cache=RemoteCache('1'*32,{'id':5},root,'2'*32)
   def upload(release,path):uploaded.append(Path(path));return {}
   with patch('scripts.director.remote_cache.upload',side_effect=upload):cache.save(out);cache.save(out)
   self.assertTrue(cache.stats['saved']);self.assertEqual(len(uploaded),2)
   target=root/'restored';self.assertEqual(restore_zip(uploaded[0],target),2);self.assertFalse((target/'project.json').exists());self.assertFalse((target/'token.txt').exists())
 def test_rejects_traversal_and_unsupported_cache_content(self):
  for name in ('../secret','project.json','visual-cache/bad/visual.mp4','visual-cache/'+'a'*64+'/execute.py'):
   with self.subTest(name=name),tempfile.TemporaryDirectory() as td:
    source=Path(td)/'cache.zip'
    with zipfile.ZipFile(source,'w') as z:z.writestr(name,'invalid')
    self.assertRaises(ValueError,restore_zip,source,Path(td)/'out')
 def test_cache_disabled_without_project_identity(self):
  with tempfile.TemporaryDirectory() as td:
   cache=RemoteCache(None,{'id':1},td,'2'*32);cache.save(td);self.assertFalse(cache.stats['enabled']);self.assertFalse(cache.stats['saved'])
