"""Retrieve previous failed Actions logs using only this runner's authorization."""
import argparse,io,json,re,urllib.error,urllib.request,zipfile
from pathlib import Path
from scripts.director.cloud import api,NoRedirect

def fetch(run,out):
 try:
  try:r=api('/actions/runs/'+str(int(run))+'/logs')
  except urllib.error.HTTPError as e:
   if e.code!=302:raise
   u=e.headers['Location']
   from urllib.parse import urlparse
   p=urlparse(u)
   if p.scheme!='https' or not (p.hostname or '').endswith(('.blob.core.windows.net','.githubusercontent.com')):raise ValueError('Logs redirect not official')
   r=urllib.request.urlopen(u,timeout=120)
  with r:raw=r.read(16*1024*1024)
  z=zipfile.ZipFile(io.BytesIO(raw));parts=[]
  for name in z.namelist():
   if z.getinfo(name).file_size>2*1024*1024:continue
   s=z.read(name).decode(errors='replace')
   # Never print a raw runner credential from any legacy log.
   s=re.sub(r'\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)\b','[REDACTED]',s)
   parts.append(name+'\n'+s[-100000:])
  Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text('\n'.join(parts)[-1500000:]);print('Previous logs saved',run)
 except Exception as e:
  Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text('Unable to retrieve official logs: '+str(e));print('Previous logs unavailable:',type(e).__name__)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run',type=int);p.add_argument('--out',type=Path,required=True);a=p.parse_args();fetch(a.run,a.out)
