"""Real portable chapter round trip. Audio is a test tone, not voice approval."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_director_real as fixture_module
from scripts.director.project import FORMATS
from scripts.director.engine import produce
from scripts.director.chapters import split,package_render,assemble
class ChapterPortableTests(unittest.TestCase):
 def test_split_render_package_and_assemble(self):
  fixture=fixture_module.DirectorRealFFmpegTests();fixture.setUp()
  try:
   root=fixture.root;path=root/'project.json';path.write_text(json.dumps(fixture.p));folder=root/'portable';plan=split(path,folder)
   with patch.dict(FORMATS,{'horizontal':(320,180)}):
    produce(path,root/'render')
    for chapter in ('c1','c2'):package_render(path,root/'render',chapter,folder/('rendered-'+chapter+'.zip'))
    report=assemble(plan,folder,root/'assembled')
    self.assertTrue(report['passed']);self.assertAlmostEqual(report['duration'],3.6,delta=.1);self.assertEqual(report['caption_count'],3)
    # Same filename/JSON with different image bytes must invalidate a prior render.
    original=(root/'image.webp').read_bytes()
    from PIL import Image
    Image.new('RGB',(320,180),(190,40,80)).save(root/'image.webp')
    new_plan=split(path,root/'changed-input')
    self.assertNotEqual(json.loads(new_plan.read_text())['chapters'][0]['document_sha256'],json.loads(plan.read_text())['chapters'][0]['document_sha256'])
    self.assertRaisesRegex(ValueError,'recurso o renderizador cambió',package_render,path,root/'render','c1',root/'stale.zip')
    (root/'image.webp').write_bytes(original)
    # Preserve the source asset while rejecting a package from another edit.
    document=json.loads(plan.read_text());document['chapters'][0]['document_sha256']='0'*64;plan.write_text(json.dumps(document))
    self.assertRaises(ValueError,assemble,plan,folder,root/'rejected')
  finally:fixture.tearDown()
