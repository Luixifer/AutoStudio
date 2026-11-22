"""Independent checks on the ACTUAL final MP4, not only source audio or mocks."""
import argparse,json,subprocess,hashlib,wave
from pathlib import Path
import numpy as np
from scripts.director.project import probe,digest
from scripts.director.audio import pcm

def verify(root,render,out):
 root=Path(root);render=Path(render);movie=render/'documental-REVISION.mp4';p=json.loads((root/'project.json').read_text());timeline=json.loads((render/'timeline.json').read_text());qa=json.loads((render/'validation.json').read_text());original=Path('content/pepe-el-gallo-travieso-episodio-1/guion.txt').read_text().strip().split('\n\n');scenes=timeline['scenes'];errors=[]
 if not qa.get('passed'):errors.append('Director technical QA failed')
 original_preserved=[s['original_text'] for s in scenes]==[v.strip() for v in original]
 if not original_preserved:errors.append('Original thirteen paragraphs changed or reordered')
 slots=[s for scene in scenes for s in scene.get('subshots',[])];expected=[f'pepe-e01-p{i:02}' for i in range(1,27)]
 if [s['id'] for s in slots]!=expected:errors.append('Twenty-six shot order differs')
 source_hashes=[]
 for s in slots:
  current=digest(root/s['media']['path']);source_hashes.append(current)
  if s['input_media_sha256']!=current:errors.append('Resource modified: '+s['id'])
 if len(set(source_hashes))!=26:errors.append('Repeated active shot resource')
 subtitle_exact=' '.join(c['text'] for c in timeline['cues']).split()==' '.join(original).split()
 if not subtitle_exact:errors.append('Subtitles differ from original narration')
 detail=probe(movie);video=next(s for s in detail['streams'] if s['codec_type']=='video');audio=next(s for s in detail['streams'] if s['codec_type']=='audio');duration=float(detail['format']['duration'])
 if (video['width'],video['height'],video['codec_name'],video['avg_frame_rate'])!=(1920,1080,'h264','30/1') or audio['codec_name']!='aac':errors.append('Incorrect format')
 if abs(duration-timeline['duration'])>.12:errors.append('Duration not driven by measured narration')
 decoder=subprocess.run(['ffmpeg','-v','error','-nostdin','-xerror','-i',str(movie),'-f','null','-'],capture_output=True,timeout=900)
 if decoder.returncode or decoder.stderr.strip():errors.append('Full independent decode failed')
 black=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-i',str(movie),'-vf','blackdetect=d=0.10:pix_th=0.06:pic_th=0.995','-an','-f','null','-'],capture_output=True,text=True,timeout=900)
 black_found=[line.strip() for line in black.stderr.splitlines() if 'black_start:' in line]
 if black_found:errors.append('Unexpected black interval')
 # This is deliberately the decoded AAC from the final film, not its dry WAV.
 decoded=subprocess.run(['ffmpeg','-v','error','-nostdin','-i',str(movie),'-vn','-ac','1','-ar','16000','-f','f32le','pipe:1'],capture_output=True,check=True,timeout=900);mixed=np.frombuffer(decoded.stdout,'<f4');dry=pcm(render/'narration.wav',600);checks=[]
 for scene in scenes:
  a=round(scene['narration_start']*16000)+800;b=min(round(scene['narration_end']*16000)-800,len(dry));voice=dry[a:b];scores=[]
  for lag in range(-3,4):
   heard=mixed[max(0,a+lag):max(0,a+lag)+len(voice)]
   if len(heard)==len(voice) and np.std(heard)>1e-7:scores.append(float(np.corrcoef(voice,heard)[0,1]))
  correlation=max(scores,default=0);checks.append({'scene_id':scene['id'],'decoded_final_aac_correlation_to_original_voice':round(correlation,6),'passed':correlation>.90})
  if correlation<=.90:errors.append('Wrong/missing narration in final AAC: '+scene['id'])
 peak=float(np.max(np.abs(mixed)));clipped=int(np.sum(np.abs(mixed)>=.999))
 if clipped:errors.append('Digital clipping in final movie')
 result={'passed':not errors,'errors':errors,'actual_mp4_sha256':digest(movie),'bytes':movie.stat().st_size,'duration_seconds':duration,'timeline_measured_seconds':timeline['duration'],'width':video['width'],'height':video['height'],'fps':video['avg_frame_rate'],'video_codec':video['codec_name'],'audio_codec':audio['codec_name'],'audio_channels':audio['channels'],'full_decode_passed':decoder.returncode==0 and not decoder.stderr.strip(),'black_intervals':black_found,'paragraphs':len(scenes),'active_subshots':len(slots),'unique_active_resources':len(set(source_hashes)),'original_script_preserved':original_preserved,'subtitle_text_matches_original':subtitle_exact,'final_aac_peak':peak,'digital_clipping_samples':clipped,'final_mixed_aac_checks':checks,'character_animation_scope':'One actual 3D crossing (P20), other shots are original 3D illustrations with smooth camera moves. No claim of fully animated characters throughout.','motion_source_native_canvas':[1280,720],'motion_native_fps':12,'human_full_listening_performed':False,'human_child_audience_tested':False,'samsung_physical_tested':False,'original_zip_images_or_mp3_used':False,'paid_apis_used':False,'youtube_published':False,'artistic_commercial_approval':False}
 out=Path(out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 if errors:raise ValueError(str(errors))
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--render',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(verify(a.input,a.render,a.out),ensure_ascii=False,indent=2))
