"""Actual animated 3D Pío and contact shadows in transparent Cycles passes.
Input is our complete original .blend, never a sprite cut from a reference sheet.
"""
import bpy,json,time,sys,argparse,hashlib,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--frames',type=int,nargs='+');p.add_argument('--samples',type=int,default=12);p.add_argument('--background',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.input.resolve();S=bpy.context.scene;pio=bpy.data.objects['Pío'];bridge=bpy.data.objects['New firm crossing'];actor={pio,*pio.children_recursive};proxies={bridge,*bridge.children_recursive};ground=bpy.data.objects['Single meadow terrain'];w,h=1280,720;target=root/'motion-alpha';target.mkdir(exist_ok=True);cam=bpy.data.objects['Crossing motion camera'];S.frame_set(1001);S.camera=cam
# Render-time frame evaluation can restore animated visibility. Remove those channels
# before overriding, preserving the actor's real location, foot and wing animations.
for obj in bpy.data.objects:
 if obj in actor:
  if obj.animation_data and obj.animation_data.action:
   for fc in list(obj.animation_data.action.fcurves):
    if fc.data_path=='hide_render':obj.animation_data.action.fcurves.remove(fc)
 elif obj.animation_data:obj.animation_data_clear()
S.render.resolution_x=w;S.render.resolution_y=h;S.render.resolution_percentage=100;S.render.threads_mode='FIXED';S.render.threads=2;S.cycles.samples=a.samples;S.cycles.use_denoising=False;S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGBA';records=[]
background=root/'motion-background-clean-v002.png'
if a.background or not background.is_file():
 for ob in actor:ob.hide_render=True
 assert all(ob.hide_render for ob in actor)
 S.render.film_transparent=False;S.render.use_border=False;S.render.filepath=str(background);bpy.ops.render.render(write_still=True)
 (root/'background-proof.json').write_text(json.dumps({'file':background.name,'actor_meshes_visible':0,'actor_visibility_channels_removed':True,'camera':cam.name,'native_dimensions':[w,h],'sha256':hashlib.sha256(background.read_bytes()).hexdigest()},indent=2)+'\n')
for ob in actor:ob.hide_render=False
for ob in bpy.data.objects:
 if ob.type in ('MESH','CURVE','FONT','SURFACE','META'):
  ob.hide_render=ob not in actor and ob not in proxies and ob!=ground;ob.is_holdout=False;ob.is_shadow_catcher=ob==ground or ob in proxies
  if ob in proxies:ob.visible_shadow=False
S.render.film_transparent=True;S.render.use_border=True;S.render.use_crop_to_border=True
for i in (a.frames if a.frames is not None else range(84)):
 S.frame_set(1001+i);S.camera=cam;v=pio.location
 projected=[world_to_camera_view(S,cam,Vector((v.x+dx,v.y+dy,v.z+dz))) for dx in (-.6,.6) for dy in (-.55,.65) for dz in (-.13,1.1)]
 # Snap to exact binary camera fractions: avoids one-pixel float crop rounding.
 x0=max(0,math.floor((min(q.x for q in projected)*w-16)/5)*5);x1=min(w,math.ceil((max(q.x for q in projected)*w+16)/5)*5);y0=max(0,math.floor((min(q.y for q in projected)*h-16)/45)*45);y1=min(h,math.ceil((max(q.y for q in projected)*h+16)/45)*45)
 S.render.border_min_x=x0/w;S.render.border_max_x=x1/w;S.render.border_min_y=y0/h;S.render.border_max_y=y1/h
 output=target/f'frame-{i:04}.png';S.render.filepath=str(output);start=time.time();bpy.ops.render.render(write_still=True);record={'frame':i,'file':str(output.relative_to(root)),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'seconds':round(time.time()-start,3),'native_canvas':[w,h],'crop_bottom_left':[x0,y0,x1,y1],'real_rgba':True,'genuine_3d_geometry_animation':True,'background':background.name,'bridge_occlusion':'Actual Cycles proxy geometry; shadow catcher retains rail occlusion and actor contact shadows','blender_version':bpy.app.version_string,'samples':a.samples};records.append(record);(target/f'frame-{i:04}.json').write_text(json.dumps(record,indent=2)+'\n');print('PEPE_ALPHA',json.dumps(record),flush=True)
(root/'motion-alpha.json').write_text(json.dumps({'frames':84,'canvas':[w,h],'native_fps':12,'background':background.name,'actual_rendered_indices':sorted(int(p.stem.split('-')[1]) for p in target.glob('frame-*.png')),'source_master':'pepe-e01-motion-master-v001.blend'},indent=2)+'\n')
