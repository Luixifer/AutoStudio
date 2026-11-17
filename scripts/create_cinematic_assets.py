"""Original CPU Blender illustrations for AutoStudio. Not real footage.
Reproduce: blender -b -t 4 --python scripts/create_cinematic_assets.py -- /path/to/AutoStudio
"""
import bpy,math,random,sys,json,hashlib
from pathlib import Path
from mathutils import Vector,noise
R=Path(sys.argv[sys.argv.index('--')+1]);OUT=R/'assets/cinematic';OUT.mkdir(parents=True,exist_ok=True);random.seed(802)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=864;scene.render.resolution_y=1536;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=93;scene.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('Deep water, virtual exploration lighting');scene.world=world;world.use_nodes=True;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.006,.018,.032,1);bg.inputs['Strength'].default_value=.22
objects=[]
def material(name,color,rough=.6,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
def textured(name,c1,c2,scale,rough,bump=.15):
 m=material(name,c1,rough);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');t=n.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=scale;t.inputs['Detail'].default_value=4;r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(*c1,1);r.color_ramp.elements[1].color=(*c2,1);l.new(t.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color']);b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=bump;b.inputs['Distance'].default_value=.08;l.new(t.outputs['Fac'],b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs['Normal']);return m
basalt=textured('Mineral basalt',(.014,.018,.021),(.11,.14,.13),5,.88,.33);sand=textured('Deep sediment',(.016,.04,.045),(.12,.16,.15),3,.93,.18);mineral=textured('Pale mineral deposits',(.28,.23,.11),(.62,.52,.29),12,.82,.14);ivory=textured('Biological tube illustration',(.4,.47,.42),(.87,.82,.59),13,.55,.1);red=material('Tubeworm inspired red plume',(.46,.016,.025),.4);black=material('Vent opening',(.003,.005,.006),.98)
def mesh(name,verts,faces,mat):
 data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update();o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.data.materials.append(mat)
 for p in data.polygons:p.use_smooth=True
 objects.append(o);return o
def tube(name,points,radii,mat,sides=9):
 verts=[]
 for j,p in enumerate(points):
  p=Vector(p);direction=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(j-1,0)]);direction.normalize();ref=Vector((0,0,1)) if abs(direction.z)<.9 else Vector((0,1,0));u=direction.cross(ref).normalized();v=direction.cross(u).normalized();radius=radii[j] if isinstance(radii,list) else radii
  for k in range(sides):
   a=k*math.tau/sides;verts.append(tuple(p+(u*math.cos(a)+v*math.sin(a))*radius))
 faces=[(j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k) for j in range(len(points)-1) for k in range(sides)];faces+=[tuple(range(sides-1,-1,-1)),tuple(range((len(points)-1)*sides,len(points)*sides))];return mesh(name,verts,faces,mat)
# Sculpted relief instead of flat schematic mountains.
verts=[];side=65
for j in range(side):
 for i in range(side):
  x=-22+i*44/(side-1);y=-22+j*44/(side-1);z=.22*noise.noise(Vector((x*.35,y*.35,1)))+.10*math.sin(x*.8+y*.3);verts.append((x,y,z))
mesh('Ocean floor relief',verts,[(j*side+i,j*side+i+1,(j+1)*side+i+1,(j+1)*side+i) for j in range(side-1) for i in range(side-1)],sand)
# Individual weathered stones have nonuniform sculpted vertices and shared materials.
for i in range(95):
 x=random.uniform(-11,11);y=random.uniform(-7,15);bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(x,y,.05));o=bpy.context.object;o.name='Original basalt rock';o.scale=(random.uniform(.2,1.0),random.uniform(.2,.85),random.uniform(.12,.52));o.data.materials.append(basalt)
 for v in o.data.vertices:v.co*=random.uniform(.84,1.16)
 for p in o.data.polygons:p.use_smooth=True
 objects.append(o)
