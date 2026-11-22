"""Decode actual assembled MP4 and compare scene frames and caption identities.
This checks correspondence to the author's manifest, not semantic truth of images.
"""
from pathlib import Path
import subprocess,math
import numpy as np
from scripts.director.project import digest

def frames(path,indices):
 indices=sorted(set(indices))
 if not indices:return {}
 # FFmpeg's evaluator rejects long left-associated sums (~100 terms).
 # Balance the exact same selected indices; never reduce the QA samples.
 terms=[f'eq(n\\,{i})' for i in indices]
 while len(terms)>1:terms=['('+terms[i]+'+'+terms[i+1]+')' if i+1<len(terms) else terms[i] for i in range(0,len(terms),2)]
 expression=terms[0]
 result=subprocess.run(['ffmpeg','-v','error','-nostdin','-threads','2','-i',str(path),'-vf',f'select={expression},scale=160:90','-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],capture_output=True,check=True,timeout=1800)
 expected=len(indices)*160*90*3
 if len(result.stdout)!=expected:raise ValueError('Faltan fotogramas reales para comprobar escenas')
 return dict(zip(indices,np.frombuffer(result.stdout,np.uint8).reshape(-1,90,160,3)))

def inspect_correspondence(video,scenes,cache,fps,cues,root):
 requested={};errors=[];reports=[];units={}
 for scene in scenes:
  slots=scene.get('subshots') or [{'id':scene['id'],'narration_start':scene['narration_offset'],'narration_end':scene['narration_offset']+scene['voice_seconds'],'start_frame':0}]
  for slot in slots:
   a,b=scene['start']+slot['narration_start'],scene['start']+slot['narration_end'];span=b-a
   times=[a+min(.04,span/10),a+span*.25,a+span*.5,a+span*.75,b-min(.04,span/10)]
   requested[slot['id']]=sorted(set(math.ceil(t*fps-1e-7) for t in times if t<b));units[slot['id']]=(scene,slot)
 from scripts.director.audio import pcm
 audio=pcm(Path(video).parent/'narration.wav')
 actual=frames(video,[index for values in requested.values() for index in values])
 for scene in scenes:
  sid=scene['id'];measurements=[];shot_reports=[]
  slots=scene.get('subshots') or [units[sid][1]]
  for slot in slots:
   origin=round(scene['start']*fps)+slot['start_frame'];indices=requested[slot['id']]
   reference_path=Path(cache).parent/'visual-cache'/slot['video_key']/'visual.mp4' if 'video_key' in slot else Path(cache)/scene['key']/'visual.mp4'
   reference=frames(reference_path,[i-origin for i in indices]);own_frames=[]
   for index in indices:
    observed=actual[index][14:64,8:152].astype(np.float32);expected=reference[index-origin][14:64,8:152].astype(np.float32)
    mae=float(np.abs(observed-expected).mean()/255);value={'time':index/fps,'subshot_id':slot['id'],'mean_absolute_error':round(mae,6),'passed':mae<.055};measurements.append(value);own_frames.append(value)
   path=slot.get('media',{}).get('path',scene['media_path']);sha=slot.get('input_media_sha256',scene['input_media_sha256']);source_valid=digest(Path(root)/path)==sha
   if not source_valid:errors.append('Fuente de subplano modificada: '+slot['id'])
   shot_reports.append({'id':slot['id'],'frames':own_frames,'input_hash_valid':source_valid,'media_path':path,'passed':source_valid and all(v['passed'] for v in own_frames)})
  own=[c for c in cues if c.get('scene_id')==sid]
  text_ok=' '.join(c['text'] for c in own).split()==scene['original_text'].split()
  bounds_ok=all(scene['narration_start']-.002<=c['start']<c['end']<=scene['narration_end']+.03 for c in own)
  source_ok=all(s['input_hash_valid'] for s in shot_reports)
  original=pcm(Path(cache)/scene['key']/'spoken.wav',600)
  trim=min(480,max(1,len(original)//20));expected_audio=original[trim:-trim];start=round(scene['narration_start']*16000)+trim
  correlations=[]
  for lag in range(-2,3):
   piece=audio[max(0,start+lag):max(0,start+lag)+len(expected_audio)]
   if len(piece)==len(expected_audio) and np.std(piece)>1e-7 and np.std(expected_audio)>1e-7:correlations.append(float(np.corrcoef(piece,expected_audio)[0,1]))
  audio_match=max(correlations,default=0);audio_ok=audio_match>.95
  passed=all(m['passed'] for m in measurements) and text_ok and bounds_ok and source_ok and audio_ok
  if not passed:errors.append('Correspondencia de escena rechazada: '+sid)
  reports.append({'id':sid,'position':scene['position'],'media':scene['media_path'],'media_sha256':scene['input_media_sha256'],'original_text':scene['original_text'],'narration_start':scene['narration_start'],'narration_end':scene['narration_end'],'voice_seconds':scene['voice_seconds'],'visual_seconds':scene['duration'],'frames':measurements,'subshots':shot_reports,'caption_text_exact':text_ok,'caption_bounds_valid':bounds_ok,'input_hash_valid':source_ok,'assembled_narration_correlation':round(audio_match,6),'assembled_narration_matches':audio_ok,'passed':passed})
 return {'schema':'scene-correspondence/1','passed':not errors,'errors':errors,'scenes':reports,'scope':'Decoded samples at beginning, quarter, middle, three quarters and end of every narration; compared to its source-bound scene render. Not semantic image analysis or human listening approval.','human_approved':False}
