"""Original scientific illustration masters. Blender 4.3.2, CPU only, no external media.
blender -b -t 4 --python scripts/create_science_art.py -- /path/to/AutoStudio [topic]
"""
import bpy,math,random,sys,json,hashlib
from pathlib import Path
from mathutils import Vector,noise
ROOT=Path(sys.argv[sys.argv.index('--')+1]);selected=sys.argv[sys.argv.index('--')+2:];TOPICS=selected or ['auroras','dna','volcanoes']
M={};SCENE=None

def mat(name,color,rough=.45,metal=0,emit=0,alpha=1):
 key=(name,tuple(color),rough,metal,emit,alpha)
 if key in M:return M[key]
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emit:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emit
 if alpha<1:
  out=n.get('Material Output');mix=n.new('ShaderNodeMixShader');tr=n.new('ShaderNodeBsdfTransparent');mix.inputs[0].default_value=alpha;l.new(tr.outputs[0],mix.inputs[1]);l.new(p.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0])
 M[key]=m;return m

def rocky(name,a,b):
 m=mat(name,a,.84);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=5;tex.inputs['Detail'].default_value=3;r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(*a,1);r.color_ramp.elements[1].color=(*b,1);l.new(tex.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color']);bum=n.new('ShaderNodeBump');bum.inputs['Strength'].default_value=.24;bum.inputs['Distance'].default_value=.09;l.new(tex.outputs['Fac'],bum.inputs[0]);l.new(bum.outputs[0],p.inputs['Normal']);return m

def sphere(name,loc,scale,material,ico=False):
 if ico:bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=loc)
 else:bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=loc)
 o=bpy.context.object;o.name=name;o.scale=scale if isinstance(scale,tuple) else (scale,)*3;o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o

def line(name,points,radius,material):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=2;d.bevel_depth=radius;d.bevel_resolution=2;s=d.splines.new('POLY');s.points.add(len(points)-1)
 for p,co in zip(s.points,points):p.co=(*co,1)
 o=bpy.data.objects.new(name,d);SCENE.collection.objects.link(o);o.data.materials.append(material);return o

def mesh(name,v,f,material):
 d=bpy.data.meshes.new(name);d.from_pydata(v,[],f);d.update();o=bpy.data.objects.new(name,d);SCENE.collection.objects.link(o);o.data.materials.append(material)
 for p in d.polygons:p.use_smooth=True
 return o

def area(name,loc,energy,color,size,target=(0,0,1)):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);SCENE.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

def setup(name,bg=(.004,.009,.024)):
 global SCENE
 s=bpy.data.scenes.new(name);bpy.context.window.scene=s;SCENE=s;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.045;s.cycles.max_bounces=4;s.cycles.transparent_max_bounces=8;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=864;s.render.resolution_y=1536;s.render.resolution_percentage=100;s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=95;s.view_settings.view_transform='AgX'
 w=bpy.data.worlds.new(name+' world');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(*bg,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.30;s.world=w
 d=bpy.data.cameras.new(name+' camera');cam=bpy.data.objects.new(name+' camera',d);s.collection.objects.link(cam);s.camera=cam;d.lens=40;d.clip_end=250
 area('Cool key',(-5,-5,9),1500,(.68,.82,1),5);area('Warm fill',(5,-2,5),900,(1,.73,.49),4);area('Rim',(1,5,6),1700,(.3,.7,1),4)
 s.use_nodes=True;n=s.node_tree.nodes;g=n.new('CompositorNodeGlare');g.glare_type='FOG_GLOW';g.quality='LOW';g.threshold=2;g.size=7;s.node_tree.links.new(n['Render Layers'].outputs['Image'],g.inputs['Image']);s.node_tree.links.new(g.outputs['Image'],n['Composite'].inputs['Image']);return s

def aim(loc,target,lens=40):
 c=SCENE.camera;c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=lens

def stars(seed=1):
 r=random.Random(seed);m=mat('Starlight',(.63,.78,1),emit=4)
 for i in range(120):sphere('Original star',(r.uniform(-22,22),r.uniform(16,22),r.uniform(-1,22)),r.uniform(.018,.05),m,True)

def terrain(material,size=24):
 side=29;verts=[]
 for j in range(side):
  for i in range(side):
   x=-size/2+i*size/(side-1);y=-size/2+j*size/(side-1);z=.18*noise.noise(Vector((x*.6,y*.5,1)));verts.append((x,y,z))
 return mesh('Original relief',verts,[(j*side+i,j*side+i+1,(j+1)*side+i+1,(j+1)*side+i) for j in range(side-1) for i in range(side-1)],material)

def curtain(xoffset=0,depth=7,color=(.03,.7,.37),phase=0):
 points=100;verts=[]
 for i in range(points):
  u=i/(points-1);x=(u-.5)*16+xoffset;y=depth+.6*math.sin(u*15+phase);base=5+.8*math.sin(u*9+phase)
  verts.extend([(x,y,base),(x,y,base+5+math.sin(u*13))])
 faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(points-1)]
 m=bpy.data.materials.new('Aurora light curtain');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');em.inputs['Color'].default_value=(*color,1);em.inputs['Strength'].default_value=3;tr=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=5;tex.inputs['Detail'].default_value=2;coord=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(coord.outputs['Generated'],sep.inputs[0]);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.02;r.color_ramp.elements[0].color=(0,0,0,1);r.color_ramp.elements[1].position=.5;r.color_ramp.elements[1].color=(.75,.75,.75,1);top=r.color_ramp.elements.new(.98);top.color=(.06,.06,.06,1);l.new(sep.outputs['Z'],r.inputs[0]);mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(r.outputs[0],mult.inputs[0]);l.new(tex.outputs['Fac'],mult.inputs[1]);l.new(mult.outputs[0],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0]);return mesh('Auroral curtain illustration',verts,faces,m)

