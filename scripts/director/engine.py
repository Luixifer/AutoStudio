"""Incremental FFmpeg documentary assembly, driven by measured narration.

Reuses the pinned personal editor's smooth camera, ASS and subtitle helpers.
Scene caches are content-addressed and verified; no commercial APIs.
"""
from __future__ import annotations
import argparse,json,math,os,subprocess,wave,shutil
from pathlib import Path
from PIL import Image,ImageOps
from scripts.personal_editor import zoom_filter,write_ass,caption_groups,srt_time
from scripts.director.project import load,probe,digest,FORMATS,media_file

ROOT=Path(__file__).resolve().parents[2]

def run(*args,timeout=1800):
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-threads','2',*map(str,args)],check=True,timeout=timeout)

def atomic_json(path,data):
    p=Path(path);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,p)

def pcm_seconds(path):
    with wave.open(str(path),'rb') as w:return w.getnframes()/w.getframerate()

def join_wavs(paths,target):
    with wave.open(str(target),'wb') as dst:
        params=None
        for path in paths:
            with wave.open(str(path),'rb') as src:
                current=(src.getnchannels(),src.getsampwidth(),src.getframerate())
                if params is None:params=current;dst.setnchannels(params[0]);dst.setsampwidth(params[1]);dst.setframerate(params[2])
                if current!=params:raise ValueError('PCM incompatible entre capítulos')
                for block in iter(lambda:src.readframes(48000),b''):dst.writeframesraw(block)

def validate_words(words,text,seconds):
    if not isinstance(words,list) or not words:raise ValueError('Faltan tiempos de locución')
    if ' '.join(w.get('word','') for w in words).split()!=text.split():raise ValueError('Subtítulos y guion no coinciden')
    previous=0
    for w in words:
        a,b=w.get('start'),w.get('end')
        if type(a) not in (int,float) or type(b) not in (int,float) or not math.isfinite(a+b) or not previous-.002<=a<b<=seconds+.03:
            raise ValueError('Subtítulos fuera del audio real')
        previous=b
    return words

def narrate(scene,config,root,out,narrators):
    voice=scene.get('voice',config.get('voice',{'mode':'kokoro','voice':'em_alex'}))
    raw=out/'spoken.wav'
    if voice['mode']=='file':
        source=media_file(root,voice.get('path'),{'.wav','.mp3'})
        run('-i',source,'-vn','-c:a','pcm_s16le','-ar','24000','-ac','1',raw)
        seconds=pcm_seconds(raw);words=voice.get('timed_words')
        if words is None:
            # Optional free CPU alignment; fail on transcription discrepancy.
            from faster_whisper import WhisperModel
            from scripts.audio_ai_qa import normalized_words
            if 'whisper' not in narrators:narrators['whisper']=WhisperModel('base',device='cpu',compute_type='int8',cpu_threads=2)
            pieces,_=narrators['whisper'].transcribe(str(raw),language='es',word_timestamps=True,condition_on_previous_text=False)
            detected=[w for p in pieces for w in (p.words or [])]
            actual=' '.join(w.word.strip() for w in detected)
            if normalized_words(actual)!=normalized_words(scene['narration']):
                raise ValueError('La transcripción no coincide con el guion: revisa el audio o aporta tiempos confirmados')
            tokens=scene['narration'].split()
            if len(tokens)!=len(detected):raise ValueError('No es posible alinear exactamente este audio; aporta tiempos confirmados')
            words=[{'word':t,'start':float(w.start),'end':float(w.end)} for t,w in zip(tokens,detected)]
        info={'engine':'user-provided audio','alignment':'provided timed_words' if voice.get('timed_words') else 'local CPU Whisper exact text match','voice_quality_approved':False}
    else:
        name=voice.get('voice','em_alex')
        if name not in narrators:
            from scripts.neural_narration import NeuralNarrator
            narrators[name]=NeuralNarrator(voice=name)
        info=narrators[name].synthesize(scene['narration'],raw);words=info['words'];seconds=pcm_seconds(raw)
    if not .3<=seconds<=180:raise ValueError('Cada escena debe contener entre 0,3 y 180 segundos reales de voz')
    validate_words(words,scene['narration'],seconds)
    return raw,words,info

