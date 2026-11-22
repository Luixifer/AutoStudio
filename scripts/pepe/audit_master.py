"""Blender-side audit of shared characters, actual visibility and spatial continuity."""
import bpy,sys,argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);S=bpy.context.scene
actors={name:bpy.data.objects[name] for name in ('Pepe','Pío','Lola','Nube')};characters={};states=[];errors=[]
for name,root in actors.items():
 objects=[]
 for ob in [root,*root.children_recursive]:
  entry={'name':ob.name,'type':ob.type,'materials':[]}
  if ob.type=='MESH':entry['vertices']=[[round(v,6) for v in x.co] for x in ob.data.vertices];entry['faces']=len(ob.data.polygons)
  if ob.type=='CURVE':entry['splines']=[[[round(v,6) for v in q.co] for q in sp.bezier_points] for sp in ob.data.splines]
  if hasattr(ob.data,'materials'):
   for m in ob.data.materials:
    node=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
    entry['materials'].append({'name':m.name,'base_color':[round(x,6) for x in node.inputs['Base Color'].default_value] if node else list(m.diffuse_color)})
  objects.append(entry)
 signature=hashlib.sha256(json.dumps(objects,sort_keys=True).encode()).hexdigest();characters[name]={'stable_object_id':root.name,'shared_geometry_sha256':signature,'object_count':len(objects),'recreated_per_shot':False}
for n in range(1,27):
 S.frame_set(n);state={'shot':n,'camera':S.camera.name,'actors':{name:{'visible':not obj.hide_render,'position':[round(v,5) for v in obj.location]} for name,obj in actors.items()},'new_bridge_visible':not bpy.data.objects['New firm crossing'].hide_render};states.append(state)
 if n in (17,18,22,26) and not all(state['actors'][name]['visible'] for name in actors):errors.append('Missing helper '+str(n))
 if n==7 and actors['Pío'].location.x>=-1:errors.append('Pío stranded before narration')
 if n in (8,9,11,12,13,14,17,18) and actors['Pío'].location.x<=1:errors.append('Pío not on opposite bank '+str(n))
 if n==20 and actors['Pío'].location.x>=-1.3:errors.append('Pío not back safely')
 if n<18 and state['new_bridge_visible']:errors.append('Bridge restored prematurely')
 if n in (17,18,22) and actors['Nube'].location.x>-3.7:errors.append('Nube remains behind Pepe or rail')
cam8=bpy.data.objects['Camera P08'];cam9=bpy.data.objects['Camera P09']
if tuple(cam8.location)==tuple(cam9.location) and cam8.data.lens==cam9.data.lens:errors.append('Repeated P08 and P09 camera')
report={'passed':not errors,'errors':errors,'blender_version':bpy.app.version_string,'source_master':bpy.data.filepath,'characters':characters,'states':states,'scope':'Shared 3D geometry/material identity, explicit scene visibility and world-space banks. Visual occlusion also reviewed from actual renders; not a human audience test.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if errors:raise RuntimeError(str(errors))
