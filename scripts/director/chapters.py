"""Portable chapter inputs/outputs and verified final assembly without source images.

No shared server, no Git media, no narration regeneration at assembly time.
"""
from __future__ import annotations
from fractions import Fraction
import argparse,hashlib,json,os,shutil,subprocess,zipfile,wave
from pathlib import Path
from scripts.director.project import load,digest,FORMATS,ID,MAX_BUNDLE,media_file,probe,SCHEMA
from scripts.director.engine import join_wavs,pcm_seconds,run,atomic_json,srt_time

def canonical(data):return json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def chapter_doc(project,chapter):return {**{k:v for k,v in project.items() if not k.startswith('_')},'chapters':[chapter]}
def fingerprint(data):return hashlib.sha256(canonical(data)).hexdigest()
def paths(value):
 found=set()
 if isinstance(value,dict):
  if 'path' in value:found.add(value['path'])
  for v in value.values():found.update(paths(v))
 elif isinstance(value,list):
  for v in value:found.update(paths(v))
 return found

def chapter_identity(project,chapter,root):
 document=chapter_doc(project,chapter)
 code_root=Path(__file__).resolve().parents[2]
 renderer={name:digest(code_root/name) for name in ('scripts/director/engine.py','scripts/director/narration.py','scripts/director/captions.py','scripts/director/text.py','scripts/director/subshots.py','scripts/director/project.py','scripts/personal_editor.py','assets/voice-models.json')}
 return fingerprint({'document':document,'input_sha256':{name:digest(Path(root)/name) for name in sorted(paths(document))},'renderer_sha256':renderer,'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]})

def split(project_path,out):
 source=Path(project_path);p=load(source);root=source.parent;out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if any(s.get('effects') for c in p['chapters'] for s in c['scenes']):raise ValueError('El reparto portátil aún no admite efectos por escena; el montaje completo sí')
 plan={'schema':'autostudio-director-assembly/1','title':p['title'],'format':p['format'],'fps':p.get('fps',30),'youtube_enabled':False,'source_project_sha256':digest(source),'chapters':[]}
 for chapter in p['chapters']:
  document=chapter_doc(p,chapter);name='input-'+chapter['id']+'.zip';target=out/name
  required=paths(document)
  if sum((root/n).stat().st_size for n in required)>MAX_BUNDLE-2_000_000:raise ValueError('Un capítulo supera 200 MiB: reduce clips o divide ese capítulo')
  with zipfile.ZipFile(target,'w',zipfile.ZIP_STORED) as z:
   z.writestr('project.json',json.dumps(document,ensure_ascii=False,indent=2)+'\n')
   for name in sorted(required):z.write(root/name,name)
  plan['chapters'].append({'id':chapter['id'],'input':target.name,'input_sha256':digest(target),'document_sha256':chapter_identity(p,chapter,root),'rendered':'rendered-'+chapter['id']+'.zip'})
 if p.get('music'):
  folder=out/'assembly-media';folder.mkdir(exist_ok=True);m=p['music'];name='music'+Path(m['path']).suffix.lower();shutil.copy2(root/m['path'],folder/name);plan['music']={**m,'path':'assembly-media/'+name,'sha256':digest(folder/name)}
 atomic_json(out/'assembly.json',plan);return out/'assembly.json'

def package_render(project_path,render_dir,chapter_id,out):
 p=load(project_path);chapter=next((c for c in p['chapters'] if c['id']==chapter_id),None)
 if chapter is None:raise ValueError('Capítulo desconocido')
 if any(s.get('effects') for s in chapter['scenes']):raise ValueError('Los efectos por escena requieren el ensamblaje completo en esta revisión')
 render=Path(render_dir);timeline=json.loads((render/'timeline.json').read_text());scenes=[s for s in timeline['scenes'] if s['chapter']==chapter_id]
 if [s['id'] for s in scenes]!=[s['id'] for s in chapter['scenes']]:raise ValueError('El capítulo renderizado no corresponde al guion')
 if timeline['project_sha256']!=digest(project_path):raise ValueError('El proyecto cambió después de renderizar')
 from scripts.director.engine import scene_cache_key
 for index,(source,rendered) in enumerate(zip(chapter['scenes'],scenes)):
  envelope={**source,'_incoming_seconds':rendered.get('narration_offset',0),'_outgoing':index<len(scenes)-1,'_strict':p.get('scene_policy')=='paragraph/1'}
  if scene_cache_key(envelope,p,Path(project_path).parent)!=rendered['key']:raise ValueError('El recurso o renderizador cambió después de completar el capítulo')

 base=render/chapter_id;video=base/'chapter.mp4';audio=base/'voice.wav';seconds=pcm_seconds(audio);offset=scenes[0]['start']
 # Use actual measured word timings and the scene order used by the render.
 from scripts.personal_editor import caption_groups
 cues=[]
 if p.get('scene_policy')=='paragraph/1':
  validation=json.loads((render/'validation.json').read_text())
  if not validation.get('passed') or not validation.get('correspondence',{}).get('passed'):raise ValueError('Capítulo sin correspondencia verificada')
  ids={s['id'] for s in scenes}
  cues=[{**c,'start':c['start']-offset,'end':c['end']-offset} for c in timeline['cues'] if c.get('scene_id') in ids]
 else:
  for s in scenes:cues.extend({**c,'start':c['start']+s['start']-offset,'end':c['end']+s['start']-offset} for c in caption_groups(s['words']))
 v=next(s for s in probe(video)['streams'] if s['codec_type']=='video')
 if abs(float(v['duration'])-seconds)>.06:raise ValueError('El vídeo y el PCM del capítulo no coinciden')
 header={'schema':'autostudio-director-rendered/1','id':chapter_id,'document_sha256':chapter_identity(p,chapter,Path(project_path).parent),'video_sha256':digest(video),'voice_sha256':digest(audio),'format':p['format'],'fps':p.get('fps',30),'duration':seconds,'cues':cues,'human_artistic_approved':False}
 out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
 if video.stat().st_size+audio.stat().st_size>=2*1024**3:raise ValueError('Capítulo superior a 2 GiB; divídelo')
 with zipfile.ZipFile(out,'w',zipfile.ZIP_STORED) as z:z.write(video,'chapter.mp4');z.write(audio,'voice.wav');z.writestr('chapter.json',json.dumps(header,ensure_ascii=False,indent=2)+'\n')
 return header

def unpack_render(source,dest):
 dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(source) as z:
  allowed={'chapter.mp4','voice.wav','chapter.json'};infos=z.infolist()
  if len(infos)!=3 or {i.filename for i in infos}!=allowed or sum(i.file_size for i in infos)>=2*1024**3:raise ValueError('Archivo de capítulo no válido')
  if next(i.file_size for i in infos if i.filename=='chapter.json')>2_000_000:raise ValueError('Metadatos excesivos')
  for name in allowed:
   with z.open(name) as src,(dest/name).open('wb') as out:shutil.copyfileobj(src,out,1024*1024)
 return json.loads((dest/'chapter.json').read_text())

def assemble(plan_path,bundles,out):
 plan_path=Path(plan_path);plan=json.loads(plan_path.read_text());out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 if plan.get('schema')!='autostudio-director-assembly/1' or plan.get('youtube_enabled') is not False or plan.get('format') not in FORMATS or plan.get('fps') not in (30,60):raise ValueError('Plan de ensamblaje incompatible')
 entries=plan.get('chapters',[])
 if not 1<=len(entries)<=24 or len({c['id'] for c in entries})!=len(entries):raise ValueError('Capítulos duplicados o ausentes')
 clips=[];wavs=[];cues=[];offset=0
 size=FORMATS[plan['format']];fps=plan['fps']
 for item in entries:
  ident=item['id']
  if not ID.fullmatch(ident) or item.get('rendered')!='rendered-'+ident+'.zip':raise ValueError('Nombre de capítulo no válido')
  dest=out/'parts'/ident;header=unpack_render(Path(bundles)/item['rendered'],dest)
  if header.get('schema')!='autostudio-director-rendered/1' or header.get('id')!=ident or header.get('document_sha256')!=item['document_sha256'] or header.get('format')!=plan['format'] or header.get('fps')!=fps:raise ValueError('Capítulo de otro proyecto o versión')
  video=dest/'chapter.mp4';audio=dest/'voice.wav'
  if digest(video)!=header['video_sha256'] or digest(audio)!=header['voice_sha256']:raise ValueError('Capítulo dañado o modificado')
  details=probe(video);v=next(s for s in details['streams'] if s['codec_type']=='video')
  if (v['width'],v['height'])!=size or v['codec_name']!='h264' or v['pix_fmt']!='yuv420p' or Fraction(v['avg_frame_rate'])!=fps:raise ValueError('Vídeo de capítulo no compatible')
  seconds=pcm_seconds(audio)
  with wave.open(str(audio),'rb') as w:
   if (w.getnchannels(),w.getsampwidth(),w.getframerate())!=(1,2,48000):raise ValueError('PCM de capítulo incompatible')
  if not .3<=seconds<=600 or abs(seconds-header['duration'])>.01 or abs(seconds-float(v['duration']))>.06:raise ValueError('Duración de capítulo incoherente')
  previous=0
  for c in header['cues']:
   if not previous-.002<=c['start']<c['end']<=seconds+.03:raise ValueError('Subtítulos de capítulo fuera de tiempo')
   previous=c['end'];cues.append({**c,'start':c['start']+offset,'end':c['end']+offset})
  clips.append(video);wavs.append(audio);offset+=seconds
 if offset>3600:raise ValueError('El ensamblaje supera 60 minutos')
 listing=out/'chapters.txt';listing.write_text(''.join("file '"+str(p.relative_to(out))+"'\n" for p in clips));speech=out/'narration.wav';join_wavs(wavs,speech)
 args=['-f','concat','-safe','1','-i',str(listing),'-i',str(speech)];graph=[];audio='1:a';m=plan.get('music')
 if m:
  music=media_file(plan_path.parent,m['path'],{'.wav','.mp3'})
  if digest(music)!=m.get('sha256'):raise ValueError('La música cambió después de dividir')
  args+=['-stream_loop','-1','-i',str(music)];gain=m.get('gain',.12)
  if not isinstance(gain,(int,float)) or not 0<=gain<=.3:raise ValueError('Ganancia musical no válida')
  graph=['[1:a]asplit=2[voice][detector]',f'[2:a]volume={gain},afade=t=in:d=1,afade=t=out:st={max(0,offset-1)}:d=1[music]','[music][detector]sidechaincompress=threshold=.025:ratio=8:attack=15:release=350[ducked]','[voice][ducked]amix=inputs=2:duration=first:normalize=0[mix]'];audio='mix'
 graph.append(f'[{audio}]loudnorm=I=-16:TP=-1.5:LRA=9,alimiter=limit=.891:level=false,aresample=48000:async=1[a]')
 final=out/'documental-REVISION.mp4';run(*args,'-filter_complex_threads','1','-filter_complex',';'.join(graph),'-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t',offset,'-movflags','+faststart',final)
 (out/'captions.srt').write_text('\n'.join(f'{i}\n{srt_time(c["start"])} --> {srt_time(c["end"])}\n{c["text"]}\n' for i,c in enumerate(cues,1)))
 from scripts.director.validate import inspect
 report=inspect(final,size,fps,offset,cues);report['assembly']='Portable, SHA-verified chapters; no narration regenerated';atomic_json(out/'validation.json',report)
 if not report['passed']:raise RuntimeError(str(report['errors']))
 (out/'SHA256SUMS').write_text(digest(final)+'  '+final.name+'\n');return report

def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
 a=s.add_parser('split');a.add_argument('project',type=Path);a.add_argument('--out',type=Path,required=True)
 a=s.add_parser('package');a.add_argument('project',type=Path);a.add_argument('--render',type=Path,required=True);a.add_argument('--chapter',required=True);a.add_argument('--out',type=Path,required=True)
 a=s.add_parser('assemble');a.add_argument('plan',type=Path);a.add_argument('--bundles',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.command=='split':print(split(a.project,a.out))
 elif a.command=='package':print(json.dumps(package_render(a.project,a.render,a.chapter,a.out),ensure_ascii=False))
 else:print(json.dumps(assemble(a.plan,a.bundles,a.out),ensure_ascii=False))
if __name__=='__main__':main()
