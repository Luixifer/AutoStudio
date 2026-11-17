#!/usr/bin/env python3
"""AutoStudio: original 3D scenes + local neural voice; legacy diagrams remain selectable."""
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
    parser=argparse.ArgumentParser();parser.add_argument('--profile',choices=['classic','cinematic'],default='cinematic');parser.add_argument('--script',type=Path);parser.add_argument('--out',type=Path,default=ROOT/'output');args=parser.parse_args()
    for tool in ['ffmpeg','ffprobe']:
        if not shutil.which(tool):raise RuntimeError('Missing required free program: '+tool)
    args.script=args.script or ROOT/('scripts/ocean_v02.json' if args.profile=='cinematic' else 'scripts/ocean.json');data=load_story(args.script);stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=args.out/(data['id']+'-'+stamp+'-'+uuid.uuid4().hex[:6]);out.mkdir(parents=True)
    started=time.monotonic();segments=[];scene_info=[];all_cues=[];all_words=[];samples_per_scene=[];total_frames=0;voice_info=[];previous_visual=None;visual_checks=[]
    cinematic=args.profile=='cinematic';narrator=None;assets=None
    if cinematic:
        sys.path.insert(0,str(ROOT))
        from scripts.neural_narration import NeuralNarrator
        from scripts.cinematic import CinematicArtwork,verify_assets
        from scripts.subtitles import group_words,caption_at
        narrator=NeuralNarrator();assets=verify_assets()
    for number,scene in enumerate(data['scenes'],1):
        wav=out/f'scene_{number:02d}.wav';voice_info.append(narrator.synthesize(scene['voice'],wav) if cinematic else synthesize(scene['voice'],wav))
        with wave.open(str(wav),'rb') as audio:
            if audio.getsampwidth()!=2 or audio.getnchannels()!=1:raise ValueError('Narrator must return 16-bit mono WAV.')
            rate=audio.getframerate();raw=audio.readframes(audio.getnframes());voice_duration=audio.getnframes()/rate
        pause=(.60 if number==len(data['scenes']) else .12) if cinematic else .45
        count=math.ceil((voice_duration+pause)*FPS);duration=count/FPS
        if (total_frames+count)/FPS>=150:raise ValueError('Narration exceeds the 150-second MVP render budget.')
        cues=group_words(voice_info[-1]['words']) if cinematic else cues_for(scene['voice'],voice_duration);art=CinematicArtwork(scene,number,len(data['scenes']),assets) if cinematic else SceneArtwork(scene,number,len(data['scenes']));mp4=out/f'scene_{number:02d}.mp4';log=out/f'scene_{number:02d}_encoder.log'
        cmd=['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','22','-profile:v','high','-level:v','3.1','-pix_fmt','yuv420p','-threads','2',str(mp4)]
        with log.open('wb') as errors:
            process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=errors)
            try:
                cue_index=0
                for frame in range(count):
                    t=frame/FPS
                    while cue_index+1<len(cues) and t>=cues[cue_index]['end']:cue_index+=1
                    subtitle=caption_at(cues,t) if cinematic else (cues[cue_index]['text'] if t>=cues[0]['start'] and t<=cues[-1]['end'] else '')
                    image=art.frame(t,duration,subtitle,previous_visual=previous_visual) if cinematic else art.frame(t,duration,subtitle)
                    if frame==count//2:image.save(out/f'preview_{number:02d}.jpg',quality=90)
                    process.stdin.write(image.tobytes())
                process.stdin.close();code=process.wait(timeout=180)
                if code:raise RuntimeError(f'FFmpeg failed for scene {number}; see {log}.')
            except BaseException:
                process.kill();process.wait();raise
        offset=total_frames/FPS
        if cinematic:
            from PIL import ImageChops,ImageStat
            a=art.visual(0,duration).crop((30,350,690,850));b=art.visual(duration-.04,duration).crop((30,350,690,850));difference=sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3
            if difference<.25:raise ValueError('Cinematic shot has no measurable visual movement.')
            visual_checks.append({'scene':number,'asset':scene['asset'],'motion_mean_absolute_pixel_difference':round(difference,3),'caption_max_words':max(len(c['words']) for c in cues),'caption_max_lines':max(len(__import__('scripts.cinematic',fromlist=['caption_layout']).caption_layout(c['words'])) for c in cues)})
            for word in voice_info[-1]['words']:all_words.append({**word,'start':offset+word['start'],'end':offset+word['end'],'scene':number})
            previous_visual=art.visual(duration-.04,duration)
        for cue in cues:all_cues.append({**cue,'start':offset+cue['start'],'end':offset+cue['end']})
        target_samples=round(duration*rate);padding=target_samples-len(raw)//2
        samples_per_scene.append((rate,raw+b'\0\0'*max(0,padding)));scene_info.append({'scene':number,'visual':scene['visual'],'voice_seconds':voice_duration,'video_seconds':duration,'frames':count,'narration':scene['voice'],'asset':scene.get('asset'),'camera':scene.get('camera')});segments.append(mp4);total_frames+=count
    if len({r for r,_ in samples_per_scene})!=1:raise ValueError('Narration sample rate changed between scenes.')
    voice=out/'narration.wav'
    with wave.open(str(voice),'wb') as output:
        output.setnchannels(1);output.setsampwidth(2);output.setframerate(samples_per_scene[0][0]);output.writeframes(b''.join(raw for _,raw in samples_per_scene))
    listing=out/'concat.txt';listing.write_text(''.join("file '"+p.name+"'\n" for p in segments))
    final=out/'short_ciencia_demo.mp4'
    sound_info=None
    if cinematic:
        from scripts.soundscape import write_ambience
        ambience=out/'ambience.wav';cursor=0;cuts=[]
        for item in scene_info[:-1]:cursor+=item['video_seconds'];cuts.append(cursor)
        sound_info=write_ambience(ambience,total_frames/FPS,cuts)
        cmd=['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-i',str(voice),'-i',str(ambience),'-filter_complex','[1:a]aformat=channel_layouts=stereo,apad,loudnorm=I=-16:LRA=7:TP=-1.5[v];[2:a]volume=0.42[b];[v][b]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.84:level=false[a]','-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','128k','-ar','48000','-ac','2','-t',str(total_frames/FPS),'-movflags','+faststart',str(final)]
    else:
        cmd=['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-i',str(voice),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','128k','-ar','48000','-ac','2','-af','apad,loudnorm=I=-16:LRA=7:TP=-1.5','-t',str(total_frames/FPS),'-movflags','+faststart',str(final)]
    subprocess.run(cmd,check=True,timeout=240)
    (out/'captions.srt').write_text('\n'.join(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n" for i,c in enumerate(all_cues,1)),encoding='utf-8')
    github=os.environ.get('GITHUB_ACTIONS')=='true';repo=os.environ.get('GITHUB_REPOSITORY');run_id=os.environ.get('GITHUB_RUN_ID')
    metadata={'schema':1,'managed_by':'autostudio-mvp','version':'0.2-cinematic.1','profile':args.profile,'title':data['title'],'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'execution':{'context':'github-actions' if github else 'standalone-python','github_repository':repo if github else None,'github_run_id':run_id if github else None,'github_run_url':f'https://github.com/{repo}/actions/runs/{run_id}' if github and repo and run_id else None,'git':git_info(),'python':platform.python_version(),'platform':platform.platform(),'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]},'video':{'frames':total_frames,'fps':FPS,'duration_seconds':total_frames/FPS,'size':[720,1280]},'narration':voice_info,'subtitle_timing':('Kokoro phoneme duration output mapped at explicit word boundaries; short dynamic word-highlighted captions. Not an independent human/ASR alignment review.' if cinematic else 'Approximate chunk timing from text lengths, not forced alignment.'),'soundscape':sound_info,'scenes':scene_info,'sources':data['sources'],'source_verification':'Provided editorial references, not retrieved by the renderer; manual verification required before publication.','visual_disclosure':('Original Blender illustrations with animated camera crops and particles; not real underwater footage or full fluid simulation.' if cinematic else 'Original animated diagrams, not real underwater footage or photorealistic AI video.'),'paid_api_requests':0,'youtube_publication':'disabled','elapsed_render_seconds':round(time.monotonic()-started,2),'script_sha256':hashlib.sha256(args.script.read_bytes()).hexdigest(),'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'scripts').glob('*.py')}}
    if data.get('production'):metadata['production']=data['production']
    quality={'profile':args.profile,'shot_count':len(scene_info),'shot_duration_seconds':[s['video_seconds'] for s in scene_info],'short_dynamic_captions':cinematic,'max_words_per_caption':max(len(c['text'].split()) for c in all_cues),'timing_source':'same TTS inference phoneme durations' if cinematic else 'text length estimate','visual_checks':visual_checks,'caption_groups':len(all_cues),'timed_words':len(all_words),'human_visual_or_voice_approval':False}
    if cinematic:
        if len(all_words)!=sum(len(s['voice'].split()) for s in data['scenes']):raise ValueError('Caption transcript word coverage mismatch.')
        if any(w['end']<=w['start'] for w in all_words) or all_words[-1]['end']>total_frames/FPS:raise ValueError('Timed words outside mux timeline.')
        quality['word_coverage_passed']=True;quality['word_times_inside_audio']=True
        metadata['asset_manifest_sha256']=hashlib.sha256((ROOT/'assets/cinematic/manifest.json').read_bytes()).hexdigest()
    (out/'quality.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2)+'\n')
    (out/'word-timings.json').write_text(json.dumps({'method':quality['timing_source'],'words':all_words,'human_verified':False},ensure_ascii=False,indent=2)+'\n')
    (out/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=inspect_video(final);(out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if not report['passed']:raise RuntimeError('Real MP4 validation failed: '+str(report['errors']))
    (out/'SHA256SUMS').write_text(''.join(hashlib.sha256((out/name).read_bytes()).hexdigest()+'  '+name+'\n' for name in ['short_ciencia_demo.mp4','metadata.json','validation.json','captions.srt','quality.json','word-timings.json']))
    (args.out/'latest.json').write_text(json.dumps({'directory':str(out.resolve()),'video':str(final.resolve()),'validated':True},indent=2)+'\n')
    print('REAL_VIDEO:',final.resolve());print('VALIDATED:',report['sha256'],'SECONDS:',report['duration_seconds'],'CONTEXT:',metadata['execution']['context'])

if __name__=='__main__':main()
