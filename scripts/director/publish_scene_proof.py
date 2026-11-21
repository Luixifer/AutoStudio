"""Attach actual strict-scene QA documentary to this run's verified APK release."""
import json,os,shutil
from pathlib import Path
from scripts.director.cloud import get_json,upload
from scripts.director.project import digest

def main():
 run=os.environ['GITHUB_RUN_ID'];out=Path('reports/scene-proof/render');report=json.loads((out/'validation.json').read_text());qa=json.loads((out/'correspondence.json').read_text())
 if not report['passed'] or not qa['passed'] or len(qa['scenes'])!=5:raise ValueError('No se entrega un documental sin correspondencia comprobada')
 release=get_json('/releases/tags/director-check-'+run)
 for name in ('documental-REVISION.mp4','validation.json','correspondence.json','timeline.json','captions.srt','input-audit.json','SHA256SUMS'):
  src=out/name;target=out/('Director-2-five-scenes-NOT-HESSDALEN-'+name);shutil.copy2(src,target);upload(release,target)
 print('ACTUAL_FIVE_SCENE_MP4_SHA256',digest(out/'documental-REVISION.mp4'));print('ACTUAL_SECONDS',report['duration'])
if __name__=='__main__':main()
