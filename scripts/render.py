#!/usr/bin/env python3
"""AutoStudio: CPU diagrams + local eSpeak NG + FFmpeg. No paid API or YouTube upload."""
import argparse,datetime,hashlib,json,math,os,platform,re,shutil,subprocess,sys,time,uuid,wave
from pathlib import Path
from urllib.parse import urlsplit
if __package__:
    from .artwork import SceneArtwork
    from .narration import synthesize
    from .validate_video import inspect_video
else:
    from artwork import SceneArtwork
    from narration import synthesize
    from validate_video import inspect_video
ROOT=Path(__file__).resolve().parents[1]
FPS=25

def load_story(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data,dict) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,39}',data.get('id','')):raise ValueError('Invalid story ID.')
    if not isinstance(data.get('title'),str) or not 1<=len(data['title'])<=140:raise ValueError('Invalid story title.')
    if data.get('language')!='es':raise ValueError('This MVP has only verified the Spanish voice.')
    scenes=data.get('scenes');sources=data.get('sources')
    if not isinstance(scenes,list) or not 1<=len(scenes)<=8:raise ValueError('Use one to eight authored scenes.')
    if not isinstance(sources,list) or not sources:raise ValueError('Provide editorial references; do not invent research.')
    for source in sources:
        if not isinstance(source,dict):raise ValueError('Sources require explicit provenance.')
        url=urlsplit(source.get('url',''))
        if url.scheme!='https' or not url.hostname or url.username or url.password:raise ValueError('Sources must be HTTPS references without credentials.')
    for s in scenes:
        if not isinstance(s,dict) or s.get('visual') not in {'ocean','vent','microbes'}:raise ValueError('Unknown schematic.')
        for key,limit in [('title',120),('caption',180),('voice',4000)]:
            if not isinstance(s.get(key),str) or not s[key].strip() or len(s[key])>limit:raise ValueError('Invalid '+key)
    return data

def cues_for(text,duration):
    words=text.split();chunks=[' '.join(words[i:i+9]) for i in range(0,len(words),9)]
    weights=[len(c)+5*sum(c.count(p) for p in '.,;:') for c in chunks];total=sum(weights);cursor=.10;end=max(.11,duration-.20);span=end-cursor;cues=[]
    for chunk,weight in zip(chunks,weights):
        next_time=cursor+span*weight/total;cues.append({'start':cursor,'end':next_time,'text':chunk});cursor=next_time
    return cues

def srt_time(seconds):
    ms=round(seconds*1000);hours,ms=divmod(ms,3600000);minutes,ms=divmod(ms,60000);secs,ms=divmod(ms,1000)
    return f'{hours:02}:{minutes:02}:{secs:02},{ms:03}'

