"""Deliver a genuine Actions five-minute TECHNICAL benchmark, never Hessdalen."""
import json,os,shutil
from pathlib import Path
from scripts.director.cloud import api,upload,get_json
from scripts.director.project import digest

TARGET='director-check-44803232978'

def target_release():
 release=get_json('/releases/tags/'+TARGET)
 if release.get('draft') or release.get('tag_name')!=TARGET or 'Estado: success' not in release.get('body',''):raise ValueError('Expected the already verified Director evaluation release')
 return release

def preflight():
 run=os.environ['GITHUB_RUN_ID'];out=Path('reports/director-benchmark');out.mkdir(parents=True,exist_ok=True);path=out/('benchmark-preparing-'+run+'.json');path.write_text(json.dumps({'status':'preparing, NOT a completed render','run_id':run,'source_commit':os.environ['GITHUB_SHA'],'youtube_enabled':False})+'\n');upload(target_release(),path);print('Existing release accepts benchmark delivery with current permissions')

def main():
 if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='Luixifer/AutoStudio':raise RuntimeError('Genuine repository workflow only')
 run=os.environ['GITHUB_RUN_ID'];root=Path('reports/director-benchmark');root.mkdir(parents=True,exist_ok=True);render=root/'long/render';check={'run_id':run,'source_commit':os.environ['GITHUB_SHA'],'status':os.environ.get('DIRECTOR_BENCHMARK_STATUS'),'scope':'Repeated technical fixture; NOT Hessdalen, not an editorial documentary','physical_samsung_tested':False,'youtube_enabled':False};files=[]
 report=render/'validation.json'
 if check['status']=='success':
  qa=json.loads(report.read_text());video=render/'documental-REVISION.mp4'
  if not qa['passed'] or not qa['full_decode'] or digest(video)!=qa['sha256'] or not 290<=qa['duration']<=310:raise ValueError('Benchmark not actually verified')
  check['validation']=qa;target=root/('AutoStudio-Director-ensayo-5min-NO-HESSDALEN-'+run+'.mp4');shutil.copy2(video,target);files.append(target)
  for name in ['validation.json','captions.srt','timeline.json','input-audit.json']:
   source=render/name;target=root/name;shutil.copy2(source,target);files.append(target)
 for name in ['resources.json','benchmark.log','setup.log']:
  path=root/name
  if path.is_file():files.append(path)
 summary=root/'benchmark-check.json';summary.write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n');files.append(summary)
 release=target_release()
 for path in files:
  if path.suffix!='.mp4':
   renamed=path.with_name('benchmark-'+run+'-'+path.name);shutil.copy2(path,renamed);path=renamed
  upload(release,path)
 print('REAL_BENCHMARK_RELEASE',release['html_url'])
if __name__=='__main__':
 import sys
 preflight() if '--preflight' in sys.argv else main()
