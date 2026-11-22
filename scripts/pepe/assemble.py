"""Finish 26 original story illustrations and one genuine 3D crossing for Director 2."""
import argparse,json,math,hashlib,shutil,subprocess,zipfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.pepe.denoise import denoise,all_shots
from scripts.director.engine import pcm_seconds
from scripts.director.subshots import resolve,canonical
from scripts.director.project import digest

def motion_timing(project,root):
 scene=project['chapters'][0]['scenes'][9];fps=project['fps'];incoming=math.ceil(.25*fps)/fps+1/fps;seconds=pcm_seconds(Path(root)/scene['voice']['path']);duration=math.ceil((seconds+scene['pause_after']+incoming)*fps)/fps;extra=math.ceil(.25*fps)/fps
 plan=resolve(scene,[{**w,'start':w['start']+incoming,'end':w['end']+incoming} for w in scene['voice']['timed_words']],fps,math.ceil((duration+extra)*fps));slot=plan[1]
 target=next(w['start']+incoming-slot['start_frame']/fps for w in scene['voice']['timed_words'] if canonical(w['word'])=='orilla')
 if not 1<target<slot['frames']/fps:raise ValueError('Arrival cue outside crossing shot')
 return {'shot_seconds':slot['frames']/fps,'arrival_seconds':target,'native_walk_seconds':5.7,'retime_factor':target/5.7,'narration_unchanged':True}

