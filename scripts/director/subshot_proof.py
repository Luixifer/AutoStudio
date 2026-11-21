"""Short real narration/render regression, explicitly NOT Hessdalen content."""
import json,shutil
from pathlib import Path
from scripts.director.engine import produce
from scripts.director.project import digest
ROOT=Path(__file__).resolve().parents[2]
def main():
 root=ROOT/'reports/subshot-proof';media=root/'media';media.mkdir(parents=True,exist_ok=True)
 texts=['Esta prueba técnica comprueba un único párrafo con varios planos.','La narración continúa mientras cambia únicamente la imagen asignada.','El resultado no es un capítulo de Hessdalen ni una aprobación editorial.']
 assets=['auroras/auroras_01.jpg','dna/dna_01.jpg','volcanoes/volcanoes_01.jpg']
 shots=[]
 for i,(text,asset) in enumerate(zip(texts,assets)):
  path=media/f'{i}.jpg';shutil.copy2(ROOT/'assets/science_v04'/asset,path)
  shots.append({'id':f'proof-shot-{i}','start_phrase':text,'end_phrase':text,'media':{'kind':'image','path':'media/'+path.name,'fit':'blur','rights':{'license':'own_creation','credit':'AutoStudio original technical fixture; not Hessdalen footage'}},'camera':{'movement':'zoom_in'},'transition':{'type':'cut','seconds':0}})
 project={'schema':'autostudio-director/1','scene_policy':'paragraph/1','title':'ENSAYO DE SUBPLANOS — NO HESSDALEN','youtube_enabled':False,'format':'horizontal','fps':30,'voice':{'mode':'kokoro','voice':'em_alex'},'subtitles':{'enabled':True,'style':'documentary'},'chapters':[{'id':'proof','scenes':[{'id':'one-paragraph','narration':' '.join(texts),'subshots':shots,'pause_after':.3}]}]}
 path=root/'project.json';path.write_text(json.dumps(project,ensure_ascii=False,indent=2)+'\n');out=root/'render';events=[]
 first=produce(path,out,checkpoint=lambda out:events.append('chapter_completed'));first_t=json.loads((out/'timeline.json').read_text());voice_hash=digest(out/'narration.wav')
 shutil.copy2(ROOT/'assets/science_v04/dna/dna_06.jpg',media/'1.jpg')
 second=produce(path,out);second_t=json.loads((out/'timeline.json').read_text());scene=second_t['scenes'][0];flags=[s['cache_reused'] for s in scene['subshots']]
 assert first['passed'] and second['passed'] and flags==[True,False,True] and scene['voice']['cache_reused'] and digest(out/'narration.wav')==voice_hash and events==['chapter_completed']
 # Full scene cache can move between runner directories without stale absolute refs.
 relocated=root/'different-runner';shutil.copytree(out,relocated,dirs_exist_ok=True)
 third=produce(path,relocated);third_t=json.loads((relocated/'timeline.json').read_text())
 assert third['passed'] and third_t['scenes'][0]['scene_cache_reused']
 report={'passed':True,'is_hessdalen':False,'source_commit':__import__('os').environ.get('GITHUB_SHA'),'resolution':[second['width'],second['height']],'duration':second['duration'],'one_paragraph':len(second_t['scenes'])==1,'one_unchanged_narration':voice_hash==digest(out/'narration.wav'),'subshot_count':len(scene['subshots']),'only_changed_visual_rerendered':flags,'relocated_cache_verified':True,'chapter_checkpoint_called':events,'correspondence':second['correspondence'],'human_listening_performed':False,'voice_naturalness_approved':False,'samsung_tested':False,'youtube_enabled':False}
 target=ROOT/'reports/director/subshot-proof.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
