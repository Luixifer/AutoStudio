"""Non-renderable editorial plan -> unchanged approved Director paragraphs.
Missing text/assets remain blockers, never synthetic substitutes.
"""
import argparse,copy,json,re
from pathlib import Path
from scripts.director.project import digest,load,validate

def readiness(plan,root):
 errors=[];root=Path(root)
 if plan.get('schema')!='autostudio-production-plan/1':return ['Esquema de planificación incorrecto']
 script=plan.get('script',{});project=None
 if not script.get('approved'):errors.append('Falta aprobación del guion definitivo')
 path=script.get('path')
 if not isinstance(path,str) or not path:errors.append('Falta ruta del proyecto Director con guion definitivo')
 else:
  candidate=(root/path).resolve()
  if not candidate.is_relative_to(root.resolve()):errors.append('Guion fuera del proyecto')
  elif not candidate.is_file():errors.append('No existe el guion: '+path)
  elif script.get('sha256')!=digest(candidate):errors.append('SHA-256 del guion ausente o distinto')
  else:
   try:project=load(candidate)
   except (ValueError,OSError,KeyError) as e:errors.append('Guion no válido: '+str(e))
 ids=set();shots=plan.get('shots',[])
 if not isinstance(shots,list) or not shots:return errors+['Faltan planos']
 for shot in shots:
  ident=shot.get('id','?')
  if not re.fullmatch('[A-Za-z0-9_-]{1,64}',ident) or ident in ids:errors.append('ID de plano ausente/duplicado: '+ident)
  ids.add(ident)
  for field in ('scene_id','start_phrase','end_phrase'):
   if not shot.get(field):errors.append(ident+': falta '+field)
  if shot.get('classification') not in ('archive','recreation','visualization','hypothesis'):errors.append(ident+': clasificación editorial ausente')
  media=shot.get('media',{});path=media.get('path');rights=media.get('rights',{})
  if not path:errors.append(ident+': falta recurso exacto')
  if not rights.get('license') or not rights.get('credit'):errors.append(ident+': faltan licencia y procedencia')
 if plan.get('youtube_enabled') is not False:errors.append('YouTube debe permanecer desactivado')
 if project and not errors:
  try:compile_plan(plan,project,root/Path(script['path']).parent)
  except (ValueError,OSError,KeyError) as e:errors.append(str(e))
 return errors

def compile_plan(plan,project,root):
 result=copy.deepcopy(project);result['scene_policy']='paragraph/1';seen=set()
 for chapter in result['chapters']:
  for scene in chapter['scenes']:
   shots=[s for s in plan['shots'] if s['scene_id']==scene['id']]
   if not shots:raise ValueError('Faltan planos para el párrafo '+scene['id'])
   # Each original narration remains byte-for-byte unchanged.
   scene['subshots']=[{k:copy.deepcopy(v) for k,v in shot.items() if k in ('id','start_phrase','end_phrase','start_occurrence','end_occurrence','media','camera','transition','classification')} for shot in shots]
   seen.update(s['id'] for s in shots)
 if len(seen)!=len(plan['shots']):raise ValueError('Planos asignados a párrafos inexistentes o IDs repetidos')
 return validate(result,root)

def main():
 p=argparse.ArgumentParser();p.add_argument('plan',type=Path);p.add_argument('--out',type=Path);p.add_argument('--compile',type=Path);a=p.parse_args()
 plan=json.loads(a.plan.read_text());errors=readiness(plan,a.plan.parent)
 report={'ready':not errors,'errors':errors,'hessdalen_produced':False,'human_artistic_approved':False}
 if a.out:a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False,indent=2))
 if errors:raise SystemExit(2)
 if a.compile:
  script=a.plan.parent/plan['script']['path'];document=compile_plan(plan,load(script),script.parent)
  # Keep relative media paths anchored to the original project folder.
  if a.compile.resolve().parent!=script.resolve().parent:raise ValueError('Guardar junto al guion original para conservar rutas de medios')
  a.compile.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