def earth(radius=2.1):
 m=mat('Illustrative planet, not measured cartography',(.025,.15,.39),.40);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=3.5;tex.inputs['Detail'].default_value=3;r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.45;r.color_ramp.elements[0].color=(.012,.055,.18,1);r.color_ramp.elements[1].position=.54;r.color_ramp.elements[1].color=(.10,.35,.20,1);l.new(tex.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color']);sphere('Stylized Earth',(0,0,2.7),radius,m)
 rim=mat('Atmosphere glow',(.03,.30,.8),emit=.6,alpha=.06);sphere('Atmospheric shell',(0,0,2.7),radius*1.04,rim)

def aurora(index):
 setup('auroras_'+str(index));stars(index)
 if index in [1,6,8]:
  snow=rocky('Night snow',(.035,.07,.10),(.24,.34,.40));terrain(snow,35)
  for j in range(7):
   x=-11+j*3.6;sphere('Distant mountain',(x,13,1),(3,3,3.5+math.sin(j)*1.6),snow,True)
  for j in range(7):
   x=-8+j*2.5;y=4+math.sin(j)*1.3;trunk=mat('Forest silhouette',(.007,.02,.025));line('Trunk',[(x,y,.1),(x,y,2)],.06,trunk)
   for k in range(3):bpy.ops.mesh.primitive_cone_add(vertices=9,radius1=.7-k*.15,radius2=0,depth=1.5,location=(x,y,1.0+k*.45));bpy.context.object.data.materials.append(trunk)
  curtain(0,8,(.025,.8,.42),index*.3)
  if index in [6,8]:curtain(1,9,(.65,.04,.30),index*.5)
  aim((0,-15,3.4),(0,8,5.0),31 if index==8 else 35)
 elif index in [2,3,7]:
  earth()
  if index==2:
   sun=mat('Solar light',(1,.30,.025),emit=4);sphere('Sun',(-6,1,3),1.5,sun)
   for j in range(15):
    z=1+j*.24;line('Solar wind trajectory',[(-5+.45*i,0,z+.1*math.sin(i*.6+j)) for i in range(11)],.014,mat('Solar wind',(.95,.55,.11),emit=2))
   aim((6,-16,9),(-1.6,0,2.7),42)
  else:
   for j in range(8):
    a=j*math.tau/8;pts=[]
    for k in range(65):
     t=.13+(math.pi-.26)*k/64;rad=(3.5 if index==3 else 2.8)*math.sin(t)**2;pts.append((rad*math.sin(t)*math.cos(a),rad*math.sin(t)*math.sin(a),2.7+rad*math.cos(t)))
    line('Illustrative magnetic field',pts,.018,mat('Field path',(.1,.55,.87),emit=2))
   if index==7:
    for z in [4.52,.9]:line('Auroral oval',[(.2+.82*math.cos(a*math.tau/80),.1+.63*math.sin(a*math.tau/80),z) for a in range(81)],.07,mat('Auroral oval green',(.1,.9,.28),emit=4))
   aim((4,-13,10 if index==7 else 6),(0,0,2.7),45)
 else:
  palette=[(.08,.65,.32),(.18,.25,.9)]
  for j in range(3):
   x=(j-1)*1.8;z=1.6+math.sin(j)*.4;sphere('Excited atmospheric atom, schematic',(x,0,z),.6,mat('Atmospheric species '+str(j),palette[j%2],emit=.4 if index==4 else 1.8))
   for k in range(6):
    a=k*math.tau/6;line('Light packet illustration',[(x+.7*math.cos(a),0,z+.7*math.sin(a)),(x+1.15*math.cos(a),0,z+1.15*math.sin(a))],.022,mat('Emission packet',(.4,1,.72),emit=3))
  if index==4:line('Incoming charged particle',[(-4,-.3,3),(-2.7,-.2,2.2),(-1.8,0,1.6)],.04,mat('Particle path',(1,.55,.12),emit=3))
  aim((3,-12,6),(0,0,1.8),46)

PALETTE=[(.9,.16,.23),(.08,.65,.66),(.95,.62,.08),(.35,.18,.8)]
def helix(origin=(0,0,0),height=6,radius=1,phase=0,scale=1,active=False):
 ox,oy,oz=origin;back=mat('Sugar phosphate illustration',(.07,.47,.70),.26,metal=.18)
 for side in [0,math.pi]:line('DNA backbone',[(ox+radius*math.cos(i*math.tau*2.0/120+phase+side),oy+radius*math.sin(i*math.tau*2.0/120+phase+side),oz+height*i/120) for i in range(121)],.085*scale,back)
 for i in range(23):
  a=i*math.tau*2/22+phase;z=oz+height*i/22;left=(ox+radius*math.cos(a),oy+radius*math.sin(a),z);right=(ox-radius*math.cos(a),oy-radius*math.sin(a),z);mid=(ox,oy,z);c=i%4
  for start,end,ind in [(left,mid,c),(mid,right,(c+2)%4)]:
   material=mat('Illustrative base '+str(ind),PALETTE[ind],.3,emit=.8 if active and 7<i<13 else 0);line('Paired base, not actual genomic sequence',[start,end],.065*scale,material)
  sphere('Backbone node',left,.12*scale,back);sphere('Backbone node',right,.12*scale,back)

def cell(loc,scale=1):
 sphere('Cell membrane illustration',loc,2.7*scale,mat('Cell membrane',(.06,.38,.48),alpha=.10));sphere('Nuclear envelope',(loc[0],loc[1],loc[2]+.1),1.65*scale,mat('Nuclear envelope',(.35,.08,.4),alpha=.13))

def dna(index):
 setup('dna_'+str(index),(.006,.012,.035));area('Biology magenta rim',(4,2,5),1400,(.8,.2,.7),4)
 if index==1:
  cell((0,0,2.8));helix((0,0,1),height=3.5,radius=.62,scale=.65)
  for j in range(18):a=j*math.tau/18;sphere('Cytoplasmic body',(2.1*math.cos(a),1.4*math.sin(a),2.8+.5*math.sin(j*3)),(.20,.12,.28),mat('Cytoplasmic body',(.12,.45,.6),.4))
  aim((6,-13,7),(0,0,2.8),46)
 elif index in [2,6,8]:
  helix((0,0,0),height=6.8,radius=1.05,phase=index*.3,active=index==6)
  if index==8:
   for j in range(7):sphere('Distant cellular context',(math.sin(j)*4,4,1+j*.8),.35,mat('Context cells',(.12,.2,.4),alpha=.35))
  aim((4 if index==6 else 2,-12,6),(0,0,3.3),43)
 elif index==3:
  helix((0,0,0),height=2.6,radius=.72,scale=.7)
  helix((-1.15,0,2.8),height=3.2,radius=.62,phase=.8,scale=.65);helix((1.15,0,2.8),height=3.2,radius=.62,phase=-.8,scale=.65)
  for x in [-1.15,1.15]:line('Replication fork branch',[(0,0,2.5),(x*.45,0,2.75),(x,0,2.8)],.11,mat('Copying connector',(.13,.6,.64)))
  aim((4,-13,6),(0,0,3.1),45)
 elif index==4:
  helix((-1,0,0),height=6,radius=.8,scale=.8)
  points=[(1.1+.35*math.sin(i*.4),-.5,1+i*.2) for i in range(23)];line('Temporary RNA message illustration',points,.09,mat('RNA strand',(1,.47,.12),emit=.2))
  for p in points:sphere('RNA base',p,.14,mat('RNA bead',(1,.64,.2)))
  aim((4,-12,5),(.2,0,3),43)
 elif index==5:
  for loc,scale in [((0,0,2.8),(1.6,1.3,.85)),((0,.1,3.8),(1.9,1.5,.85))]:
   o=sphere('Ribosomal subunit illustration',loc,scale,mat('Ribosome',(.23,.15,.48),.48))
   for v in o.data.vertices:v.co*=1+.10*noise.noise(v.co*6)
  line('RNA entering ribosome',[(-4,-.7,3.15),(-2,-.7,3.15),(0,-.7,3.15),(3,-.7,3.15)],.07,mat('RNA',(1,.6,.12)))
  points=[(.3+math.sin(i*.8)*.7,-.5-math.cos(i*.7)*.3,2.9-i*.22) for i in range(15)]
  line('Emerging polypeptide',points,.08,mat('Protein backbone',(.15,.65,.5)))
  for i,p in enumerate(points):sphere('Amino acid illustration',p,.19,mat('Protein group '+str(i%4),PALETTE[i%4],.3))
  aim((6,-13,7),(0,0,2.6),44)
 else:
  for x in [-1.55,1.55]:cell((x,0,3),.62);helix((x,0,1.7),height=2.6,radius=.42,phase=x,scale=.5,active=x>0)
  for i in range(15):p=(math.sin(i*2.3)*3,-.7,1+(i%7)*.6);sphere('Extracellular signal illustration',p,.11,mat('Chemical signal',(.95,.64,.16),emit=.3))
  aim((5,-14,7),(0,0,3),44)

ROCK=None;LAVA=None

def cone(loc=(0,0,0),scale=1):
 x,y,z=loc;verts=[];sides=64;rings=25
 for j in range(rings):
  r=.65+(6-.65)*j/(rings-1)
  for k in range(sides):
   a=k*math.tau/sides;h=3.8*(1-(r-.65)/(6-.65))**1.65+.13*math.sin(a*8+j*.7)*(1-j/rings);verts.append((x+r*math.cos(a)*scale,y+r*math.sin(a)*scale,z+h*scale))
 mesh('Original eroded volcanic cone',verts,[(j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k) for j in range(rings-1) for k in range(sides)],ROCK)
 sphere('Crater lava surface',(x,y,z+3.68*scale),(.58*scale,.58*scale,.07*scale),LAVA)
 return loc

def cutaway():
 for j in range(6):
  points=[(-2.8+i*.2,1.2,1+j*.48+.10*math.sin(i*.4+j)) for i in range(29)]
  for i,p in enumerate(points):sphere('Solid mantle schematic rock',p,(.22,.55,.28),ROCK,True)

def volcanoes(index):
 global ROCK,LAVA
 setup('volcanoes_'+str(index),(.025,.035,.06));ROCK=rocky('Original basalt '+str(index),(.05,.035,.031),(.23,.17,.13));LAVA=mat('Molten rock illumination',(1,.08,.008),.30,emit=2.5);area('Geology warm key',(-6,-4,9),2700,(1,.68,.38),6)
 if index in [1,5,6,8]:
  terrain(ROCK,32);cone()
  for j in range(8):sphere('Distant volcanic terrain',(-12+j*3.5,13,0),(3,3,1.8+math.sin(j)),ROCK,True)
  if index in [5]:
   for j in range(32):
    r=random.Random(j+170);h=j*.15;sphere('Ash plume illustration',(math.sin(j*.7)*(.2+h*.08),math.cos(j)*.2,3.7+h),(.2+h*.10,.22+h*.08,.23+h*.08),mat('Ash '+str(j),(.11+j*.001,.10+j*.001,.10+j*.001),.85),True)
   for j in range(16):a=j*math.tau/16;line('Ejected glowing fragment',[ (.2*math.cos(a),.2*math.sin(a),4),(.8*math.cos(a),.8*math.sin(a),5.6),(1.9*math.cos(a),1.9*math.sin(a),4.5)],.025,LAVA)
  if index in [6,8]:
   pts=[]
   for i in range(38):
    r=.6+i*.14;x=.2*math.sin(i*.3);y=-r;h=3.8*max(0,1-(r-.65)/(6-.65))**1.65+.06;pts.append((x,y,h))
   line('Lava flow dark crust',pts,.28,mat('Cooling crust',(.15,.012,.005),.65));line('Incandescent lava channel',pts,.16,LAVA)
  aim((10,-17,8 if index!=6 else 6),(0,0,2.8),36 if index in [1,8] else 45)
 elif index in [2,3,4]:
  cutaway()
  if index==2:
   for j in range(3):line('Very slow deformation indicator',[(-2+i*.4,.5,1.7+j*.8+.12*math.sin(i*.5)) for i in range(12)],.022,mat('Deformation path',(.3,.55,.7),emit=.6))
  else:
   for j in range(13):x=.35*math.sin(j*1.3);z=1+j*.2;sphere('Localized melt pocket',(x,.4,z),(.15,.24,.20),LAVA)
   if index==4:
    line('Magma ascent schematic',[(math.sin(i*.35)*.35,.1,.9+i*.13) for i in range(28)],.22,mat('Magma ascent',(1,.20,.015),emit=.9))
    for j in range(6):sphere('Gas bubble schematic',(math.sin(j)*.3,-.2,1.2+j*.45),.08+j*.019,mat('Gas bubble',(1,.7,.16),emit=.3))
  aim((5,-12,6),(0,.7,2.5),48)
 else:
  terrain(ROCK,24);cone((-3,0,0),.48);cone((3,0,0),.48)
  line('More mobile flow illustration',[(-3+.15*math.sin(j*.8),-j*.18,1.75*max(0,1-j/18)**1.5+.1) for j in range(19)],.14,LAVA)
  line('More viscous flow illustration',[(3+.09*math.sin(j*.7),-j*.12,1.75*max(0,1-j/13)**1.5+.1) for j in range(12)],.27,LAVA)
  aim((7,-16,8),(0,0,1.8),40)

for topic in TOPICS:
 random.seed(404);M.clear();bpy.ops.wm.read_factory_settings(use_empty=True);assets=[];out=ROOT/'assets/science_v04'/topic;out.mkdir(parents=True,exist_ok=True)
 for index in range(1,9):
  {'auroras':aurora,'dna':dna,'volcanoes':volcanoes}[topic](index)
  file=out/f'{topic}_{index:02}.jpg';SCENE.render.filepath=str(file);bpy.ops.render.render(write_still=True)
  assets.append({'id':f'{topic}_{index:02}','file':str(file.relative_to(ROOT)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'width':864,'height':1536,'topic_id':topic,'type':'Original 3D scientific illustration, not actual footage','origin':'scripts/create_science_art.py, Blender 4.3.2 CPU','source':f'sources/science_v04/{topic}_master_v001.blend','license':'LicenseRef-AutoStudio-Original','license_file':'assets/science_v04/LICENSE_ART.md','credit':'Ilustración original AutoStudio','scale_disclosure':'Qualitative illustration, not to scale; no measured simulation or biological data'})
  print('SCIENCE_ASSET_RENDERED',topic,index,flush=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'sources/science_v04/{topic}_master_v001.blend'),compress=True)
 (out/'manifest.json').write_text(json.dumps({'schema':1,'topic_id':topic,'assets':assets,'generator':'scripts/create_science_art.py','real_footage':False},ensure_ascii=False,indent=2)+'\n')
 print('SCIENCE_TOPIC_COMPLETE',topic,flush=True)
