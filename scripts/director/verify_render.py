"""Independently recover QA for an already-rendered MP4; never regenerate it."""
import argparse,json
from pathlib import Path
from scripts.director.project import load,digest,FORMATS
from scripts.director.correspondence import inspect_correspondence
from scripts.director.validate import inspect
from scripts.director.engine import atomic_json

def verify(project,out):
 project=Path(project).resolve();out=Path(out);p=load(project);timeline=json.loads((out/'timeline.json').read_text());scenes=[s for c in p['chapters'] for s in c['scenes']]
 if timeline['project_sha256']!=digest(project) or [s['id'] for s in scenes]!=[s['id'] for s in timeline['scenes']]:raise ValueError('El guion y el render no corresponden')
 for original,actual in zip(scenes,timeline['scenes']):
  if original['narration']!=actual['original_text'] or original['media']['path']!=actual['media_path']:raise ValueError('Una asociación cambió después de renderizar')
 qa=inspect_correspondence(out/'documental-REVISION.mp4',timeline['scenes'],out/'scene-cache',p.get('fps',30),timeline['cues'],project.parent)
 report=inspect(out/'documental-REVISION.mp4',FORMATS[p['format']],p.get('fps',30),timeline['duration'],timeline['cues']);report['correspondence']=qa;report['passed']&=qa['passed'];report['recovery_scope']='Independent full decode and scene correspondence of an existing MP4; no regeneration; original failed run is not relabelled'
 atomic_json(out/'recovered-verification.json',report);atomic_json(out/'recovered-correspondence.json',qa)
 if not report['passed']:raise RuntimeError(str(report))
 print(json.dumps({'passed':True,'duration':report['duration'],'sha256':report['sha256'],'scenes':len(qa['scenes'])}))
 return report
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('project',type=Path);parser.add_argument('--out',type=Path,required=True);a=parser.parse_args();verify(a.project,a.out)
