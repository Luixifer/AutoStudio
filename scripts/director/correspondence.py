"""Decode actual assembled MP4 and compare scene frames and caption identities.
This checks correspondence to the author's manifest, not semantic truth of images.
"""
from pathlib import Path
import subprocess,math
import numpy as np
from scripts.director.project import digest

def frames(path,indices):
 indices=sorted(set(indices));expression='+'.join(f'eq(n\\,{i})' for i in indices)
 result=subprocess.run(['ffmpeg','-v','error','-nostdin','-threads','2','-i',str(path),'-vf',f'select={expression},scale=160:90','-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],capture_output=True,check=True,timeout=1800)
 expected=len(indices)*160*90*3
 if len(result.stdout)!=expected:raise ValueError('Faltan fotogramas reales para comprobar escenas')
 return dict(zip(indices,np.frombuffer(result.stdout,np.uint8).reshape(-1,90,160,3)))

def inspect_correspondence(video,scenes,cache,fps,cues,root):
 requested={};errors=[];reports=[]
 for scene in scenes:
  a,b=scene['narration_start'],scene['narration_end'];span=b-a
  times=[a+min(.04,span/10),a+span*.25,a+span*.5,a+span*.75,b-min(.04,span/10)]
  requested[scene['id']]=sorted(set(math.ceil(t*fps-1e-7) for t in times if t<b))
 from scripts.audio_ai_qa import pcm16
 audio=pcm16(Path(video).parent/'narration.wav')
 actual=frames(video,[index for values in requested.values() for index in values])
 for scene in scenes:
  sid=scene['id'];start_frame=round(scene['start']*fps);indices=requested[sid]
  reference=frames(Path(cache)/scene['key']/'visual.mp4',[i-start_frame for i in indices])
  measurements=[]
  for index in indices:
   # Stationary titles and subtitles are outside this comparison region.
   observed=actual[index][14:64,8:152].astype(np.float32)
   expected=reference[index-start_frame][14:64,8:152].astype(np.float32)
   mae=float(np.abs(observed-expected).mean()/255)
   measurements.append({'time':index/fps,'mean_absolute_error':round(mae,6),'passed':mae<.055})
  own=[c for c in cues if c.get('scene_id')==sid]
  text_ok=' '.join(c['text'] for c in own).split()==scene['original_text'].split()
  bounds_ok=all(scene['narration_start']-.002<=c['start']<c['end']<=scene['narration_end']+.03 for c in own)
  source_ok=digest(Path(root)/scene['media_path'])==scene['input_media_sha256']
  original=pcm16(Path(cache)/scene['key']/'spoken.wav')
  trim=min(480,max(1,len(original)//20));expected_audio=original[trim:-trim];start=round(scene['narration_start']*16000)+trim
  correlations=[]
  for lag in range(-2,3):
   piece=audio[max(0,start+lag):max(0,start+lag)+len(expected_audio)]
   if len(piece)==len(expected_audio) and np.std(piece)>1e-7 and np.std(expected_audio)>1e-7:correlations.append(float(np.corrcoef(piece,expected_audio)[0,1]))
  audio_match=max(correlations,default=0);audio_ok=audio_match>.95
  passed=all(m['passed'] for m in measurements) and text_ok and bounds_ok and source_ok and audio_ok
  if not passed:errors.append('Correspondencia de escena rechazada: '+sid)
  reports.append({'id':sid,'position':scene['position'],'media':scene['media_path'],'media_sha256':scene['input_media_sha256'],'original_text':scene['original_text'],'narration_start':scene['narration_start'],'narration_end':scene['narration_end'],'voice_seconds':scene['voice_seconds'],'visual_seconds':scene['duration'],'frames':measurements,'caption_text_exact':text_ok,'caption_bounds_valid':bounds_ok,'input_hash_valid':source_ok,'assembled_narration_correlation':round(audio_match,6),'assembled_narration_matches':audio_ok,'passed':passed})
 return {'schema':'scene-correspondence/1','passed':not errors,'errors':errors,'scenes':reports,'scope':'Decoded samples at beginning, quarter, middle, three quarters and end of every narration; compared to its source-bound scene render. Not semantic image analysis or human listening approval.','human_approved':False}
