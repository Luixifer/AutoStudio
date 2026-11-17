"""Fixed three-topic acceptance test, not a general or mobile production queue.
Dispatches genuine workflows sequentially, downloads each MP4 and checks its identity.
"""
import hashlib,json,os,re,subprocess,time,urllib.request,urllib.error,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
from scripts.validate_video import inspect_video
from scripts.production import build_plan
TOPICS=['auroras','dna','volcanoes']

def main():
    repo=os.environ['GITHUB_REPOSITORY'];token=os.environ['GH_REVIEW_TOKEN'];source=os.environ['GITHUB_SHA'];out=ROOT/'reports/phase-a-review';out.mkdir(parents=True,exist_ok=True)
    summary={'schema':1,'managed_by':'autostudio-phase-a-review','repository':repo,'source_commit':source,'github_run_id':os.environ['GITHUB_RUN_ID'],'passed':False,'topics':[],'physical_samsung_tested':False,'youtube_published':False}
    def save():(out/'review.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    def get(url,authenticated=False,body=None):
        headers={'User-Agent':'AutoStudio-Phase-A-Review/0.4','Cache-Control':'no-cache'}
        if authenticated:headers.update(Authorization='Bearer '+token,Accept='application/vnd.github+json',**{'X-GitHub-Api-Version':'2022-11-28'})
        request=urllib.request.Request(url,headers=headers,data=json.dumps(body).encode() if body is not None else None,method='POST' if body is not None else 'GET')
        if body is not None:request.add_header('Content-Type','application/json')
        with urllib.request.urlopen(request,timeout=60) as r:return r.status,r.read(21*1024*1024)
    def api(path,body=None):
        status,data=get('https://api.github.com/repos/'+repo+path,True,body);return {} if status==204 else json.loads(data)
    catalog=json.loads((ROOT/'content/catalog.json').read_text());entries={e['id']:e for e in catalog['topics'] if e.get('published',True)}
    save()
    try:
        for topic_id in TOPICS:
            entry=entries[topic_id];identifier=uuid.uuid4().hex;row={'topic_id':topic_id,'topic':entry['name'],'request_id':identifier,'status':'dispatching'};summary['topics'].append(row);save()
            api('/actions/workflows/produce-short.yml/dispatches',{'ref':'main','inputs':{'request_id':identifier,'topic':entry['name']}})
            deadline=time.monotonic()+480;run=None
            while time.monotonic()<deadline:
                data=api('/actions/workflows/produce-short.yml/runs?event=workflow_dispatch&per_page=50')
                run=next((r for r in data['workflow_runs'] if r.get('display_title')=='AutoStudio · control · '+identifier),None)
                if run:
                    row.update(run_id=str(run['id']),run_url=run['html_url'],status=run['status']);save()
                    if run['status']=='completed':
                        if run['conclusion']!='success':raise RuntimeError('Actual production failed for '+topic_id+' at '+run['html_url'])
                        break
                time.sleep(8)
            else:raise TimeoutError('Production did not complete within eight minutes: '+topic_id)
            base='https://raw.githubusercontent.com/'+repo+'/video-preview/jobs/'+identifier+'/'
            result=None
            for i in range(12):
                try:result=json.loads(get(base+'result.json?check='+str(time.time_ns()))[1]);break
                except urllib.error.HTTPError as e:
                    if e.code!=404:raise
                    time.sleep(3)
            if result is None or result.get('request_id')!=identifier or result.get('run_id')!=str(run['id']) or result.get('topic_id')!=topic_id or result.get('status')!='completed' or result.get('source_commit')!=source:raise ValueError('Result is stale or belongs to another topic/run/source.')
            video=out/(topic_id+'.mp4');video.write_bytes(get(base+'short_ciencia_demo.mp4')[1]);validation=inspect_video(video)
            if not validation['passed'] or validation['sha256']!=result['video']['sha256']:raise ValueError('Downloaded actual MP4 did not pass validation.')
            story=json.loads(get(base+'story.json')[1]);plan=json.loads(get(base+'scene-plan.json')[1]);quality=json.loads(get(base+'quality.json')[1]);expected,expected_plan=build_plan(entry['name'],identifier)
            if [s['voice'] for s in story['scenes']]!=[s['voice'] for s in expected['scenes']]:raise ValueError('Different requested story was rendered.')
            if [s['media']['sha256'] for s in plan['scenes']]!=[s['media']['sha256'] for s in expected_plan['scenes']]:raise ValueError('Wrong illustrations were used.')
            if not quality.get('word_coverage_passed') or quality['max_words_per_caption']>3:raise ValueError('Subtitle checks failed.')
            folder=out/topic_id;folder.mkdir(exist_ok=True)
            for name,data in [('validation.json',validation),('scene-plan.json',plan),('quality.json',quality)]: (folder/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
            row.update(status='validated',video_url='https://github.com/'+repo+'/raw/refs/heads/video-preview/jobs/'+identifier+'/short_ciencia_demo.mp4',raw_video_url=base+'short_ciencia_demo.mp4',duration_seconds=validation['duration_seconds'],bytes=validation['bytes'],sha256=validation['sha256'],scene_count=len(plan['scenes']),word_count=quality['timed_words'],story_sha256=hashlib.sha256(' '.join(s['voice'] for s in story['scenes']).encode()).hexdigest(),asset_hashes=[s['media']['sha256'] for s in plan['scenes']]);save();print('REAL_TOPIC_MP4_VALIDATED',topic_id,identifier,validation['sha256'],flush=True)
        if len({r['story_sha256'] for r in summary['topics']})!=3:raise ValueError('Duplicate script.')
        for a,b in [(0,1),(0,2),(1,2)]:
            if set(summary['topics'][a]['asset_hashes']) & set(summary['topics'][b]['asset_hashes']):raise ValueError('Visual assets are shared across the three new themes.')
        summary['passed']=True;save()
    except Exception as error:summary['error']=type(error).__name__+': '+str(error);save();raise

if __name__=='__main__':main()
