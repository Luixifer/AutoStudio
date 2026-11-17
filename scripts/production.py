"""Versioned production request and scene plan. Uses the existing renderer unchanged in scope."""
import argparse,hashlib,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.providers import get_script_provider,LocalImageProvider
REQUEST_ID=re.compile(r'[a-f0-9]{32}')

def request_id(value):
    if not isinstance(value,str) or not REQUEST_ID.fullmatch(value):raise ValueError('Identificador de trabajo inválido; se requieren 32 caracteres hexadecimales.')
    return value

def build_plan(topic,identifier,provider='curated-local-v1',format='short'):
    request_id(identifier)
    if not isinstance(topic,str) or not 3<=len(topic.strip())<=160 or any(ord(c)<32 for c in topic):raise ValueError('El tema debe tener entre 3 y 160 caracteres, sin controles.')
    if format!='short':raise ValueError('Documentales todavía no habilitados; solo Shorts.')
    story=get_script_provider(provider).create(topic.strip());images=LocalImageProvider();scenes=[]
    for i,s in enumerate(story['scenes'],1):
        asset=images.resolve(s['asset']);sid=f's{i:02}'
        s['scene_id']=sid
        scenes.append({'id':sid,'narration':s['voice'],'duration':{'mode':'actual_audio_plus_pause','seconds':None},'media':{'provider':images.id,'asset_id':s['asset'],'file':asset['file'],'sha256':asset['sha256']},'subtitles':{'mode':'model_word_durations','max_words':3},'effects':{'camera':s['camera'],'particles':'subtle'},'transition':{'type':'crossfade_from_previous','seconds':.18 if i>1 else 0}})
    plan={'schema':1,'request_id':identifier,'topic':topic.strip(),'format':'short','script_provider':provider,'image_provider':images.id,'scenes':scenes,'youtube':{'enabled':False},'paid_api_allowed':False}
    story['production']={'request_id':identifier,'topic':topic.strip(),'schema':1,'format':'short','script_provider':provider}
    return story,plan

def main():
    p=argparse.ArgumentParser();p.add_argument('--topic',default=os.environ.get('AUTOSTUDIO_TOPIC'));p.add_argument('--request-id',default=os.environ.get('AUTOSTUDIO_REQUEST_ID'));p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    identifier=request_id(a.request_id);story,plan=build_plan(a.topic,identifier)
    directory=ROOT/'output/requests'/identifier;directory.mkdir(parents=True,exist_ok=True)
    (directory/'story.json').write_text(json.dumps(story,ensure_ascii=False,indent=2)+'\n');(directory/'scene-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    if not a.prepare_only:
        subprocess.run([sys.executable,str(ROOT/'scripts/render.py'),'--profile','cinematic','--script',str(directory/'story.json'),'--out',str(ROOT/'output')],check=True)
        out=Path(json.loads((ROOT/'output/latest.json').read_text())['directory'])
        metadata=json.loads((out/'metadata.json').read_text());cursor=0
        for scene,actual in zip(plan['scenes'],metadata['scenes']):
            scene['duration']['seconds']=actual['video_seconds'];scene['voice_seconds']=actual['voice_seconds'];scene['timeline_start_seconds']=round(cursor,6);cursor+=actual['video_seconds']
        (out/'story.json').write_bytes((directory/'story.json').read_bytes())
        (out/'scene-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
        print('PRODUCTION_REQUEST_CONFIRMED',identifier)
if __name__=='__main__':main()