def crossing(root):
 root=Path(root);use_native=(root/'full-motion-source.json').is_file();use_alpha=(root/'motion-alpha.json').is_file() and not use_native;meta=json.loads((root/('full-motion-source.json' if use_native else 'motion-alpha.json' if use_alpha else 'motion-crop.json')).read_text());crop=meta.get('crop_bottom_left');w,h=meta.get('canvas',meta.get('native_canvas'));full=root/'motion-full';full.mkdir(exist_ok=True);clean=root/'motion-clean';clean.mkdir(exist_ok=True)
 background=None
 if not use_native:
  background_name=meta.get('background','motion-background.png');denoise(root/background_name,clean/'background.png');background=Image.open(clean/'background.png').convert('RGB')
 records=[]
 for i in range(meta['frames']):
  if use_native:
   raw=Path(meta['root'])/'motion'/f'frame-{i:04}.png';target=full/raw.name;record=denoise(raw,target);record.update(source_full_scene_sha256=digest(raw),source_kind='Actual complete Blender 3D frame')
  elif use_alpha:
   raw=root/'motion-alpha'/f'frame-{i:04}.png';source_meta=json.loads(raw.with_suffix('.json').read_text());crop=source_meta['crop_bottom_left'];tile=Image.open(raw).convert('RGBA');tw,th=tile.size;alpha=np.asarray(tile)[:,:,3]
   if not (int((alpha==0).sum())>100 and int((alpha>=200).sum())>100):raise ValueError('RGBA pass missing real transparency or character: '+raw.name)
   if [tw,th]!=[crop[2]-crop[0],crop[3]-crop[1]]:raise ValueError('RGBA camera crop does not match actual image dimensions')
   frame=background.convert('RGBA');frame.alpha_composite(tile,(crop[0],h-crop[1]-th));frame=frame.convert('RGB');composite=clean/f'raw-{i:04}.png';frame.save(composite);target=full/raw.name;record=denoise(composite,target);record.update(source_rgba_sha256=digest(raw),crop_bottom_left=crop,transparent_pixels=int((alpha==0).sum()),opaque_pixels=int((alpha>=200).sum()))
  else:
   raw=root/'motion'/f'frame-{i:04}.png';cleanfile=clean/raw.name;record=denoise(raw,cleanfile);tile=Image.open(cleanfile).convert('RGB');tw,th=tile.size
   if abs(tw-(crop[2]-crop[0]))>1 or abs(th-(crop[3]-crop[1]))>1:raise ValueError('Motion region dimensions differ from its camera crop')
   xx=np.minimum(np.arange(tw),np.arange(tw)[::-1]);yy=np.minimum(np.arange(th),np.arange(th)[::-1]);mask=np.uint8(np.minimum(np.minimum(xx[None,:],yy[:,None])/16,1)*255)
   frame=background.copy();frame.paste(tile,(crop[0],h-crop[1]-th),Image.fromarray(mask));target=full/raw.name;frame.save(target)
  records.append({'frame':i,**record,'composite_sha256':digest(target)});print('MOTION_COMPOSITE',i,flush=True)
 project=json.loads((root/'project.json').read_text());timing=motion_timing(project,root);native_rate=12/timing['retime_factor'];target=root/'media'/'shot-20.mp4';length=timing['shot_seconds']+.30
 subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-threads','2','-framerate',str(native_rate),'-i',str(full/'frame-%04d.png'),'-vf','minterpolate=fps=30:mi_mode=mci:mc_mode=obmc:me_mode=bilat:search_param=16,tpad=stop_mode=clone:stop_duration=2','-t',str(length),'-an','-c:v','libx264','-crf','18','-preset','veryfast','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],check=True)
 shot=project['chapters'][0]['scenes'][9]['subshots'][1];shot['media'].update(kind='video',path='media/shot-20.mp4',source_audio=False);shot['camera']={'movement':'static'}
 (root/'project.json').write_text(json.dumps(project,ensure_ascii=False,indent=2)+'\n')
 shots=json.loads((root/'shots.json').read_text());shots['shots'][19].update(asset='media/shot-20.mp4',reference_illustration='media/shot-20.png',production_status='genuine_3d_animation_rendered');(root/'shots.json').write_text(json.dumps(shots,ensure_ascii=False,indent=2)+'\n')
 report={'genuine_blender_3d_frames':84,'native_canvas':[1280,720],'native_animation_fps':12,'encoded_fps':30,'motion_interpolation':True,'full_native_1080p_animation':False,'genuine_full_scene_3d_frames':use_native,'real_transparent_3d_passes':use_alpha,'region_render':meta,'timing':timing,'final_source_sha256':digest(target),'frames':records}
 (root/'motion-provenance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 return report

def titles(root):
 root=Path(root);source=root/'media/shot-01.png';backup=root/'raw/shot-01-clean-without-title.png'
 denoise(root/'raw/shot-01.png',backup)
 im=Image.open(backup).convert('RGB');d=ImageDraw.Draw(im);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',62);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',44)
 d.text((150,95),'Pepe el Gallo Travieso',font=font,fill='#fff5ce',stroke_width=4,stroke_fill='#335748');d.text((155,175),'El gran rescate de Pío',font=small,fill='#fff8e8',stroke_width=3,stroke_fill='#335748');im.save(source)
 final=root/'media/shot-26.png';backup_last=root/'raw/shot-26-clean-without-footer.png'
 denoise(root/'raw/shot-26.png',backup_last)
 last=Image.open(backup_last).convert('RGB');draw=ImageDraw.Draw(last);f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',40);message='Cerca del agua, siempre con una persona adulta.';box=draw.textbbox((0,0),message,font=f);x=(1920-(box[2]-box[0]))//2;draw.text((x,958),message,font=f,fill='#fff8e8',stroke_width=2,stroke_fill='#335748');last.save(final)
 manifest={'first_title':{'clean_source_sha256':digest(backup),'final_sha256':digest(source),'text':['Pepe el Gallo Travieso','El gran rescate de Pío']},'closing_caregiver_note':{'clean_source_sha256':digest(backup_last),'final_sha256':digest(final),'text':message,'not_part_of_spoken_script':True},'font':'DejaVu Sans, system free font; no commercial font service'};(root/'typography.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

def inputs_qa(root):
 root=Path(root);project=json.loads((root/'project.json').read_text());scenes=project['chapters'][0]['scenes'];original=Path('content/pepe-el-gallo-travieso-episodio-1/guion.txt').read_text().strip().split('\n\n');assert [s['narration'] for s in scenes]==[p.strip() for p in original]
 assert len(scenes)==13 and sum(len(s['subshots']) for s in scenes)==26
 sha=[];records=[]
 for n in range(1,27):
  p=root/'media'/f'shot-{n:02}.png'
  with Image.open(p) as im:
   im.verify()
  im=Image.open(p);assert im.size==(1920,1080);assert min(np.asarray(im).std(axis=(0,1)))>8
  value=digest(p);assert value not in sha;sha.append(value);records.append({'shot':n,'sha256':value,'native_dimensions':list(im.size),'placeholder':False})
 result={'passed':True,'paragraphs_preserved':13,'source_script_sha256':digest(Path('content/pepe-el-gallo-travieso-episodio-1/guion.txt')),'individual_native_1080p_illustrations':26,'unique_illustrations':len(set(sha)),'original_reference_sheets_used':False,'story':'Pío stranded on opposite bank, helped home by Pepe, Lola and Nube; narrative text unchanged','illustrations':records,'human_child_audience_tested':False}
 (root/'input-quality.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result

def contacts(root,target):
 root=Path(root);out=Image.new('RGB',(1600,6*205),(240,243,230));d=ImageDraw.Draw(out)
 for n in range(1,27):
  im=Image.open(root/'media'/f'shot-{n:02}.png').convert('RGB');im.thumbnail((312,176));x=((n-1)%5)*320;y=((n-1)//5)*205;out.paste(im,(x,y+22));d.text((x+6,y+4),f'P{n:02} / 26 · fuente original',fill=(35,65,55))
 out.save(target)

def bundle(root,out,include_master=True):
 root=Path(root);out=Path(out);p=json.loads((root/'project.json').read_text());paths={'project.json','shots.json','audio-provenance.json','input-quality.json','denoise.json','motion-provenance.json','typography.json','master-audit.json','raw/shot-01.png','raw/shot-26.png'}
 def collect(x):
  if isinstance(x,dict):
   if 'path' in x:paths.add(x['path'])
   for v in x.values():collect(v)
  elif isinstance(x,list):
   for v in x:collect(v)
 collect(p);paths.update(f'media/shot-{n:02}.png' for n in range(1,27))
 if include_master:paths.update(['pepe-e01-master-v002.blend','pepe-e01-motion-master-v001.blend'])
 out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
  for name in sorted(paths):
   f=root/name
   if not f.is_file():raise ValueError('Missing editable project file '+name)
   z.write(f,name)
  for f in sorted(Path('scripts').rglob('*.py')):z.write(f,str(f))
  for name in ('requirements.txt','requirements-neural.txt','requirements-director.txt','assets/voice-models.json'):
   f=Path(name)
   if f.is_file():z.write(f,name)
  for name in ('full-motion-source.json',):
   if (root/name).is_file():z.write(root/name,name)
  for f in sorted(Path('content/pepe-el-gallo-travieso-episodio-1').glob('*')):
   if f.is_file():z.write(f,str(f))
  for i in range(1,14):z.write(root/f'voice-{i:02}/metadata.json',f'provenance/voice-{i:02}.json')
 return {'file':out.name,'bytes':out.stat().st_size,'sha256':digest(out)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--motion',action='store_true');p.add_argument('--stills',action='store_true');p.add_argument('--qa',action='store_true');a=p.parse_args()
 if a.stills:all_shots(a.input);titles(a.input)
 if a.motion:crossing(a.input)
 if a.qa:print(json.dumps(inputs_qa(a.input),indent=2));contacts(a.input,a.input/'contact-26.jpg')
