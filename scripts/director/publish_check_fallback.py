"""Small, sanitized diagnostics/APK only in an isolated managed evidence branch.
Never places documentary MP4s, input packages, keys or credentials in Git.
"""
import json,os,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BRANCH='director-preview'
def git(*args,cwd=ROOT):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
def publish(error=None):
 if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='Luixifer/AutoStudio':raise RuntimeError('Genuine workflow only')
 run=os.environ['GITHUB_RUN_ID'];metadata={'managed_by':'autostudio-director-evaluation','run_id':run,'source_commit':os.environ['GITHUB_SHA'],'status':os.environ.get('DIRECTOR_CHECK_STATUS'),'release_delivery_error':str(error)[:500] if error else None,'physical_samsung_tested':False}
 with tempfile.TemporaryDirectory(dir=os.environ.get('RUNNER_TEMP')) as temp:
  tree=Path(temp)/'tree';exists=git('ls-remote','--heads','origin','refs/heads/'+BRANCH)
  if exists:
   git('fetch','--no-tags','origin','refs/heads/'+BRANCH)
   old=json.loads(git('show','FETCH_HEAD:latest.json'))
   if old.get('managed_by')!=metadata['managed_by']:raise ValueError('Unmanaged evidence branch')
   git('worktree','add','--detach',str(tree),'FETCH_HEAD')
  else:
   git('worktree','add','--detach',str(tree),'HEAD');git('switch','--orphan','director-output-'+run,cwd=tree)
  dest=tree/'runs'/run;dest.mkdir(parents=True,exist_ok=True)
  for p in (ROOT/'reports/director').glob('*'):
   if p.suffix not in ('.txt','.json','.png','.log'):continue
   if p.suffix in ('.txt','.json','.log'):
    text=p.read_text(errors='replace')[-300000:];text=re.sub(r'\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)\b','[REDACTED]',text);(dest/p.name).write_text(text)
   elif p.stat().st_size<5*1024*1024:shutil.copy2(p,dest/p.name)
  for name in ['AutoStudio-Director-0.1.0-lab.apk','apk-info.json','SHA256SUMS']:
   p=ROOT/'build/android'/name
   if p.is_file() and p.stat().st_size<2*1024*1024:shutil.copy2(p,dest/p.name)
  (tree/'latest.json').write_text(json.dumps(metadata,indent=2)+'\n');(dest/'attempt.json').write_text(json.dumps(metadata,indent=2)+'\n')
  git('config','user.name','AutoStudio Actions',cwd=tree);git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com',cwd=tree);git('add','--','latest.json','runs/'+run,cwd=tree);git('commit','-m','Director evaluation '+run,cwd=tree);git('push','origin','HEAD:refs/heads/'+BRANCH,cwd=tree)
  print('REAL_DIAGNOSTICS_BRANCH',BRANCH,'RUN',run)
if __name__=='__main__':publish()
