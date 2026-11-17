"""Read only requested Actions startup logs on the runner; publish sanitized diagnostics."""
import io,json,os,re,subprocess,urllib.request,urllib.error,zipfile
from pathlib import Path
REPO=os.environ['GITHUB_REPOSITORY'];TOKEN=os.environ['GH_DIAGNOSTIC_TOKEN'];ROOT=Path.cwd();OUT=ROOT/'reports/android-diagnostics';OUT.mkdir(parents=True,exist_ok=True)
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
opener=urllib.request.build_opener(NoRedirect)
ids=os.environ.get('DIAGNOSTIC_RUN_IDS','').split(',')
summary=[]
for run in ids:
    if not re.fullmatch(r'\d{8,20}',run):raise ValueError('Invalid diagnostic run ID')
    request=urllib.request.Request(f'https://api.github.com/repos/{REPO}/actions/runs/{run}/logs',headers={'Authorization':'Bearer '+TOKEN,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'AutoStudio-Diagnostics'})
    try:
        response=opener.open(request,timeout=30);data=response.read(20*1024*1024)
    except urllib.error.HTTPError as e:
        if e.code!=302:raise
        location=e.headers['Location']
        if not location.startswith('https://'):raise ValueError('Unsafe log download')
        with urllib.request.urlopen(location,timeout=60) as response:data=response.read(20*1024*1024)
    found=[]
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for entry in archive.infolist():
            if 'Iniciar Android 15' not in entry.filename:continue
            text=archive.read(entry).decode('utf-8',errors='replace').replace(TOKEN,'[REDACTED]')
            text=re.sub(r'\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)\b','[REDACTED]',text)
            (OUT/(run+'-startup.txt')).write_text(text);found.append(entry.filename)
    summary.append({'run_id':run,'matched_startup_logs':found})
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
subprocess.run(['git','fetch','--no-tags','origin','refs/heads/android-preview'],check=True)
# Keep diagnostics in the existing managed output branch, without changing any APK.
marker=json.loads(git('show','FETCH_HEAD:attempt.json'))
if marker.get('managed_by')!='autostudio-android-lab':raise ValueError('Unknown output branch')
files={p.name:p.read_bytes() for p in OUT.iterdir()}
subprocess.run(['git','switch','-c','android-diagnostics-output','FETCH_HEAD'],check=True)
dest=ROOT/'diagnostics';dest.mkdir(exist_ok=True)
for name,data in files.items():(dest/name).write_bytes(data)
subprocess.run(['git','config','user.name','AutoStudio Diagnostics'],check=True);subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],check=True)
subprocess.run(['git','add','--',*[str(Path('diagnostics')/n) for n in files]],check=True)
subprocess.run(['git','commit','-m','Record sanitized Android startup diagnostics'],check=True);subprocess.run(['git','push','origin','HEAD:refs/heads/android-preview'],check=True)
print('Published sanitized startup logs for',','.join(ids))
