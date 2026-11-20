"""Five-minute transport/codec benchmark, explicitly NOT a documentary.

Extends measured speech from the short technical fixture, with exact copied
sample/timing offsets. Repetition is intentional for load testing, not editing.
"""
import argparse,copy,json,shutil,wave
from pathlib import Path
from scripts.director.engine import join_wavs,pcm_seconds,produce

def create(input_project,short_render,out):
 source=Path(input_project);short=Path(short_render);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 data=json.loads(source.read_text());timeline=json.loads((short/'timeline.json').read_text());(out/'media').mkdir(exist_ok=True)
 def copy_media(obj):
  if isinstance(obj,dict):
   if 'path' in obj:
    src=source.parent/obj['path'];dest=out/'media'/src.name;shutil.copy2(src,dest);obj['path']='media/'+src.name
   for v in obj.values():copy_media(v)
  elif isinstance(obj,list):
   for v in obj:copy_media(v)
 copy_media(data)
 base=short/'narration.wav';seconds=pcm_seconds(base);repeat=max(1,round(100/seconds));narration=out/'media/benchmark-voice.wav';join_wavs([base]*repeat,narration)
 words=[]
 for r in range(repeat):
  for scene in timeline['scenes']:
   words.extend({**w,'start':w['start']+scene['start']+r*seconds,'end':w['end']+scene['start']+r*seconds} for w in scene['words'])
 scenes=data['chapters'][0]['scenes']
 for scene in scenes:
  scene['narration']=' '.join(w['word'] for w in words);scene['voice']={'mode':'file','path':'media/benchmark-voice.wav','timed_words':words}
 data['title']='BENCHMARK ~5 MIN · REPETICIÓN INTENCIONAL · NO HESSDALEN'
 path=out/'project.json';path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');return path
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('--short-render',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();path=create(a.project,a.short_render,a.out/'input');produce(path,a.out/'render')
