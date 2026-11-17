"""Publish real debug APK + sanitized test evidence to a separate managed Git branch."""
import hashlib,json,os,re,shutil,tempfile,zipfile
from pathlib import Path
from urllib.parse import urlsplit
from publish_result import ROOT,git
BRANCH='android-preview-04'
NAME='AutoStudio-Control-0.4.0-lab.apk'
def main():
    if os.environ.get('GITHUB_ACTIONS')!='true':raise RuntimeError('Only genuine Actions APK builds may be published.')
    repo=os.environ['GITHUB_REPOSITORY'];run=os.environ['GITHUB_RUN_ID'];commit=os.environ['GITHUB_SHA'];status=os.environ.get('AUTOSTUDIO_JOB_STATUS','failure')
    if ROOT!=Path(os.environ['GITHUB_WORKSPACE']).resolve():raise ValueError('Unexpected workspace.')
    origin=urlsplit(git('remote','get-url','origin',capture=True))
    if origin.hostname!='github.com' or origin.path.strip('/').removesuffix('.git').lower()!=repo.lower():raise ValueError('Unexpected origin.')
    out=ROOT/'build/android';apk=out/NAME;info=None
    if apk.is_file() and (out/'apk-info.json').is_file():
        info=json.loads((out/'apk-info.json').read_text())
        if info['source_commit']!=commit or info['github_run_id']!=run or info['worktree_dirty'] or info['sha256']!=hashlib.sha256(apk.read_bytes()).hexdigest():raise ValueError('APK provenance mismatch.')
        with zipfile.ZipFile(apk) as z:
            if not {'AndroidManifest.xml','classes.dex'}.issubset(z.namelist()) or any(p.endswith(('.keystore','.jks')) for p in z.namelist()):raise ValueError('Invalid APK or included signing key.')
    full=ROOT/'reports/android-qa/full/full.json';recovery=ROOT/'reports/android-qa/recovery/recovery.json';checked=False
    if status=='success':
        checked=info is not None and full.is_file() and recovery.is_file() and json.loads(full.read_text()).get('passed') and json.loads(recovery.read_text()).get('passed')
        if not checked:raise ValueError('Successful status without actual Android integration evidence.')
    attempt={'managed_by':'autostudio-android-lab','repository':repo,'github_run_id':run,'source_commit':commit,'status':status,'new_apk':info is not None,'android_emulator_cloud_roundtrip_passed':bool(checked),'physical_samsung_tested':False,'run_url':f'https://github.com/{repo}/actions/runs/{run}'}
    with tempfile.TemporaryDirectory(dir=os.environ.get('RUNNER_TEMP')) as directory:
        stage=Path(directory);(stage/'attempt.json').write_text(json.dumps(attempt,indent=2)+'\n')
        if info:
            for name in [NAME,'apk-info.json','SHA256SUMS']:shutil.copy2(out/name,stage/name)
            with zipfile.ZipFile(stage/'AutoStudio-Control-0.4.0-lab.zip','w',zipfile.ZIP_DEFLATED) as z:
                for name in [NAME,'SHA256SUMS']:z.write(stage/name,name)
        (stage/'reports').mkdir()
        for name in ['unit-tests.txt','android-build.txt','android-startup.txt','emulator.log','android-instrumentation.txt','android-recovery.txt']:
            f=ROOT/'reports'/name
            if f.is_file():
                text=f.read_text(errors='replace')[-100000:]
                text=re.sub(r'\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)\b','[REDACTED]',text)
                (stage/'reports'/name).write_text(text)
        if (ROOT/'reports/android-qa').is_dir():shutil.copytree(ROOT/'reports/android-qa',stage/'qa')
        exists=bool(git('ls-remote','--heads','origin','refs/heads/'+BRANCH,capture=True))
        if exists:
            git('fetch','--no-tags','origin','refs/heads/'+BRANCH);old=json.loads(git('show','FETCH_HEAD:attempt.json',capture=True))
            if old.get('managed_by')!='autostudio-android-lab':raise ValueError('Not an AutoStudio output branch.')
            git('switch','-c','android-output','FETCH_HEAD')
        else:git('switch','--orphan','android-output')
        for source in stage.iterdir():
            dest=ROOT/source.name
            if source.is_dir():shutil.copytree(source,dest,dirs_exist_ok=True)
            else:shutil.copy2(source,dest)
        state='APK compilada y recorrido real superado en emulador Android 15.' if checked else 'Este intento no ha completado la validación integral. Consulta attempt.json; un APK anterior no se considera nuevo.'
        (ROOT/'README.md').write_text(f'# AutoStudio Control LAB 0.4\n\n{state}\n\n[Descargar APK](https://github.com/{repo}/raw/refs/heads/{BRANCH}/{NAME}) · [ZIP alternativo](https://github.com/{repo}/raw/refs/heads/{BRANCH}/AutoStudio-Control-0.4.0-lab.zip)\n\n[Prueba real de Actions]({attempt["run_url"]}) · [Guía móvil](https://github.com/{repo}/blob/main/android/README.md)\n\nFirma de depuración. Credencial introducida por el usuario y cifrada en Android Keystore; no incluida en el APK. No se ha probado físicamente en Samsung. No hay publicación en YouTube ni APIs de IA de pago.\n')
        git('config','user.name','AutoStudio Actions');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
        paths=['attempt.json','README.md']+([NAME,'apk-info.json','SHA256SUMS','AutoStudio-Control-0.4.0-lab.zip'] if info else [])
        paths += [str(Path('reports')/p.name) for p in (stage/'reports').iterdir()]
        if (stage/'qa').exists():paths += [str(p.relative_to(stage)) for p in (stage/'qa').rglob('*') if p.is_file()]
        git('add','--',*paths);git('commit','-m',f'Android lab run {run} ({status})');git('push','origin','HEAD:refs/heads/'+BRANCH)
if __name__=='__main__':main()