# Hydrothermal chimneys: no lava/flames. Warm materials are reflected exploration lights.
for x,y,h,rad in [(0,2,4.5,.55),(-2.3,4,3.2,.45),(2.6,5,2.5,.43),(1.7,8,4,.42),(-4,7,2.4,.4)]:
 rings=22;sides=28;verts=[]
 for j in range(rings):
  z=h*j/(rings-1);base=rad*(1.28-.48*j/(rings-1));cx=x+.14*math.sin(j*.15);cy=y+.09*math.cos(j*.3)
  for k in range(sides):
   a=k*math.tau/sides;r=base*(1+.15*math.sin(a*5+j*.9)+.05*math.sin(a*13-j*.3));verts.append((cx+r*math.cos(a),cy+r*math.sin(a),z+.025*math.sin(k*3)))
 faces=[(j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k) for j in range(rings-1) for k in range(sides)];mesh('Mineral chimney',verts,faces,basalt)
 for a in [0,1.4,3.1,4.7]:tube('Mineral vein',[(x+math.cos(a)*rad*1.2,y+math.sin(a)*rad*1.2,.1),(x+math.cos(a)*rad,y+math.sin(a)*rad,h*.55),(x+.1+math.cos(a)*rad*.8,y+math.sin(a)*rad*.8,h)],[.035,.04,.028],mineral,6)
 bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=8,location=(x+.14*math.sin(21*.15),y+.09*math.cos(21*.3),h),major_radius=rad*.69,minor_radius=.08);o=bpy.context.object;o.data.materials.append(mineral);objects.append(o)
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=rad*.6,depth=.03,location=(x+.14*math.sin(21*.15),y+.09*math.cos(21*.3),h-.06));o=bpy.context.object;o.data.materials.append(black);objects.append(o)
 # One irregular volume mesh per plume, with procedural density.
 points=[]
 for j in range(12):points.append((x+.15*math.sin(j*.8)+j*.055,y+.13*math.cos(j*.7),h+j*.38))
 m=bpy.data.materials.new('Suspended mineral plume');m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');vol=n.new('ShaderNodeVolumePrincipled');vol.inputs['Color'].default_value=(.15,.18,.19,1);vol.inputs['Density'].default_value=.35;tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=3;tex.inputs['Detail'].default_value=3;mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=.55;m.node_tree.links.new(tex.outputs['Fac'],mul.inputs[0]);m.node_tree.links.new(mul.outputs[0],vol.inputs['Density']);m.node_tree.links.new(vol.outputs['Volume'],out.inputs['Volume']);tube('Illustrative mineral plume',points,[.17+j*.065 for j in range(12)],m,14)
# Garden: species-inspired depiction, not a biological measurement or actual footage.
for i in range(32):
 x=2.4+random.uniform(-1.0,1);y=-.1+random.uniform(-1,1.3);h=random.uniform(.38,1.2);lean=random.uniform(-.13,.13);points=[(x,y,.08),(x+lean*.3,y,h*.45),(x+lean,y+.06,h)];tube('Tube worm inspired animal',points,[.07,.055,.045],ivory)
 for k in range(9):
  a=k*math.tau/9;end=(x+lean+math.cos(a)*.12,y+.06+math.sin(a)*.10,h+.25);tube('Red branchial plume',[(x+lean,y+.06,h),(end[0]*.4+(x+lean)*.6,end[1],h+.17),end],[.022,.018,.004],red,6)
