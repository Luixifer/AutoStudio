"""Prepare original 13 paragraphs, 26 exact visual ranges and measured Dora audio."""
import json,hashlib,argparse,shutil
from pathlib import Path
from scripts.director.engine import narrate,pcm_seconds
from scripts.director.subshots import resolve
from scripts.pepe.voice import ChildNarrator,PERFORMANCE
ROOT=Path(__file__).resolve().parents[2]
CUTS=['brillaba al sol.','«¡quiquiriquí!».','entre las flores.','no se podía cruzar.','«¡No sé volver!».','¡Voy a ayudarte!».','movió las alas y...','Pero la tabla era corta.','Nube, el conejito.','«Un pasito... y otro pasito...».','a abrazar a Pepe.','Pepe sonrió.','Bueno... ¡casi siempre!']
BRIEFS=[
('farm_wide','Presentación de granja, Pepe en cercado, colores luminosos, mañana.'),('pepe_curious','Retrato de Pepe curioso, cresta roja, ojos enormes, cola azul turquesa.'),
('pepe_call','Pepe saluda al amanecer desde el cercado; gesto alegre.'),('pio_greeting','Pío pequeño amarillo junto a Pepe; cariño, escala estable.'),
('butterfly_flowers','Mariposa azul entre flores, Pío mira con curiosidad.'),('pio_forest','Pío sigue mariposa hacia bosque; escenario amable, sin peligro explícito.'),
('stream_wide','Arroyo pequeño, puente viejo claramente cerrado al fondo, piedras y dos orillas.'),('pio_opposite','Pío en terreno seco, orilla derecha opuesta; no representar saltos peligrosos.'),
('pio_call','Pío llama desde derecha, ojos preocupados suavemente; sin angustia intensa.'),('pepe_run','Pepe corre desde granja hacia arroyo, gesto atento y protector.'),
('reassure','Pepe izquierda, Pío derecha separados por agua; gesto de tranquilidad.'),('pepe_think','Pepe piensa en la orilla izquierda; expresividad y espacio para idea.'),
('pepe_measure','Pepe evalúa distancia desde terreno seco, NO salta sobre agua.'),('pepe_stop','Pepe se detiene prudentemente, alas abiertas, orilla firme izquierda.'),
('short_board','Pepe encuentra una tabla corta junto al cobertizo.'),('boards_rope','Dos tablas y cuerda junto al cobertizo; idea alegre de Pepe.'),
('friends_arrive','Lola blanca y Nube gris de orejas rosadas llegan junto a Pepe.'),('build_crossing','Los tres colaboran en paso fantástico ancho, apoyos firmes y cuerda; Pío sigue derecha.'),
('pio_first_step','Pío da primer paso sobre paso ancho con apoyos; Pepe espera izquierda cerca.'),('pio_safe','Pío termina de cruzar hacia izquierda y pisa terreno seco junto a Pepe.'),
('hug','Pepe y Pío se abrazan en la orilla izquierda segura.'),('celebrate','Lola, Nube y mariposa celebran junto a Pepe y Pío, todos a salvo.'),
('golden_farm','Tarde dorada, granja cálida y Pepe sonriente.'),('friends_sunset','Pepe y Pío juntos contemplan el horizonte, calma y afecto.'),
('ask_before_walk','Pío avisa mirando a Pepe antes del paseo; complicidad alegre.'),('farm_final','Granja al atardecer con amigos y mariposa; final cálido sin llamadas comerciales.')]