def ease_keys(keys,axis,frames):
    """Piecewise cosine interpolation, continuous position and zero endpoint speed."""
    phase=f'min(on/{max(1,frames-1)},1)'
    expression=str(keys[-1].get(axis,1.05 if axis=='zoom' else .5))
    for a,b in reversed(list(zip(keys,keys[1:]))):
        lo=a.get(axis,1.05 if axis=='zoom' else .5);hi=b.get(axis,1.05 if axis=='zoom' else .5)
        u=f'clip(({phase}-{a["at"]})/({b["at"]}-{a["at"]}),0,1)'
        value=f'({lo}+({hi}-{lo})*(.5-.5*cos(PI*{u})))'
        expression=f'if(lte({phase},{b["at"]}),{value},{expression})'
    return expression

def camera_filter(scene,frames,size,fps):
    keys=scene.get('camera',{}).get('keyframes')
    if not keys:
        return zoom_filter({'camera':{'movement':scene.get('camera',{}).get('movement','zoom_in'),'zoom':1.08,'target':[.5,.5]}},frames,size,fps)
    z=ease_keys(keys,'zoom',frames);x=ease_keys(keys,'x',frames);y=ease_keys(keys,'y',frames)
    return f"format=yuv444p,zoompan=z='{z}':x='(iw-iw/zoom)*({x})':y='(ih-ih/zoom)*({y})':d=1:s={size[0]}x{size[1]}:fps={fps},format=yuv420p"

