"""Publish only public technical test fixtures and debug APK; no user media."""
import json,os
from pathlib import Path
from scripts.director.cloud import api,upload
from scripts.director.project import digest

def main():
 if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='Luixifer/AutoStudio':raise RuntimeError('Genuine authorized Actions only')
 run=os.environ['GITHUB_RUN_ID'];status=os.environ['DIRECTOR_CHECK_STATUS'];out=Path('reports/director');out.mkdir(parents=True,exist_ok=True)
 check={'run_id':run,'source_commit':os.environ['GITHUB_SHA'],'job_status':status,'physical_samsung_tested':False,'hessdalen_produced':False,'youtube_enabled':False}
 qa=out/'roundtrip.json'
 if qa.is_file() and qa.stat().st_size:
  try:check['android_emulator']=json.loads(qa.read_text())
  except json.JSONDecodeError:check['qa_error']='Invalid emulator JSON; not treated as success'
 recovery=out/'recovery.json'
 if recovery.is_file() and recovery.stat().st_size:
  try:check['android_recovery']=json.loads(recovery.read_text())
  except json.JSONDecodeError:check['recovery_error']='Invalid recovery report'
 if status=='success' and not (check.get('android_emulator',{}).get('passed') and check.get('android_recovery',{}).get('passed')):raise RuntimeError('Success without real emulator and recovery evidence')
 apk=Path('build/android/AutoStudio-Director-0.1.0-lab.apk')
 if apk.is_file():
  info=json.loads(Path('build/android/apk-info.json').read_text())
  if info['sha256']!=digest(apk) or info['source_commit']!=os.environ['GITHUB_SHA'] or info['github_run_id']!=run:raise ValueError('APK provenance mismatch')
  check['apk']=info
 (out/'check.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n')
 body='Evaluación técnica, NO documental Hessdalen. Estado: '+status+'. Sin prueba física Samsung. No aprobación artística. Ejecución: https://github.com/Luixifer/AutoStudio/actions/runs/'+run
 with api('/releases','POST',{'tag_name':'director-check-'+run,'target_commitish':os.environ['GITHUB_SHA'],'name':'AutoStudio Director LAB · '+run,'draft':False,'prerelease':True,'body':body}) as r:release=json.load(r)
 paths=[*(p for p in out.iterdir() if p.is_file()),*(p for p in [apk,Path('build/android/apk-info.json'),Path('build/android/SHA256SUMS')] if p.is_file())]
 for path in paths:upload(release,path)
 print('REAL_EVALUATION_RELEASE',release['html_url'])
if __name__=='__main__':
 try:main()
 except Exception as error:
  from scripts.director.publish_check_fallback import publish
  publish(error)
  raise
 else:
  from scripts.director.publish_check_fallback import publish
  publish()
