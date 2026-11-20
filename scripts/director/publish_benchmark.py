"""Deliver a genuine Actions five-minute TECHNICAL benchmark, never Hessdalen."""
import json,os,shutil
from pathlib import Path
from scripts.director.cloud import api,upload
from scripts.director.project import digest

def main():
 if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='Luixifer/AutoStudio':raise RuntimeError('Genuine repository workflow only')
 run=os.environ['GITHUB_RUN_ID'];root=Path('reports/director-benchmark');root.mkdir(parents=True,exist_ok=True);render=root/'long/render';check={'run_id':run,'source_commit':os.environ['GITHUB_SHA'],'status':os.environ.get('DIRECTOR_BENCHMARK_STATUS'),'scope':'Repeated technical fixture; NOT Hessdalen, not an editorial documentary','physical_samsung_tested':False,'youtube_enabled':False};files=[]
 report=render/'validation.json'
 if check['status']=='success':
  qa=json.loads(report.read_text());video=render/'documental-REVISION.mp4'
  if not qa['passed'] or not qa['full_decode'] or digest(video)!=qa['sha256'] or not 290<=qa['duration']<=310:raise ValueError('Benchmark not actually verified')
  check['validation']=qa;target=root/'AutoStudio-Director-ensayo-5min-NO-HESSDALEN.mp4';shutil.copy2(video,target);files.append(target)
  for name in ['validation.json','captions.srt','timeline.json','input-audit.json']:
   source=render/name;target=root/name;shutil.copy2(source,target);files.append(target)
 for name in ['resources.json','benchmark.log']:
  path=root/name
  if path.is_file():files.append(path)
 summary=root/'benchmark-check.json';summary.write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n');files.append(summary)
 with api('/releases','POST',{'tag_name':'director-benchmark-'+run,'target_commitish':os.environ['GITHUB_SHA'],'name':'Director · ensayo técnico ~5 min · NO Hessdalen','draft':False,'prerelease':True,'body':'Material repetido de ensayo. No son escenas ni documental de Hessdalen. Sin aprobación artística. Estado: '+check['status']+' · https://github.com/Luixifer/AutoStudio/actions/runs/'+run}) as response:release=json.load(response)
 for path in files:upload(release,path)
 print('REAL_BENCHMARK_RELEASE',release['html_url'])
if __name__=='__main__':main()