def git_info():
    def value(*args):
        r=subprocess.run(['git',*args],cwd=ROOT,text=True,capture_output=True);return r.stdout.strip() if r.returncode==0 else None
    return {'commit':value('rev-parse','HEAD'),'worktree_dirty':bool(value('status','--porcelain'))}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--script',type=Path,default=ROOT/'scripts/ocean.json');parser.add_argument('--out',type=Path,default=ROOT/'output');args=parser.parse_args()
    for tool in ['ffmpeg','ffprobe']:
        if not shutil.which(tool):raise RuntimeError('Missing required free program: '+tool)
    data=load_story(args.script);stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=args.out/(data['id']+'-'+stamp+'-'+uuid.uuid4().hex[:6]);out.mkdir(parents=True)
    started=time.monotonic();segments=[];scene_info=[];all_cues=[];samples_per_scene=[];total_frames=0;voice_info=[]
    for number,scene in enumerate(data['scenes'],1):
        wav=out/f'scene_{number:02d}.wav';voice_info.append(synthesize(scene['voice'],wav))
        with wave.open(str(wav),'rb') as audio:
            if audio.getsampwidth()!=2 or audio.getnchannels()!=1:raise ValueError('Narrator must return 16-bit mono WAV.')
            rate=audio.getframerate();raw=audio.readframes(audio.getnframes());voice_duration=audio.getnframes()/rate
        count=math.ceil((voice_duration+.45)*FPS);duration=count/FPS
        if (total_frames+count)/FPS>=150:raise ValueError('Narration exceeds the 150-second MVP render budget.')
        cues=cues_for(scene['voice'],voice_duration);art=SceneArtwork(scene,number,len(data['scenes']));mp4=out/f'scene_{number:02d}.mp4';log=out/f'scene_{number:02d}_encoder.log'
        cmd=['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','22','-profile:v','high','-level:v','3.1','-pix_fmt','yuv420p','-threads','2',str(mp4)]
        with log.open('wb') as errors:
            process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=errors)
            try:
                cue_index=0
                for frame in range(count):
                    t=frame/FPS
                    while cue_index+1<len(cues) and t>=cues[cue_index]['end']:cue_index+=1
                    subtitle=cues[cue_index]['text'] if t>=cues[0]['start'] and t<=cues[-1]['end'] else ''
                    image=art.frame(t,duration,subtitle)
                    if frame==count//2:image.save(out/f'preview_{number:02d}.jpg',quality=90)
                    process.stdin.write(image.tobytes())
                process.stdin.close();code=process.wait(timeout=180)
                if code:raise RuntimeError(f'FFmpeg failed for scene {number}; see {log}.')
            except BaseException:
                process.kill();process.wait();raise
        offset=total_frames/FPS
        for cue in cues:all_cues.append({**cue,'start':offset+cue['start'],'end':offset+cue['end']})
        target_samples=round(duration*rate);padding=target_samples-len(raw)//2
        samples_per_scene.append((rate,raw+b'\0\0'*max(0,padding)));scene_info.append({'scene':number,'visual':scene['visual'],'voice_seconds':voice_duration,'video_seconds':duration,'frames':count,'narration':scene['voice']});segments.append(mp4);total_frames+=count
    if len({r for r,_ in samples_per_scene})!=1:raise ValueError('Narration sample rate changed between scenes.')
    voice=out/'narration.wav'
    with wave.open(str(voice),'wb') as output:
        output.setnchannels(1);output.setsampwidth(2);output.setframerate(samples_per_scene[0][0]);output.writeframes(b''.join(raw for _,raw in samples_per_scene))
    listing=out/'concat.txt';listing.write_text(''.join("file '"+p.name+"'\n" for p in segments))
    final=out/'short_ciencia_demo.mp4'
    cmd=['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-i',str(voice),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','128k','-ar','48000','-ac','2','-af','apad,loudnorm=I=-16:LRA=7:TP=-1.5','-t',str(total_frames/FPS),'-movflags','+faststart',str(final)]
    subprocess.run(cmd,check=True,timeout=240)
    (out/'captions.srt').write_text('\n'.join(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n" for i,c in enumerate(all_cues,1)),encoding='utf-8')
    github=os.environ.get('GITHUB_ACTIONS')=='true';repo=os.environ.get('GITHUB_REPOSITORY');run_id=os.environ.get('GITHUB_RUN_ID')
    metadata={'schema':1,'managed_by':'autostudio-mvp','version':'0.2.0','title':data['title'],'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'execution':{'context':'github-actions' if github else 'standalone-python','github_repository':repo if github else None,'github_run_id':run_id if github else None,'github_run_url':f'https://github.com/{repo}/actions/runs/{run_id}' if github and repo and run_id else None,'git':git_info(),'python':platform.python_version(),'platform':platform.platform(),'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]},'video':{'frames':total_frames,'fps':FPS,'duration_seconds':total_frames/FPS,'size':[720,1280]},'narration':voice_info,'subtitle_timing':'Approximate chunk timing from text lengths, not forced alignment.','scenes':scene_info,'sources':data['sources'],'source_verification':'Provided editorial references, not retrieved by the renderer; manual verification required before publication.','visual_disclosure':'Original animated diagrams, not real underwater footage or photorealistic AI video.','paid_api_requests':0,'youtube_publication':'disabled','elapsed_render_seconds':round(time.monotonic()-started,2),'script_sha256':hashlib.sha256(args.script.read_bytes()).hexdigest(),'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'scripts').glob('*.py')}}
    (out/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=inspect_video(final);(out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if not report['passed']:raise RuntimeError('Real MP4 validation failed: '+str(report['errors']))
    (out/'SHA256SUMS').write_text(''.join(hashlib.sha256((out/name).read_bytes()).hexdigest()+'  '+name+'\n' for name in ['short_ciencia_demo.mp4','metadata.json','validation.json','captions.srt']))
    (args.out/'latest.json').write_text(json.dumps({'directory':str(out.resolve()),'video':str(final.resolve()),'validated':True},indent=2)+'\n')
    print('REAL_VIDEO:',final.resolve());print('VALIDATED:',report['sha256'],'SECONDS:',report['duration_seconds'],'CONTEXT:',metadata['execution']['context'])

if __name__=='__main__':main()
