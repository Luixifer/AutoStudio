"""Publish bounded QA evidence, never an unverified MP4 or a private API credential."""
import json,os,subprocess,tempfile,shutil
from pathlib import Path
from publish_result import ROOT,git
BRANCH='phase-a-review'
def main():
 if os.environ.get('GITHUB_ACTIONS')!='true':raise RuntimeError('Actions evidence required.')
 report=ROOT/'reports/phase-a-review/review.json'
 data=json.loads(report.read_text()) if report.exists() else {'managed_by':'autostudio-phase-a-review','passed':False,'topics':[]}
 data['job_status']=os.environ.get('AUTOSTUDIO_JOB_STATUS','failure');data['review_run_url']=f'https://github.com/{os.environ["GITHUB_REPOSITORY"]}/actions/runs/{os.environ["GITHUB_RUN_ID"]}'
 if data.get('source_commit')!=os.environ['GITHUB_SHA'] or data.get('github_run_id')!=os.environ['GITHUB_RUN_ID']:raise ValueError('Unexpected review source/run.')
 with tempfile.TemporaryDirectory(dir=os.environ.get('RUNNER_TEMP')) as directory:
  stage=Path(directory);(stage/'review.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
  for topic in ['auroras','dna','volcanoes']:
   folder=ROOT/'reports/phase-a-review'/topic
   if folder.is_dir():shutil.copytree(folder,stage/topic)
  exists=bool(git('ls-remote','--heads','origin','refs/heads/'+BRANCH,capture=True))
  if exists:
   git('fetch','origin','refs/heads/'+BRANCH);old=json.loads(git('show','FETCH_HEAD:review.json',capture=True))
   if old.get('managed_by')!='autostudio-phase-a-review':raise ValueError('Unmanaged review branch.')
   git('switch','-c','phase-a-output','FETCH_HEAD')
  else:git('switch','--orphan','phase-a-output')
  for p in stage.iterdir():
   dest=ROOT/p.name
   if p.is_dir():shutil.copytree(p,dest,dirs_exist_ok=True)
   else:shutil.copy2(p,dest)
  lines=['# AutoStudio 0.4 — tres Shorts reales de la Fase A','',f'Estado de la revisión: {data.get("passed",False)}',f'[Ejecución]({data["review_run_url"]})','']
  for row in data.get('topics',[]):
   if row.get('status')=='validated':lines.append(f'- [{row["topic"]}: descargar MP4]({row["video_url"]}) · {row["duration_seconds"]} s · [Actions]({row["run_url"]})')
  lines+=['','No son filmaciones reales ni fotorrealismo aprobado. Sin APIs de pago ni publicación en YouTube.'];(ROOT/'README.md').write_text('\n'.join(lines)+'\n')
  paths=['review.json','README.md']+[str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file() and p.name!='review.json']
  git('config','user.name','AutoStudio Review');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com');git('add','--',*paths);git('commit','-m',f'Record three-topic review {os.environ["GITHUB_RUN_ID"]}');git('push','origin','HEAD:refs/heads/'+BRANCH)
if __name__=='__main__':main()