def prepare(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);(out/'media').mkdir(exist_ok=True)
 source=ROOT/'content/pepe-el-gallo-travieso-episodio-1/guion.txt';raw=source.read_text();paragraphs=[p.strip() for p in raw.strip().split('\n\n') if p.strip()]
 if len(paragraphs)!=13:raise ValueError('El guion debe conservar 13 párrafos')
 config={'schema':'autostudio-director/1','title':'Pepe el Gallo Travieso · El gran rescate de Pío','scene_policy':'paragraph/1','youtube_enabled':False,'format':'horizontal','fps':30,'voice':{'mode':'kokoro','voice':'ef_dora'},'subtitles':{'enabled':False,'style':'documentary'}}
 scenes=[];shots=[];narrators={'ef_dora':ChildNarrator()};total=0
 for i,(text,cut) in enumerate(zip(paragraphs,CUTS)):
  split=text.index(cut)+len(cut);left=text[:split].strip();right=text[split:].strip()
  assert left and right and (left+' '+right).split()==text.split()
  scene={'id':f'pepe-e01-s{i+1:02}','narration':text,'pause_after':4 if i==12 else .45,'transition':{'type':'dissolve','seconds':.25},'subshots':[]}
  voicefolder=out/f'voice-{i+1:02}';voicefolder.mkdir(exist_ok=True);marker=voicefolder/'metadata.json'
  if marker.is_file() and json.loads(marker.read_text()).get('performance')==PERFORMANCE:
   meta=json.loads(marker.read_text());assert meta['text_sha256']==hashlib.sha256(text.encode()).hexdigest();path=voicefolder/'spoken.wav';words=meta['words']
  else:
   if marker.is_file():
    shutil.copy2(marker,voicefolder/'metadata-before-preschool.json');shutil.copy2(voicefolder/'spoken.wav',voicefolder/'spoken-before-preschool.wav')
   path,words,info=narrate(scene,config,out,voicefolder,narrators);meta={'performance':PERFORMANCE,'words':words,'voice':info,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'seconds':pcm_seconds(path)};marker.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
  target=out/'media'/f'narration-{i+1:02}.wav';shutil.copy2(path,target);scene['voice']={'mode':'file','path':'media/'+target.name,'timed_words':words}
  for j,part in enumerate((left,right)):
   n=i*2+j+1;slug,brief=BRIEFS[n-1];shot={'id':f'pepe-e01-p{n:02}','start_phrase':part,'end_phrase':part,'media':{'kind':'image','path':f'media/shot-{n:02}.png','fit':'cover','rights':{'license':'own_creation','credit':'AutoStudio; original Blender characters, scene, materials and render; no reference-sheet crops'}},'camera':{'movement':'zoom_in' if n%2==0 else 'pan_left'},'transition':{'type':'cut','seconds':0}}
   scene['subshots'].append(shot);shots.append({'id':shot['id'],'paragraph_id':scene['id'],'slug':slug,'brief':brief,'narration':part,'source_words':len(part.split()),'asset':shot['media']['path'],'production_status':'pending_render','license':'own_creation'})
  incoming=0 if i==0 else __import__('math').ceil(.25*30)/30+1/30
  duration=__import__('math').ceil((meta['seconds']+scene['pause_after']+incoming)*30)/30
  shifted=[{**w,'start':w['start']+incoming,'end':w['end']+incoming} for w in words]
  plan=resolve(scene,shifted,30,__import__('math').ceil((duration+(.25 if i<12 else 0))*30))
  for j,slot in enumerate(plan):shots[-2+j].update(narration_start=slot['narration_start'],narration_end=slot['narration_end'],visual_seconds=slot['frames']/30)
  total+=duration;scenes.append(scene);print('VOICE',i+1,round(meta['seconds'],3),'seconds',flush=True)
 config['chapters']=[{'id':'pepe-e01','title':'El gran rescate de Pío','scenes':scenes}]
 config['music']={'path':'media/pepe-original-music.wav','gain':.09,'rights':{'license':'own_creation','credit':'AutoStudio; original procedural score, no supplied MP3 used'}}
 (out/'project.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n');(out/'shots.json').write_text(json.dumps({'source_script_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scene_count':13,'shot_count':26,'measured_total_seconds':total,'original_reference_assets_available':False,'shots':shots},ensure_ascii=False,indent=2)+'\n')
 print('TOTAL_MEASURED',total,flush=True);return config
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();prepare(a.out)
