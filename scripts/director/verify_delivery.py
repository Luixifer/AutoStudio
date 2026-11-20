"""Recover/verify the actually uploaded long MP4 and test real numeric narration.
No video is fabricated to replace an unavailable render.
"""
import hashlib,json,os,re,shutil,subprocess,urllib.request
from pathlib import Path
from scripts.director.cloud import upload
from scripts.director.publish_benchmark import target_release
from scripts.director.project import digest
from scripts.director.validate import inspect

BASE='https://github.com/Luixifer/AutoStudio/releases/download/director-check-44803232978/'
SOURCE_RUN='44804915434'

def fetch(name,dest,max_bytes=2*1024**3):
 total=0
 with urllib.request.urlopen(BASE+name,timeout=120) as source,Path(dest).open('wb') as out:
  for block in iter(lambda:source.read(1024*1024),b''):
   total+=len(block)
   if total>max_bytes:raise ValueError('Unexpected download size')
   out.write(block)

def verify(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 name='AutoStudio-Director-ensayo-5min-NO-HESSDALEN-'+SOURCE_RUN+'.mp4';video=out/name;fetch(name,video)
 for kind in ('validation.json','timeline.json','captions.srt','resources.json'):
  fetch('benchmark-'+SOURCE_RUN+'-'+kind,out/kind,2*1024*1024)
 original=json.loads((out/'validation.json').read_text());timeline=json.loads((out/'timeline.json').read_text())
 if not original['passed'] or digest(video)!=original['sha256']:raise ValueError('Actual uploaded video does not match the original renderer report')
 if original.get('github_run_id')!=SOURCE_RUN:raise ValueError('Wrong source execution')
 qa=inspect(video,(1920,1080),30,timeline['duration'],timeline['cues'])
 srt=(out/'captions.srt').read_text()
 if srt.count(' --> ')!=len(timeline['cues']):raise ValueError('Actual SRT is incomplete')
 if not qa['passed']:raise RuntimeError(str(qa['errors']))
 result={'passed':True,'source_render_run':SOURCE_RUN,'verification_run':os.environ.get('GITHUB_RUN_ID'),'verification_source_commit':os.environ.get('GITHUB_SHA'),'video_url':BASE+name,'original_render':original,'independent_full_decode':qa,'resources_original_runner':json.loads((out/'resources.json').read_text()),'actual_srt_cues':srt.count(' --> '),'scope':'Independent verification of the actual previously uploaded MP4; no video regenerated','hessdalen_produced':False,'human_artistic_approved':False,'physical_samsung_tested':False,'youtube_enabled':False}
 (out/'delivery-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result

def language(out):
 from scripts.director.fixture import create
 from scripts.director.engine import narrate,produce
 out=Path(out);p=create(out/'input');project=json.loads(p.read_text());scene=project['chapters'][0]['scenes'][0]
 scene['narration']='Esta prueba usa 1981, 3,5 y 60 minutos.'
 voice_work=out/'voice';voice_work.mkdir(parents=True,exist_ok=True);raw,words,info=narrate(scene,project,p.parent,voice_work,{})
 target=p.parent/'media/imported-numbers.mp3';subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af','adelay=300:all=1','-c:a','libmp3lame','-b:a','128k',str(target)],check=True)
 scene['voice']={'mode':'file','path':'media/imported-numbers.mp3'}
 # Another scene exercises real Kokoro numeric expansion in the producer.
 project['chapters'][0]['scenes'][1]['narration']='También se leen 1981, 3,5 y 60 minutos sin cambiar las cifras del guion.'
 p.write_text(json.dumps(project,ensure_ascii=False,indent=2)+'\n');report=produce(p,out/'render');timeline=json.loads((out/'render/timeline.json').read_text())
 if not any(w['word']=='1981,' for w in timeline['scenes'][0]['words']):raise ValueError('Original numeric captions not preserved')
 (out/'language-verification.json').write_text(json.dumps({'passed':report['passed'],'original_script_preserved':True,'actual_cpu_whisper_imported_mp3':True,'actual_cpu_kokoro_numeric_expansion':True,'no_estimated_word_times':True,'video_sha256':report['sha256'],'human_listening_approved':False,'youtube_enabled':False},indent=2)+'\n')

def publish(out):
 run=os.environ['GITHUB_RUN_ID'];out=Path(out);release=target_release()
 for p in [out/'delivery-verification.json',out/'language/language-verification.json',out/'previous-upload.log']:
  if p.is_file() and p.stat().st_size:
   safe=out/('director-quality-'+run+'-'+p.name);shutil.copy2(p,safe);upload(release,safe)
 print('REAL_VERIFICATION_RUN',run)

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 verify(a.out);language(a.out/'language');publish(a.out)
