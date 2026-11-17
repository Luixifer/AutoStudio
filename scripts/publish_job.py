"""Publish one correlated production result; never substitute another request's MP4."""
import hashlib,json,os,shutil,tempfile
from pathlib import Path
from urllib.parse import urlsplit
if __package__:
    from .publish_result import ROOT,FILES,git,verified_bundle
    from .production import request_id
else:
    from publish_result import ROOT,FILES,git,verified_bundle
    from production import request_id

def make_result(identifier,run,commit,repository,status,bundle=None):
    request_id(identifier)
    result={'schema':1,'request_id':identifier,'run_id':str(run),'source_commit':commit,'repository':repository,'status':status,'youtube_published':False,'run_url':f'https://github.com/{repository}/actions/runs/{run}'}
    if bundle:
        meta=json.loads((bundle/'metadata.json').read_text());validation=json.loads((bundle/'validation.json').read_text())
        if meta.get('production',{}).get('request_id')!=identifier:raise ValueError('Production request does not match the rendered MP4.')
        result.update(topic=meta['production']['topic'],title=meta['title'],video={'file':'short_ciencia_demo.mp4','sha256':validation['sha256'],'bytes':validation['bytes'],'duration_seconds':validation['duration_seconds'],'width':720,'height':1280},scene_plan='scene-plan.json')
    else:result['message']='La generación no se completó. Revisa los registros de esta ejecución; no se mostrará otro vídeo como resultado.'
    return result

def main():
    if os.environ.get('GITHUB_ACTIONS')!='true':raise RuntimeError('Only actual Actions results can be published.')
    identifier=request_id(os.environ['AUTOSTUDIO_REQUEST_ID']);run=os.environ['GITHUB_RUN_ID'];commit=os.environ['GITHUB_SHA'];repo=os.environ['GITHUB_REPOSITORY']
    if Path(os.environ['GITHUB_WORKSPACE']).resolve()!=ROOT:raise ValueError('Unexpected checkout.')
    origin=urlsplit(git('remote','get-url','origin',capture=True))
    if origin.hostname!='github.com' or origin.path.strip('/').removesuffix('.git').lower()!=repo.lower():raise ValueError('Unexpected Git remote.')
    status=os.environ.get('AUTOSTUDIO_JOB_STATUS','failure');bundle=None
    if status=='success':bundle=verified_bundle(ROOT/'output/latest.json',repo,run,commit)
    result=make_result(identifier,run,commit,repo,'completed' if bundle else 'failed',bundle)
    with tempfile.TemporaryDirectory(dir=os.environ.get('RUNNER_TEMP')) as directory:
        stage=Path(directory)
        (stage/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        if bundle:
            for name in FILES+['scene-plan.json','story.json']:shutil.copy2(bundle/name,stage/name)
        (stage/'logs').mkdir()
        for name in ['unit-tests.txt','render.log']:
            source=ROOT/'reports'/name
            if source.is_file():(stage/'logs'/name).write_text(source.read_text(errors='replace')[-100000:])
        git('fetch','--no-tags','origin','refs/heads/video-preview')
        marker=json.loads(git('show','FETCH_HEAD:attempt.json',capture=True))
        if marker.get('managed_by')!='autostudio-mvp':raise ValueError('Output branch is not managed by AutoStudio.')
        old=git('cat-file','-e',f'FETCH_HEAD:jobs/{identifier}/result.json',check=False)
        if old.returncode==0:raise ValueError('Request already published. Refusing to overwrite immutable result.')
        git('switch','-c','production-output','FETCH_HEAD')
        target=ROOT/'jobs'/identifier;shutil.copytree(stage,target)
        index=ROOT/'jobs/index.json';items=json.loads(index.read_text()) if index.exists() else []
        items=[result]+items;index.write_text(json.dumps(items[:100],ensure_ascii=False,indent=2)+'\n')
        git('config','user.name','AutoStudio Actions');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
        git('add','--',str(target.relative_to(ROOT)),'jobs/index.json');git('commit','-m',f'Publish production {identifier} ({result["status"]})');git('push','origin','HEAD:refs/heads/video-preview')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(f'### AutoStudio\nSolicitud `{identifier}`: {result["status"]}\n\n[Resultado](https://github.com/{repo}/tree/video-preview/jobs/{identifier})\n')
if __name__=='__main__':main()