def canvas(source,target,size,fit='contain',layer=False):
    with Image.open(source) as original:
        image=ImageOps.exif_transpose(original).convert('RGBA' if layer else 'RGB')
        if layer and (image.getextrema()[3][0]==255):raise ValueError('Capa parallax sin transparencia real')
        if fit=='cover' and not layer:result=ImageOps.fit(image,size,Image.Resampling.LANCZOS)
        else:
            fg=ImageOps.contain(image,size,Image.Resampling.LANCZOS)
            result=Image.new('RGBA' if layer else 'RGB',size,(0,0,0,0) if layer else (13,20,31))
            result.paste(fg,((size[0]-fg.width)//2,(size[1]-fg.height)//2))
        result.save(target)

def scene_cache_key(scene,config,root):
    # Include all source code used by this engine, actual models and ffmpeg build.
    inputs={}
    def collect(obj):
        if isinstance(obj,dict):
            if 'path' in obj:inputs[obj['path']]=digest(Path(root)/obj['path'])
            for value in obj.values():collect(value)
        elif isinstance(obj,list):
            for value in obj:collect(value)
    collect(scene);collect(config.get('voice',{}))
    code=[Path(__file__),Path(__file__).parent/'project.py',ROOT/'scripts/neural_narration.py',ROOT/'scripts/personal_editor.py',ROOT/'assets/voice-models.json']
    value={'scene':scene,'format':config['format'],'fps':config.get('fps',30),'voice':config.get('voice'), 'inputs':inputs,'code':{str(p.relative_to(ROOT)):digest(p) for p in code},'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]}
    import hashlib
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()

def render_scene(scene,config,root,cache,narrators,outgoing=True):
    key=scene_cache_key({**scene,'_outgoing':outgoing},config,root);work=cache/key;work.mkdir(parents=True,exist_ok=True)
    marker=work/'complete.json';video=work/'visual.mp4';audio=work/'narration.wav'
    if marker.is_file():
        old=json.loads(marker.read_text())
        if all((work/name).is_file() and digest(work/name)==sha for name,sha in old['files'].items()):return work,old
    raw,words,voice=narrate(scene,config,root,work,narrators)
    fps=config.get('fps',30);size=FORMATS[config['format']];width,height=size
    spoken=pcm_seconds(raw);duration=math.ceil((spoken+.2)*fps)/fps
    transition=scene.get('transition',{})
    extra=transition.get('seconds',0) if outgoing and transition.get('type','cut')!='cut' else 0
    # Narration never crossfades/overlaps: visual handles extend after its scene.
    if extra>=duration:raise ValueError('Transición mayor que la escena')
    frames=math.ceil((duration+extra)*fps);visual_seconds=frames/fps
    run('-i',raw,'-af','apad','-t',f'{duration:.6f}','-ar','48000','-ac','1','-c:a','pcm_s16le',audio)
    m=scene['media'];source=Path(root)/m['path'];args=[];graph=[]
    if m['kind']=='image':
        big=(width*2,height*2);still=work/'canvas.png';canvas(source,still,big,m.get('fit','contain'))
        args+=['-loop','1','-framerate',str(fps),'-i',str(still)];previous='0:v'
        for i,layer in enumerate(m.get('layers',[]),1):
            pic=work/f'layer-{i}.png';canvas(Path(root)/layer['path'],pic,big,layer=True)
            args+=['-loop','1','-framerate',str(fps),'-i',str(pic)]
            a=layer.get('from',[0,0]);b=layer.get('to',[0,0]);phase=f'(.5-.5*cos(PI*min(t/{visual_seconds},1)))'
            x=f'{big[0]}*({a[0]}+({b[0]}-{a[0]})*{phase})';y=f'{big[1]}*({a[1]}+({b[1]}-{a[1]})*{phase})'
            graph.append(f'[{previous}][{i}:v]overlay=x=\'{x}\':y=\'{y}\':eval=frame:shortest=1[p{i}]');previous=f'p{i}'
        graph.append(f'[{previous}]'+camera_filter(scene,frames,size,fps)+'[v]')
    else:
        details=probe(source);v=next((s for s in details['streams'] if s['codec_type']=='video'),None)
        if not v:raise ValueError('MP4 sin vídeo')
        available=float(details['format']['duration'])-float(m.get('trim_start',0))
        if available<=0 or available+1/fps<visual_seconds and not m.get('loop',False):
            raise ValueError('Clip insuficiente para la locución; recórtala, aporta otro clip o activa bucle explícitamente')
        if m.get('loop',False):args+=['-stream_loop','-1']
        args+=['-ss',str(m.get('trim_start',0)),'-i',str(source)]
        fit=f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x0d141f'
        if m.get('fit','contain')=='cover':fit=f'scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}'
        graph.append(f'[0:v]scale=ceil(iw*sar/2)*2:ih,setsar=1,fps={fps},{fit},setsar=1,setpts=PTS-STARTPTS,format=yuv420p[v]')
    temp=work/'visual.tmp.mp4'
    run(*args,'-filter_complex_threads','1','-filter_complex',';'.join(graph),'-map','[v]','-an','-frames:v',frames,'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-r',fps,'-movflags','+faststart',temp)
    os.replace(temp,video)
    info={'id':scene['id'],'key':key,'duration':duration,'voice_seconds':spoken,'visual_seconds':visual_seconds,'transition_seconds':extra,'transition':transition.get('type','cut'),'words':words,'voice':voice,'files':{p.name:digest(p) for p in (video,audio)},'input_media_sha256':digest(source)}
    atomic_json(marker,info);return work,info

def produce(project_path,out,chapter_id=None):
    path=Path(project_path).resolve();config=load(path);root=path.parent;out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    size=FORMATS[config['format']];fps=config.get('fps',30);cache=out/'scene-cache';cache.mkdir(exist_ok=True);narrators={}
    chapters=config['chapters']
    if chapter_id:
        chapters=[c for c in chapters if c['id']==chapter_id]
        if not chapters:raise ValueError('Capítulo desconocido')
    outputs=[];global_cues=[];global_offset=0;scene_reports=[]
    for chapter in chapters:
        parts=[];cues=[];offset=0
        for index,scene in enumerate(chapter['scenes']):
            work,meta=render_scene(scene,config,root,cache,narrators,index<len(chapter['scenes'])-1)
            meta={**meta,'start':global_offset+offset,'chapter':chapter['id']};parts.append((work,meta))
            cues.extend({**c,'start':c['start']+offset,'end':c['end']+offset} for c in caption_groups(meta['words']))
            offset+=meta['duration'];scene_reports.append(meta)
        if offset>600:raise ValueError('Capítulo superior a diez minutos; divídelo para renderizar por partes')
        if global_offset+offset>3600:raise ValueError('Documental superior al límite de 60 minutos')
        work=out/chapter['id'];work.mkdir(exist_ok=True);chapter_audio=work/'voice.wav';join_wavs([p/'narration.wav' for p,m in parts],chapter_audio)
        ass=work/'captions.ass';write_ass(ass,cues,size,config['title'],offset,source_type='provided')
        args=[];graph=[]
        for p,m in parts:args+=['-i',str(p/'visual.mp4')]
        for i,(p,m) in enumerate(parts):graph.append(f'[{i}:v]setsar=1,setpts=PTS-STARTPTS,format=yuv420p,settb=AVTB,fps={fps}[s{i}]')
        prev='s0';elapsed=0
        for i in range(1,len(parts)):
            last=parts[i-1][1];elapsed+=last['duration'];name=f'x{i}';d=last['transition_seconds']
            if d:
                kind='fade' if last['transition']=='dissolve' else last['transition']
                graph.append(f'[{prev}][s{i}]xfade=transition={kind}:duration={d}:offset={elapsed},fps={fps}[{name}]')
            else:graph.append(f'[{prev}][s{i}]concat=n=2:v=1:a=0,fps={fps}[{name}]')
            prev=name
        # Paths generated under controlled work directories, never filter text from input.
        safe=str(ass).replace('\\','\\\\').replace(':','\\:').replace("'","'\\''")
        graph.append(f"[{prev}]ass=filename='{safe}',format=yuv420p[final]")
        target=work/'chapter.mp4';temp=work/'chapter.tmp.mp4'
        run(*args,'-filter_complex_threads','1','-filter_complex',';'.join(graph),'-map','[final]','-an','-t',offset,'-c:v','libx264','-preset','veryfast','-crf','20','-r',fps,'-pix_fmt','yuv420p','-movflags','+faststart',temp)
        os.replace(temp,target);outputs.append((target,chapter_audio))
        global_cues.extend({**c,'start':c['start']+global_offset,'end':c['end']+global_offset} for c in cues);global_offset+=offset
        atomic_json(work/'chapter.json',{'id':chapter['id'],'duration':offset,'video_sha256':digest(target),'voice_sha256':digest(chapter_audio),'scenes':[m['id'] for p,m in parts]})
    listing=out/'chapters.txt';listing.write_text(''.join("file '"+str(v.relative_to(out))+"'\n" for v,a in outputs))
    speech=out/'narration.wav';join_wavs([a for v,a in outputs],speech)
    args=['-f','concat','-safe','1','-i',str(listing),'-i',str(speech)];graph=[];audio='1:a';index=2
    music=config.get('music')
    if music:
        args+=['-stream_loop','-1','-i',str(root/music['path'])];gain=music.get('gain',.12)
        graph+=['[1:a]asplit=2[voice][detector]',f'[{index}:a]volume={gain},afade=t=in:d=1,afade=t=out:st={max(0,global_offset-1)}:d=1[music]', '[music][detector]sidechaincompress=threshold=0.025:ratio=8:attack=15:release=350[ducked]','[voice][ducked]amix=inputs=2:duration=first:normalize=0[mixed]'];audio='mixed';index+=1
    fx=[]
    for meta in scene_reports:
        scene=next(s for c in chapters for s in c['scenes'] if s['id']==meta['id'])
        for effect in scene.get('effects',[]):
            at=effect.get('at',0)
            if at>=meta['duration']:raise ValueError('Efecto fuera de la escena')
            args+=['-i',str(root/effect['path'])];label=f'fx{index}';delay=round((meta['start']+at)*1000)
            graph.append(f'[{index}:a]volume={effect.get("gain",.2)},adelay={delay}:all=1[{label}]');fx.append(label);index+=1
    if fx:graph.append(''.join(f'[{x}]' for x in [audio,*fx])+f'amix=inputs={1+len(fx)}:duration=first:normalize=0[withfx]');audio='withfx'
    graph.append(f'[{audio}]loudnorm=I=-16:TP=-1.5:LRA=9,alimiter=limit=.891:level=false,aresample=48000:async=1[a]')
    final=out/'documental-REVISION.mp4';temp=out/'documental.tmp.mp4'
    run(*args,'-filter_complex_threads','1','-filter_complex',';'.join(graph),'-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-ac','2','-ar','48000','-t',global_offset,'-movflags','+faststart',temp)
    os.replace(temp,final)
    captions=out/'captions.srt';captions.write_text('\n'.join(f'{i}\n{srt_time(c["start"])} --> {srt_time(c["end"])}\n{c["text"]}\n' for i,c in enumerate(global_cues,1)),encoding='utf-8')
    atomic_json(out/'timeline.json',{'duration':global_offset,'scenes':scene_reports,'cues':global_cues,'chapters':[str(v.relative_to(out)) for v,a in outputs],'human_artistic_approved':False,'youtube_enabled':False,'project_sha256':digest(path),'scope':'Single selected chapter' if chapter_id else 'Complete project'})
    from scripts.director.validate import inspect
    report=inspect(final,size,fps,global_offset,global_cues)
    report['github_run_id']=os.environ.get('GITHUB_RUN_ID');report['execution_context']='GitHub Actions' if os.environ.get('GITHUB_ACTIONS')=='true' else 'cloud workspace'
    atomic_json(out/'validation.json',report)
    if not report['passed']:raise RuntimeError('QA rechazado: '+str(report['errors']))
    (out/'SHA256SUMS').write_text(digest(final)+'  '+final.name+'\n')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--chapter');a=p.parse_args();print(json.dumps(produce(a.project,a.out,a.chapter),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