# Water volume and virtual light; no sunlight at the seabed.
water=bpy.data.materials.new('Water scattering');water.use_nodes=True;nodes=water.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');v=nodes.new('ShaderNodeVolumePrincipled');v.inputs['Color'].default_value=(.12,.33,.43,1);v.inputs['Density'].default_value=.017;v.inputs['Anisotropy'].default_value=.2;water.node_tree.links.new(v.outputs['Volume'],out.inputs['Volume']);bpy.ops.mesh.primitive_cube_add(size=2,location=(0,0,10));volume=bpy.context.object;volume.name='Water column';volume.scale=(30,30,18);volume.data.materials.append(water)
def area(name,pos,power,color,size,target):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color;o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
lights=[area('Virtual exploration key',(-3,-4,8),2800,(.48,.79,1),5,(0,2,2)),area('Virtual warm exploration fill',(5,-2,4),1800,(1,.76,.43),4,(0,2,2)),area('Blue depth rim',(1,10,8),3500,(.18,.66,1),5,(0,3,3))]
data=bpy.data.cameras.new('Original documentary study camera');camera=bpy.data.objects.new('Original documentary study camera',data);scene.collection.objects.link(camera);scene.camera=camera;data.lens=40;data.dof.use_dof=True;data.dof.aperture_fstop=5.6
assets=[]
def render(name,position,target,lens=40,focus=8):
 camera.location=position;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();data.lens=lens;data.dof.focus_distance=(Vector(target)-camera.location).length;scene.render.filepath=str(OUT/(name+'.jpg'));bpy.ops.render.render(write_still=True);p=OUT/(name+'.jpg');assets.append({'id':name,'file':'assets/cinematic/'+p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'width':864,'height':1536,'origin':'Original Blender CPU render from scripts/create_cinematic_assets.py','type':'3D illustration, not actual footage','lighting':'Virtual exploration lighting, not sunlight at the seabed','license':'Project-original artwork; no third-party image assets'})
# Save the same useful wide-shot camera in the editable source.
camera.location=(9,-14,7);camera.rotation_euler=(Vector((0,3,2.2))-camera.location).to_track_quat('-Z','Y').to_euler();data.dof.focus_distance=(Vector((0,3,2.2))-camera.location).length
bpy.ops.wm.save_as_mainfile(filepath=str(R/'sources/ocean_environment_v02.blend'))
render('seabed_wide',(9,-14,7),(0,3,2.2),40)
render('vent_close',(2.2,-4.6,4.6),(0,2,3.7),55)
render('community',(4.8,-3.8,2.1),(2.5,.1,.65),60)
render('closing',(-10,-12,4.7),(0,4,2.4),42)
# Microscopic biological illustration in a separate scene: no fake microscope footage.
for o in objects:o.hide_render=True
volume.hide_render=True
for l in lights:l.hide_render=True
cell=material('Cell membrane',(.07,.42,.39),.28);p=cell.node_tree.nodes.get('Principled BSDF');p.inputs['Subsurface Weight'].default_value=.16;p.inputs['Subsurface Radius'].default_value=(.15,.4,.28)
core=material('Illustrative intracellular granules',(.76,.58,.22),.35)
for i in range(15):
 x=random.uniform(-2,2);y=random.uniform(-1.8,2.2);z=random.uniform(.2,1.4);bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=14,location=(x,y,z));o=bpy.context.object;o.name='Illustrative microbial cell';o.scale=(.27,.13,.14);o.rotation_euler[2]=random.random()*math.pi;o.data.materials.append(cell)
 for face in o.data.polygons:face.use_smooth=True
 for j in range(4):
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.025,location=(x+random.uniform(-.16,.16),y-.13,z+random.uniform(-.06,.06)));bpy.context.object.data.materials.append(core)
area('Microscopic illustration key',(-2,-2,5),550,(.60,.9,1),4,(0,0,0));area('Microscopic illustration rim',(1,3,3),800,(.2,1,.65),3,(0,0,0));render('microbes',(2,-3,2.3),(0,0,.8),60)
(OUT/'manifest.json').write_text(json.dumps({'schema':1,'generator':'scripts/create_cinematic_assets.py','source':'sources/ocean_environment_v02.blend','assets':assets,'real_underwater_footage':False},ensure_ascii=False,indent=2));print('ORIGINAL_3D_ASSETS_COMPLETE',len(assets))

# Free spatial denoising; preserve raw renders separately.
import subprocess
subprocess.run(['python3',str(R/'scripts/finish_assets.py')],check=True)
