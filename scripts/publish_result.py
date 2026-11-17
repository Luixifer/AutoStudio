"""Publish a real Actions attempt via Git, not a paid service/API.
Only runs inside GitHub Actions; writes the managed video-preview branch, never main.
"""
import hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
BRANCH='video-preview'
FILES=['short_ciencia_demo.mp4','metadata.json','validation.json','captions.srt','SHA256SUMS']

def git(*args,capture=False,check=True):
    p=subprocess.run(['git',*args],cwd=ROOT,text=True,capture_output=capture,check=check)
    return p.stdout.strip() if capture else p

def verified_bundle(latest,repository,run_id,source_commit):
    directory=Path(json.loads(latest.read_text())['directory']).resolve()
    if not directory.is_relative_to((ROOT/'output').resolve()):raise ValueError('Output escapes the render directory.')
    metadata=json.loads((directory/'metadata.json').read_text());report=json.loads((directory/'validation.json').read_text());execution=metadata.get('execution',{})
    if metadata.get('managed_by')!='autostudio-mvp' or execution.get('context')!='github-actions':raise ValueError('Not a real Actions render.')
    if execution.get('github_repository')!=repository or execution.get('github_run_id')!=run_id or execution.get('git',{}).get('commit')!=source_commit:raise ValueError('Stale run or source commit; refusing misleading publication.')
    video=directory/'short_ciencia_demo.mp4'
    if not report.get('passed') or report.get('sha256')!=hashlib.sha256(video.read_bytes()).hexdigest():raise ValueError('MP4 did not pass validation, or its bytes changed.')
    if video.stat().st_size>20*1024*1024:raise ValueError('MP4 exceeds repository-preview budget.')
    if not all((directory/name).is_file() for name in FILES):raise ValueError('Incomplete output bundle.')
    return directory

def main():
    if os.environ.get('GITHUB_ACTIONS')!='true':raise RuntimeError('This publisher only runs in GitHub Actions. It must not relabel a Cloud/local test as Actions.')
    repo=os.environ['GITHUB_REPOSITORY'];run=os.environ['GITHUB_RUN_ID'];commit=os.environ['GITHUB_SHA'];workspace=Path(os.environ['GITHUB_WORKSPACE']).resolve()
    if workspace!=ROOT:raise RuntimeError('Unexpected Actions checkout directory.')
    remote=urlsplit(git('remote','get-url','origin',capture=True))
    if remote.hostname!='github.com' or remote.path.removeprefix('/').removesuffix('.git').lower()!=repo.lower():raise RuntimeError('Unexpected repository origin.')
    run_url=f'https://github.com/{repo}/actions/runs/{run}';status=os.environ.get('AUTOSTUDIO_JOB_STATUS','failure');error=None;bundle=None
    if status=='success':
        try:bundle=verified_bundle(ROOT/'output/latest.json',repo,run,commit)
        except Exception as exc:error=str(exc);status='failure'
    attempt={'managed_by':'autostudio-mvp','github_repository':repo,'github_run_id':run,'github_run_url':run_url,'source_commit':commit,'status_before_publication':status,'new_validated_video':bundle is not None,'error':error,'youtube_publication':'disabled'}
    with tempfile.TemporaryDirectory(dir=os.environ.get('RUNNER_TEMP')) as temp:
        stage=Path(temp)
        (stage/'attempt.json').write_text(json.dumps(attempt,ensure_ascii=False,indent=2)+'\n')
        if bundle:
            for name in FILES:shutil.copy2(bundle/name,stage/name)
        (stage/'logs').mkdir()
        for name in ['unit-tests.txt','render.log']:
            path=ROOT/'reports'/name
            if path.is_file():(stage/'logs'/name).write_text(path.read_text(errors='replace')[-100000:])
        # Refuse to replace a user-owned branch. No force pushes or main changes.
        exists=bool(git('ls-remote','--heads','origin','refs/heads/'+BRANCH,capture=True))
        if exists:
            git('fetch','--no-tags','origin','refs/heads/'+BRANCH)
            old=json.loads(git('show','FETCH_HEAD:attempt.json',capture=True))
            if old.get('managed_by')!='autostudio-mvp' or old.get('github_repository','').lower()!=repo.lower():raise RuntimeError('Existing preview branch is not managed by AutoStudio.')
            git('switch','-c',BRANCH,'FETCH_HEAD')
        else:git('switch','--orphan',BRANCH)
        for name in ['attempt.json',*FILES]:
            if (stage/name).is_file():shutil.copy2(stage/name,ROOT/name)
        (ROOT/'logs').mkdir(exist_ok=True)
        for path in (stage/'logs').glob('*'):shutil.copy2(path,ROOT/'logs'/path.name)
        download=f'https://github.com/{repo}/raw/refs/heads/{BRANCH}/short_ciencia_demo.mp4'
        note='Vídeo nuevo generado y validado en esta ejecución.' if bundle else 'Este intento falló. Si existe un MP4 anterior, no corresponde a este intento.'
        readme=f'# AutoStudio — resultado de prueba\n\n{note}\n\n[Ejecución real de GitHub Actions]({run_url})\n\n[Descargar MP4 para móvil]({download})\n\nConsulta `attempt.json`, `metadata.json`, `validation.json` y `SHA256SUMS`. Los esquemas son ilustraciones originales, la voz es sintética y la publicación en YouTube está desactivada. Esta rama contiene resultados; el código está en `main`.\n'
        (ROOT/'README.md').write_text(readme)
        git('config','user.name','AutoStudio Actions');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
        paths=['attempt.json','README.md']+[name for name in FILES if (stage/name).is_file()]+[str(Path('logs')/p.name) for p in (stage/'logs').glob('*')]
        git('add','--',*paths);git('commit','-m',f'Record real AutoStudio run {run} ({status})');git('push','origin','HEAD:refs/heads/'+BRANCH)
    summary=os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a') as stream:stream.write(f'## AutoStudio\n\n{note}\n\n[Descargar vídeo]({download}) · [Resultado e informes](https://github.com/{repo}/tree/{BRANCH})\n')
    if error:raise RuntimeError(error)
if __name__=='__main__':main()
