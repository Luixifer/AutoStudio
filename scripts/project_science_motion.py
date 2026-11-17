"""Project authored 3D paths to image coordinates for inexpensive 2D motion overlays.
Run with Blender after create_science_art.py. No extra renders or invented trajectories.
"""
import bpy,sys,json
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector,Matrix
ROOT=Path(sys.argv[sys.argv.index('--')+1])
prefixes={'auroras':['Solar wind trajectory','Illustrative magnetic field','Auroral oval','Light packet illustration','Incoming charged particle'], 'dna':['DNA backbone','Temporary RNA message','RNA entering ribosome','Emerging polypeptide'], 'volcanoes':['Magma ascent schematic','Incandescent lava channel','Ejected glowing fragment','More mobile flow illustration','More viscous flow illustration']}
for topic,wanted in prefixes.items():
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'sources/science_v04/{topic}_master_v001.blend'))
 file=ROOT/f'assets/science_v04/{topic}/manifest.json';manifest=json.loads(file.read_text())
 for asset in manifest['assets']:
  index=int(asset['id'].rsplit('_',1)[1]);scene=bpy.data.scenes[f'{topic}_{index}'];bpy.context.window.scene=scene;bpy.context.view_layer.update();camera=scene.camera.copy();camera.matrix_world=Matrix.LocRotScale(scene.camera.location,scene.camera.rotation_euler.to_quaternion(),scene.camera.scale);paths=[]
  for obj in scene.objects:
   if obj.type!='CURVE' or not any(obj.name.startswith(p) for p in wanted):continue
   points=[];visibility=[];has_earth=any(o.name.startswith('Stylized Earth') for o in scene.objects)
   for p in obj.data.splines[0].points:
    co=world_to_camera_view(scene,camera,obj.matrix_world@Vector(p.co[:3]))
    if co.z>0:
     points.append([round(co.x,6),round(1-co.y,6)])
     point=obj.matrix_world@Vector(p.co[:3]);origin=scene.camera.location;direction=point-origin;offset=origin-Vector((0,0,2.7));u=-offset.dot(direction)/max(direction.length_squared,1e-12)
     hidden=has_earth and 0<u<1 and (offset+direction*u).length<2.1
     visibility.append(not hidden)
   if len(points)>=2:paths.append({'name':obj.name,'points':points,'visible':visibility})
  asset['motion_paths']=paths[:12]
 file.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('PROJECTED_MOTION_PATHS',topic,sum(len(a['motion_paths']) for a in manifest['assets']),flush=True)
