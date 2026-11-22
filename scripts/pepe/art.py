"""Original editable 3D storybook master. Blender 4.3.2, CPU Cycles.
No downloaded models, pictures, fonts, music or reference-sheet crops.
blender -b -t 4 --python scripts/pepe/art.py -- --out reports/pepe81/input --shots 1 2 11 18
"""
import bpy,math,random,json,sys,argparse,time,hashlib
from pathlib import Path
from mathutils import Vector
A=argparse.ArgumentParser();A.add_argument('--out',type=Path,required=True);A.add_argument('--shots',type=int,nargs='*');A.add_argument('--preview',action='store_true');A.add_argument('--samples',type=int,default=32);A.add_argument('--render-threads',type=int,default=4);A.add_argument('--motion-crop',action='store_true');A.add_argument('--motion-start',type=int);A.add_argument('--motion-end',type=int);A.add_argument('--motion-total',type=int,default=84);args=A.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=args.out.resolve();OUT.mkdir(parents=True,exist_ok=True);(OUT/'media').mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);S=bpy.context.scene;S.name='Pepe · El gran rescate de Pío';R=random.Random(81);M={};ACT={};GROUPS={}

def mat(name,color,rough=.45,sub=.0,metal=0,noise=False):
 if name in M:return M[name]
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Subsurface Weight'].default_value=sub
 if noise:
  ns=m.node_tree.nodes;links=m.node_tree.links;t=ns.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=22;t.inputs['Detail'].default_value=2
  bump=ns.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.025;links.new(t.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],p.inputs['Normal'])
 M[name]=m;return m
orange=mat('Pepe · warm tangerine',(.91,.255,.037),.36,.08,noise=True);gold=mat('Golden beaks and toes',(.98,.54,.055),.30,.05);cream=mat('Warm cream feather',(.99,.75,.34),.44,.05);red=mat('Pepe · cherry red crest',(.78,.028,.045),.32,.12);teal=mat('Pepe · turquoise tail',(.018,.45,.57),.30,.05);blue=mat('Tail · deep blue',(.025,.18,.42),.31);white=mat('Eye whites',(.99,.985,.91),.2);black=mat('Pupils',(.009,.015,.024),.16);brown=mat('Warm facial outline',(.20,.071,.035),.5);iris=mat('Eyes · honey brown',(.22,.10,.025),.22);blush=mat('Soft cheek',(.98,.35,.21),.6,.1);yellow=mat('Pío · butter yellow',(.99,.72,.09),.42,.11,noise=True);yellowLight=mat('Pío · sunlit down',(.99,.86,.30),.42,.1);wool=mat('Lola · vanilla wool',(.94,.91,.80),.83,.08,noise=True);face=mat('Lola · warm cream face',(.77,.67,.49),.61,.09);gray=mat('Nube · pale silver fur',(.64,.71,.74),.72,.1,noise=True);pink=mat('Nube · rose inner ear',(.98,.43,.50),.54,.15);wood=mat('Honey timber',(.43,.19,.065),.58,noise=True);woodLight=mat('Sunlit timber',(.70,.39,.13),.53,noise=True);ropeMat=mat('Natural rope',(.67,.48,.23),.8,noise=True);barnRed=mat('Red painted barn',(.69,.075,.075),.56,noise=True);trim=mat('Cream barn trim',(.98,.84,.55),.48);roofMat=mat('Roof slate · blueberry',(.115,.22,.32),.50);grass=mat('Meadow green',(.23,.48,.095),.9);grass2=mat('Blade bright',(.38,.62,.12),.85);stone=mat('Smooth river stone',(.49,.58,.50),.8,noise=True);leafMat=mat('Apple green canopy',(.31,.55,.09),.8);leafDark=mat('Forest jade',(.13,.37,.12),.8);skyMat=mat('Distant mint hills',(.35,.64,.33),.9);flowerPink=mat('Cosmos pink',(.95,.20,.38),.48,.1);flowerBlue=mat('Blue flowers',(.21,.45,.92),.48);flowerWhite=mat('Daisy cream',(.98,.94,.76),.6);water=mat('Shallow turquoise stream',(.075,.45,.48),.20);water.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.45;waterLight=mat('Gentle water glints',(.47,.86,.84),.3)

def parent(o,p):
 if p:o.parent=p
 return o

def egg(name,loc,scale,m,p=None,segments=24):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=16,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 return parent(o,p)

def cube(name,loc,scale,m,p=None,bevel=.06):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:
  mod=o.modifiers.new('Soft crafted edges','BEVEL');mod.width=bevel;mod.segments=3;mod=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return parent(o,p)

def curve(name,points,radius,m,p=None):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=10;d.bevel_depth=radius;d.bevel_resolution=3;s=d.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
 for b,co in zip(s.bezier_points,points):b.co=co;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,d);S.collection.objects.link(o);o.data.materials.append(m);return parent(o,p)

def leaf(name,points,width,depth,m,p=None):
 # Closed curved feather, tapered at both ends; not a flat texture or icon.
 points=[Vector(v) for v in points];verts=[];rings=11;sides=10
 for j in range(rings):
  t=j/(rings-1);a=t*(len(points)-1);k=min(len(points)-2,int(a));center=points[k].lerp(points[k+1],a-k);w=max(.006,math.sin(math.pi*t)**.7)
  for q in range(sides):
   ang=q*2*math.pi/sides;verts.append(tuple(center+Vector((math.cos(ang)*width*w,math.sin(ang)*depth*w,0))))
 faces=[(j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k) for j in range(rings-1) for k in range(sides)];faces += [tuple(range(sides-1,-1,-1)),tuple((rings-1)*sides+k for k in range(sides))]
 d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(name,d);S.collection.objects.link(o);o.data.materials.append(m)
 for f in d.polygons:f.use_smooth=True
 mod=o.modifiers.new('Polished feather volume','SUBSURF');mod.levels=1;mod.render_levels=1
 return parent(o,p)

def rig(name):
 o=bpy.data.objects.new(name,None);S.collection.objects.link(o);o.empty_display_type='PLAIN_AXES';ACT[name]=o;return o

def pivot(name,loc,p):
 o=bpy.data.objects.new(name,None);S.collection.objects.link(o);o.location=loc;o.parent=p;return o

def eyes(p,z,x,y,r,look=0):
 for side in (-1,1):
  egg(p.name+' · eye white',(side*x,y,z),(r,r*.74,r*1.08),white,p)
  egg(p.name+' · amber iris',(side*x+look,y-r*.68,z),(r*.68,r*.16,r*.76),iris,p)
  egg(p.name+' · pupil',(side*x+look,y-r*.82,z),(r*.48,r*.12,r*.56),black,p)
  egg(p.name+' · catchlight',(side*x-r*.15+look,y-r*.94,z+r*.26),(r*.20,r*.08,r*.20),white,p,16)
  egg(p.name+' · little glint',(side*x+r*.18+look,y-r*.93,z-r*.15),(r*.075,r*.05,r*.075),white,p,12)
  curve(p.name+' · expressive eyebrow',[(side*x-r*.75,y,z+r*1.10),(side*x,y-.025,z+r*1.30),(side*x+r*.70,y,z+r*1.12)],r*.09,brown,p)

def bird(name,small=False):
 p=rig(name)
 if not small:
  egg('Pepe · sculpted pear torso',(0,0,.86),(.50,.38,.62),orange,p);egg('Pepe · chest bib',(0,-.28,.76),(.34,.15,.39),cream,p)
  egg('Pepe · cheeky head',(0,-.035,1.43),(.45,.36,.43),orange,p);eyes(p,1.48,.205,-.31,.197)
  for i in range(3):leaf('Pepe · crimson crest lobe '+str(i),[(0,-.27+i*.22,1.72),(.015,-.31+i*.22,2.12-i*.055),(.01,-.13+i*.22,2.14-i*.07)],.145,.12,red,p)
  for i in range(5):
   x=(i-2)*.13;leaf('Pepe · curled turquoise tail '+str(i),[(x,.22,.68),(x*1.5,.68,.96),(x*1.8,.94,1.55),(x*1.8,.62,1.82-abs(i-2)*.10)],.12,.105,teal if i%2 else blue,p)
  wingz=.99
  for side in (-1,1):
   w=pivot('Pepe · wing pivot '+str(side),(side*.44,0,wingz),p);ACT['pepe_wing_'+str(side)]=w
   egg('Pepe · wing shoulder',(0,-.015,-.08),(.16,.24,.27),orange,w)
   for i in range(4):leaf('Pepe · layered wing feather',[(side*.02,-.18+i*.10,-.03),(side*.09,-.20+i*.11,-.23),(side*.13,-.12+i*.11,-.43+i*.04)],.095,.065,cream if i==0 else orange,w)
  upper=egg('Pepe · upper beak',(0,-.49,1.32),(.19,.22,.12),gold,p);ACT['pepe_beak']=upper;egg('Pepe · lower beak',(0,-.46,1.23),(.145,.16,.075),gold,p)
  curve('Pepe · gentle smile',[(-.11,-.59,1.255),(0,-.64,1.24),(.11,-.59,1.255)],.013,brown,p)
  egg('Pepe · red wattle left',(-.065,-.35,1.12),(.075,.07,.13),red,p);egg('Pepe · red wattle right',(.065,-.35,1.12),(.075,.07,.13),red,p)
  for side in (-1,1):
   leg=pivot('Pepe · leg pivot '+str(side),(side*.19,0,.25),p);ACT['pepe_leg_'+str(side)]=leg
   curve('Pepe · shank',[(0,0,0),(0,-.02,-.20)],.048,gold,leg)
   for toe in (-1,0,1):curve('Pepe · rounded toe',[(0,-.02,-.20),(toe*.09,-.18,-.24),(toe*.13,-.29,-.23)],.035,gold,leg)
 else:
  egg('Pío · soft yellow body',(0,0,.40),(.33,.27,.35),yellow,p);egg('Pío · round head',(0,-.035,.66),(.31,.25,.31),yellowLight,p);eyes(p,.70,.139,-.23,.127)
  egg('Pío · tiny beak',(0,-.35,.57),(.105,.12,.065),gold,p)
  for side in (-1,1):
   egg('Pío · blush',(side*.22,-.245,.55),(.055,.022,.033),blush,p)
   egg('Pío · fluffy wing',(side*.31,-.005,.40),(.115,.13,.18),yellowLight,p)
   for toe in (-1,0,1):curve('Pío · little toe',[(side*.13,0,.13),(side*.13+toe*.045,-.17,.025)],.021,gold,p)
  for i in (-1,0,1):leaf('Pío · down tuft',[(i*.04,.02,.86),(i*.06,-.02,1.025-abs(i)*.05),(i*.08,-.09,1.0-abs(i)*.05)],.035,.03,yellow,p)
 return p

pepe=bird('Pepe');pio=bird('Pío',True)
lola=rig('Lola');egg('Lola · soft torso',(0,0,.65),(.55,.38,.42),wool,lola)
for i in range(30):
 phi=R.uniform(0,2*math.pi);zz=R.uniform(-.8,.9);rr=math.sqrt(1-zz*zz);egg('Lola · wool curl',(rr*math.cos(phi)*.48,rr*math.sin(phi)*.33,.68+zz*.31),(.14,.13,.14),wool,lola,16)
egg('Lola · face',(0,-.34,.82),(.24,.23,.30),face,lola);eyes(lola,.88,.128,-.52,.114)
for side in (-1,1):
 egg('Lola · floppy ear',(side*.29,-.30,.94),(.19,.08,.085),face,lola);egg('Lola · inner ear',(side*.30,-.36,.95),(.13,.025,.045),pink,lola)
 for y in (-.20,.19):
  egg('Lola · leg',(side*.30,y,.26),(.075,.08,.23),face,lola);egg('Lola · small hoof',(side*.30,y,.105),(.09,.10,.07),brown,lola)
egg('Lola · nose',(0,-.57,.70),(.075,.045,.04),brown,lola);curve('Lola · smile',[(-.08,-.555,.64),(0,-.58,.615),(.08,-.555,.64)],.012,brown,lola)
nube=rig('Nube');egg('Nube · body',(0,0,.39),(.30,.24,.33),gray,nube);egg('Nube · head',(0,-.04,.72),(.29,.25,.28),gray,nube);eyes(nube,.75,.133,-.23,.121)
for side in (-1,1):
 ear=pivot('Nube · ear '+str(side),(side*.15,0,.89),nube);ear.rotation_euler.y=side*.18;egg('Nube · outer ear',(0,0,.27),(.105,.08,.33),gray,ear);egg('Nube · pink ear',(0,-.067,.28),(.063,.025,.245),pink,ear)
 egg('Nube · foot',(side*.20,-.10,.13),(.135,.18,.10),gray,nube);egg('Nube · paw',(side*.27,-.09,.44),(.085,.09,.16),gray,nube)
 egg('Nube · cream muzzle',(side*.06,-.28,.61),(.08,.06,.06),wool,nube)
egg('Nube · rose nose',(0,-.343,.65),(.043,.028,.032),pink,nube);egg('Nube · tail',(0,.24,.35),(.14,.14,.15),wool,nube);nube.scale=(.8,)*3
butterfly=rig('Mariposa');bodyMat=mat('Butterfly royal body',(.055,.09,.22),.5);wingMat=mat('Butterfly sky blue',(.05,.48,.96),.30,.08)
egg('Mariposa · body',(0,0,0),(.035,.035,.14),bodyMat,butterfly)
for side in (-1,1):
 wing=egg('Mariposa · blue heart wing',(side*.13,0,.035),(.17,.027,.18),wingMat,butterfly);wing.rotation_euler.y=side*.25
 egg('Mariposa · lower wing',(side*.095,0,-.11),(.11,.025,.11),teal,butterfly)
 for j in range(3):egg('Mariposa · golden spot',(side*(.09+j*.035),-.026,.06+j*.025),(.017,.009,.024),cream,butterfly,12)
 curve('Mariposa · antenna',[(0,0,.13),(side*.06,0,.21),(side*.075,0,.20)],.008,bodyMat,butterfly)

# Shared environment: one continuous map; the dry home bank is x < -1.
bpy.ops.mesh.primitive_grid_add(x_subdivisions=60,y_subdivisions=60,size=55);ground=bpy.context.object;ground.name='Single meadow terrain'
for v in ground.data.vertices:
 x,y=v.co.x,v.co.y;v.co.z=-.16 if abs(x)<.95 else -.03+.09*math.sin(x*.32)*math.sin(y*.30)
ground.data.materials.append(grass)
# A shallow stream, gently curved surface; banks always remain separated in world X.
verts=[];n=64
for i in range(n):
 y=-10+i*24/(n-1);bend=.15*math.sin(y*.65)
 for x in (-.88,.88):verts.append((x+bend,y,.015))
d=bpy.data.meshes.new('Stream mesh');d.from_pydata(verts,[],[(2*i,2*i+1,2*i+3,2*i+2) for i in range(n-1)]);o=bpy.data.objects.new('Shallow quiet stream',d);S.collection.objects.link(o);o.data.materials.append(water)
for side in (-1,1):
 for i in range(18):
  y=-7+i*.8;egg('Rounded bank stone',(side*(1.03+R.uniform(-.1,.14)),y,.06),(R.uniform(.18,.35),R.uniform(.22,.4),R.uniform(.09,.17)),stone,None,16)
for i in range(20):
 y=-6+i*.65;x=R.uniform(-.55,.55);curve('Quiet water ripple',[(x-.12,y,.025),(x,y+.035,.025),(x+.13,y,.025)],.008,waterLight)
for x,y,sc in [(-10,14,8),(-1,16,9),(11,15,8),(-18,7,8),(18,8,8)]:egg('Soft distant hill',(x,y,-1),(sc,sc*.6,sc*.48),skyMat,None,24)

# Original red timber barn, framed double doors, deep roof eaves, windows.
for x in range(14):cube('Barn · vertical painted board',(-9.6+x*.27,5,1.33),(.255,2.7,2.65),barnRed,bevel=.035)
for side in (-1,1):
 roof=cube('Barn · sloping roof',(-7.85+side*.98,5,3.13),(2.25,3.2,.16),roofMat,bevel=.055);roof.rotation_euler.y=side*math.radians(28)
 cube('Barn · ivory corner',(-9.71 if side<0 else -5.99,3.60,1.35),(.14,.15,2.8),trim,bevel=.02)
 cube('Barn · door panel',(-7.85+side*.42,3.60,.95),(.80,.10,1.8),woodLight,bevel=.06)
 for z in (.19,1.72):cube('Barn · door cross bar',(-7.85+side*.42,3.51,z),(.80,.06,.09),trim,bevel=.02)
curve('Barn · arched cream doorway',[(-8.8,3.50,.1),(-8.8,3.50,1.82),(-7.85,3.50,2.22),(-6.90,3.50,1.82),(-6.90,3.50,.1)],.075,trim)
for x in (-9.12,-6.58):
 cube('Barn · window frame',(x,3.56,1.85),(.65,.12,.70),trim,bevel=.06);cube('Barn · pale blue window',(x,3.48,1.85),(.48,.04,.53),mat('Blue window',(.30,.73,.85),.15),bevel=.03)
 cube('Barn · window mullion',(x,3.43,1.85),(.035,.04,.53),trim,bevel=.01);cube('Barn · window transom',(x,3.43,1.85),(.48,.04,.035),trim,bevel=.01)
# Little shed stores safe planks and a rope; no uncredited model files.
cube('Shed timber wall',(-4.4,3.7,.80),(1.7,1.3,1.6),wood,bevel=.09);cube('Shed roof',(-4.4,3.7,1.69),(2.05,1.6,.18),roofMat,bevel=.08)
for z in (.4,.85,1.3):cube('Shed horizontal seams',(-4.4,3.035,z),(1.65,.025,.025),woodLight,bevel=.01)
for i in range(9):
 x=-11+i*.68;cube('Fence · rounded post',(x,2.0,.48),(.11,.12,.95),trim,bevel=.05)
for z in (.35,.72):cube('Fence · honey rail',(-8.3,2.0,z),(5.8,.09,.10),woodLight,bevel=.04)
# Soft round trees, trunks, forked branches and individually shaded canopy lobes.
for x,y,size in [(-12,5,1.4),(-10,9,1.5),(-3,7,1.3),(3.8,5,1.4),(5.2,7,1.6),(7,3.5,1.3),(9,9,1.5),(3.3,9,1.6),(-13,-1,1.1)]:
 curve('Tree · sculpted trunk',[(x,y,0),(x+.1,y,.9*size),(x-.1,y,2.4*size)],.14*size,wood)
 for j in range(5):
  ang=j*math.pi*2/5;egg('Tree · round leafy crown',(x+math.cos(ang)*.45*size,y+math.sin(ang)*.40*size,2.4*size+(.25 if j%2 else -.05)),(.75*size,.7*size,.78*size),leafMat if j%2 else leafDark,None,20)
# Flowers are chunky and readable; deterministic placement avoids the stream and deck.
for i in range(90):
 x=R.uniform(-13,8);y=R.uniform(-2.7,7)
 if abs(x)<1.5 or (-3.6<x<-.9 and -.5<y<1.4):continue
 z=.13;curve('Meadow · flower stem',[(x,y,0),(x+.015,y,z+.16)],.012,leafDark)
 color=[flowerPink,flowerBlue,flowerWhite][i%3];r=R.uniform(.045,.075)
 for j in range(5):
  a=j*2*math.pi/5;egg('Meadow · soft petal',(x+math.cos(a)*r,y+math.sin(a)*r,z+.17),(.065,.05,.025),color,None,12)
 egg('Meadow · flower heart',(x,y,z+.19),(.034,.034,.025),gold,None,12)
# Modest tufts, no millions of hair strands.
for i in range(75):
 x=R.uniform(-11,7);y=R.uniform(-3,8)
 if abs(x)<1.3:continue
 for j in (-1,0,1):curve('Meadow · soft grass blade',[(x,y,0),(x+j*.04,y+.025,.17+abs(j)*.05)],.013,grass2)
# Old bridge stays closed upstream: no character ever uses it.
old=rig('Old closed crossing');old.location=(0,3.1,.1)
for side in (-1,1):
 for i in range(3):cube('Old bridge · broken dry end',(side*(1.05-i*.17),0,.11),(.16,.65,.10),wood,old,bevel=.04)
 cube('Old bridge · closed barrier',(side*1.45,0,.45),(.10,1.0,.06),red,old,bevel=.02)
 for yy in (-.42,.42):cube('Old bridge · barrier post',(side*1.45,yy,.22),(.07,.08,.5),woodLight,old,bevel=.025)
# Props and final safe, fantastical supported crossing.
board1=rig('Short board');board1.location=(-2.9,-.45,.12);cube('First rounded plank',(0,0,0),(1.30,.43,.10),woodLight,board1,bevel=.045)
board2=rig('Second board and rope');board2.location=(-4.65,-.4,.15);cube('Second rounded plank',(0,0,0),(1.30,.43,.10),woodLight,board2,bevel=.045)
for i in range(3):
 coords=[(-.10+(.22+i*.035)*math.cos(k*2*math.pi/40),-.4+(.22+i*.035)*math.sin(k*2*math.pi/40),.05+i*.03) for k in range(41)];curve('Coiled sturdy rope',coords,.022,ropeMat,board2)
bridge=rig('New firm crossing')
for x in (-1.15,0,1.15):
 egg('Crossing · broad fixed support',(x,0,.05),(.25,.56,.16),stone,bridge,20)
for x in (-.62,.62):
 cube('Crossing · joined safe deck',(x,0,.25),(1.30,.93,.12),woodLight,bridge,bevel=.045)
 for y in (-.29,0,.29):curve('Crossing · fine plank grain',[(x-.56,y,.315),(x,y+.015,.315),(x+.56,y,.315)],.007,wood,bridge)
for side in (-1,1):
 for x in (-1.30,0,1.30):
  cube('Crossing · rope rail post',(x,side*.52,.60),(.08,.08,.85),wood,bridge,bevel=.035)
 curve('Crossing · secure hand rope',[(-1.30,side*.52,1.0),(0,side*.52,.91),(1.30,side*.52,1.0)],.025,ropeMat,bridge)
# Broad stepping rock is only scenery; no jump is animated.
egg('Stream · broad gentle rock',(.18,1.2,.05),(.34,.45,.12),stone)

S.render.engine='CYCLES';S.cycles.samples=args.samples if not args.preview else 16;S.cycles.use_denoising=False;S.cycles.max_bounces=4;S.cycles.diffuse_bounces=2;S.cycles.glossy_bounces=2;S.cycles.use_adaptive_sampling=True;S.cycles.adaptive_threshold=.08;S.render.threads_mode='FIXED';S.render.threads=args.render_threads;S.render.resolution_x=1920;S.render.resolution_y=1080;S.render.resolution_percentage=50 if args.preview else 100;S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGB';S.render.film_transparent=False;S.view_settings.view_transform='AgX';S.view_settings.look='AgX - Medium High Contrast';S.render.fps=30
w=bpy.data.worlds.new('Warm pastel blue sky');w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.45,.69,.85,1);w.node_tree.nodes['Background'].inputs[1].default_value=.55;S.world=w

def area(name,loc,power,color,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);S.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((-2,0,0))-o.location).to_track_quat('-Z','Y').to_euler();return o
key=area('Large soft sunshine',(-5,-6,10),1800,(1,.83,.60),6);fill=area('Gentle sky fill',(5,-2,7),1000,(.70,.86,1),7);rim=area('Warm edge light',(-1,5,8),2200,(1,.75,.43),5)
d=bpy.data.lights.new('Afternoon sun','SUN');d.energy=1.8;d.angle=.13;o=bpy.data.objects.new('Afternoon sun',d);S.collection.objects.link(o);o.rotation_euler=(.45,-.5,-.4)
# Root lists stay identical throughout the story; poses and cameras only change.
for root in (pepe,pio,lola,nube,butterfly,board1,board2,bridge):
 GROUPS[root.name]=[root,*root.children_recursive]
BASE={o.name:(o.location.copy(),o.rotation_euler.copy(),o.scale.copy()) for o in bpy.data.objects if o.parent}

def visible(root,yes):
 for o in GROUPS[root.name]:o.hide_render=not yes

def pose(n):
 for name,(loc,rot,scale) in BASE.items():ob=bpy.data.objects[name];ob.location=loc;ob.rotation_euler=rot;ob.scale=scale
 for root in (pepe,pio,lola,nube,butterfly,board1,board2,bridge):visible(root,False);root.rotation_euler=(0,0,0)
 visible(pepe,True);pepe.location=(-6,0,0);pio.location=(2,0,0);lola.location=(-3.1,.3,0);nube.location=(-4.10,-.35,0);butterfly.location=(-2.5,0,1.7)
 camera=(-6,-9,4.3);target=(-6,1.3,1.0);lens=42
 if n==2:camera=(-6,-4.2,2.1);target=(-6,0,1.32);lens=57;pepe.rotation_euler.z=-.12
 if n==3:camera=(-6,-5.2,2.5);target=(-6,0,1.05);lens=50;ACT['pepe_wing_-1'].rotation_euler.y=-.55;ACT['pepe_wing_1'].rotation_euler.y=.30
 if n==4:visible(pio,True);pio.location=(-5.05,-.2,0);camera=(-5.7,-5.8,2.6);target=(-5.5,0,.9);lens=48
 if n in (5,6):
  visible(pepe,False);visible(pio,True);visible(butterfly,True);pio.location=(-3.1 if n==5 else -2.1,.6 if n==5 else 1.2,0);butterfly.location=(pio.location.x+.48,pio.location.y+.08,1.18);camera=(pio.location.x,-4.3,2.1);target=(pio.location.x+.15,.6,.65);lens=51 if n==5 else 39
 if n in (7,8,9):
  visible(pepe,False);visible(pio,True);camera=(0,-9,4.8) if n==7 else (1,-4.7,2.2);target=(0,1,.2) if n==7 else (2,0,.55);lens=40 if n==7 else 52
 if n==9:camera=(2,-2.9,1.25);target=(2,0,.67);lens=57;pio.rotation_euler.z=-.08
 if n==7:pio.location=(-1.70,.5,0) # before the narrated crossing, Pío is still on the home bank
 if n==10:pepe.location=(-3.9,0,0);camera=(-4,-5.0,2.3);target=(-3.8,0,.95);lens=48;ACT['pepe_leg_-1'].rotation_euler.x=.23;ACT['pepe_leg_1'].rotation_euler.x=-.23;pepe.rotation_euler.y=-.10
 if n in (11,12,13,14,17,18,19,20,21,22):
  pepe.location=(-2.0,0,0);visible(pio,True);camera=(0,-9,4.3);target=(-.25,.4,.7);lens=44
 if n==12:camera=(-2,-4.1,2.15);target=(-2,0,1.2);lens=55;ACT['pepe_wing_1'].rotation_euler.y=-.5;pepe.rotation_euler.z=.12
 if n==13:pepe.location=(-1.75,0,0);camera=(-.1,-6.9,3.3);target=(-.1,0,.75);lens=43
 if n==14:camera=(-1.8,-4.5,2.4);target=(-1.9,0,.95);lens=46;ACT['pepe_wing_-1'].rotation_euler.y=-.65;ACT['pepe_wing_1'].rotation_euler.y=.65
 if n in (15,16):
  pepe.location=(-4.0,.1,0);visible(board1,True);visible(board2,n==16);camera=(-3.8,-5.5,2.8);target=(-3.9,1,.65);lens=45;ACT['pepe_wing_1'].rotation_euler.y=.45
 if n in (17,18,22):visible(lola,True);visible(nube,True);camera=(-.8,-9,4.3);target=(-.8,.4,.8);lens=40
 if n>=18 and n<=22:visible(bridge,True)
 if n==19:pio.location=(.95,-.08,.31);camera=(.3,-6.1,2.8);target=(-.15,0,.75);lens=46
 if n==20:pio.location=(-1.65,-.35,0);pepe.location=(-2.55,0,0);camera=(-1.9,-5.0,2.4);target=(-1.9,0,.9);lens=46
 if n in (21,22):
  pio.location=(-1.58,-.38,0);pepe.location=(-2.1,-.02,0);ACT['pepe_wing_1'].rotation_euler.y=.62
  if n==21:camera=(-1.85,-4.5,2.2);target=(-1.85,-.1,.9);lens=55
 if n==22:visible(butterfly,True);butterfly.location=(-2.15,0,2.35);lola.location=(-3.30,.3,0);nube.location=(-4.20,-.25,0)
 if n in (23,24,25,26):
  key.data.color=(1,.63,.34);rim.data.color=(1,.53,.25);w.node_tree.nodes['Background'].inputs[0].default_value=(.65,.48,.46,1)
  if n>=24:visible(pio,True);pio.location=(-5.1,-.1,0)
  if n==23:camera=(-6,-6.0,2.8);target=(-6,.3,1.15);lens=50
  if n==24:camera=(-5.5,-6.7,2.9);target=(-5.3,.7,1.1);lens=50;pepe.rotation_euler.z=-.18;pio.rotation_euler.z=-.25
  if n==25:camera=(-5.5,-5,2.4);target=(-5.45,0,.85);lens=48;pepe.rotation_euler.z=.23;pio.rotation_euler.z=-.25
  if n==26:visible(lola,True);visible(nube,True);visible(butterfly,True);lola.location=(-7.1,.2,0);nube.location=(-4.45,.45,0);butterfly.location=(-5.8,.3,2.5);camera=(-5.5,-12.0,5.3);target=(-6.1,2.3,1.0);lens=41
 else:key.data.color=(1,.83,.60);rim.data.color=(1,.75,.43);w.node_tree.nodes['Background'].inputs[0].default_value=(.45,.69,.85,1)
 return camera,target,lens

cameras=[]
for n in range(1,27):
 position,target,lens=pose(n);d=bpy.data.cameras.new(f'P{n:02d} · fixed editorial camera');d.lens=lens;d.clip_end=250;o=bpy.data.objects.new(f'Camera P{n:02d}',d);S.collection.objects.link(o);o.location=position;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();cameras.append(o)
 marker=S.timeline_markers.new(f'P{n:02d}',frame=n);marker.camera=o
 for obj in bpy.data.objects:
  if obj.type!='CAMERA':
   obj.keyframe_insert(data_path='hide_render',frame=n)
   if obj in ACT.values():obj.keyframe_insert(data_path='location',frame=n);obj.keyframe_insert(data_path='rotation_euler',frame=n)
 key.data.keyframe_insert(data_path='color',frame=n);rim.data.keyframe_insert(data_path='color',frame=n);w.node_tree.nodes['Background'].inputs[0].keyframe_insert('default_value',frame=n)
for action in bpy.data.actions:
 for f in action.fcurves:
  for k in f.keyframe_points:k.interpolation='CONSTANT'
S.frame_start=1;S.frame_end=26;S.camera=cameras[0];S.frame_set(1);S['production_note']='26 individual original still illustrations, shared exact geometry, object-pivot rigs, CPU Cycles. Camera movement assembled by AutoStudio. Not full character animation.';S['source_generator']='scripts/pepe/art.py';S['character_ids']='Pepe|Pío|Lola|Nube';S['continuity']='Safe/home bank x < -1; Pío starts isolated x=2; new deck appears P18; Pío crosses right-to-left P19-P20.'
master=OUT/('pepe-e01-master-v002.blend' if args.samples!=32 else 'pepe-e01-master-v001.blend');bpy.ops.wm.save_as_mainfile(filepath=str(master))
if args.motion_start is not None:
 # Genuine 3D walk across the safe bridge, NOT a translated flat character image.
 S.frame_set(20)
 for ob in bpy.data.objects:
  if ob.type!='CAMERA':
   for field in ('hide_render','location','rotation_euler'):ob.keyframe_insert(data_path=field,frame=1001)
 key.data.keyframe_insert(data_path='color',frame=1001);rim.data.keyframe_insert(data_path='color',frame=1001);w.node_tree.nodes['Background'].inputs[0].keyframe_insert('default_value',frame=1001)
 d=bpy.data.cameras.new('Crossing motion camera');d.lens=43;cam=bpy.data.objects.new('Crossing motion camera',d);S.collection.objects.link(cam);cam.location=(0,-8,3.6);cam.rotation_euler=(Vector((-.3,0,.85))-cam.location).to_track_quat('-Z','Y').to_euler();S.camera=cam;marker=S.timeline_markers.new('P20 actual crossing animation · 12 fps',frame=1001);marker.camera=cam
 pepe.location=(-2.1,0,0);pepe.keyframe_insert(data_path='location',frame=1001)
 feet=[o for o in pio.children_recursive if 'little toe' in o.name];wings=[o for o in pio.children_recursive if 'fluffy wing' in o.name]
 for k in range(args.motion_total):
  t=k/12;u=min(t/5.7,1);ease=.5-.5*math.cos(math.pi*u);x=.95-2.53*ease;lift=.31*(1-min(max((-x-1.15)/.43,0),1));bob=.018*math.sin(t*math.pi*4)**2 if u<1 else 0
  pio.location=(x,-.08,lift+bob);pio.rotation_euler.z=-math.pi/2;pio.keyframe_insert(data_path='location',frame=1001+k);pio.keyframe_insert(data_path='rotation_euler',frame=1001+k)
  for j,foot in enumerate(feet):foot.location.z=-bob+(.035*max(0,math.sin(t*math.pi*4+(math.pi if j<3 else 0))) if u<1 else 0);foot.keyframe_insert(data_path='location',frame=1001+k)
  for j,wing in enumerate(wings):wing.rotation_euler.y=(1 if j else -1)*.12*math.sin(t*4);wing.keyframe_insert(data_path='rotation_euler',frame=1001+k)
 for act in bpy.data.actions:
  for fc in act.fcurves:
   for k in fc.keyframe_points:
    if k.co.x>=1001:k.interpolation='LINEAR' if fc.data_path!='hide_render' else 'CONSTANT'
 S.frame_start=1001;S.frame_end=1000+args.motion_total;S.render.fps=12;S.render.resolution_x=1280;S.render.resolution_y=720;S.render.resolution_percentage=100;S.cycles.samples=12;S['production_note']='26 source still poses at frames 1-26; actual 3D Pío bridge walk at 1001-1084, native 1280x720 at 12 fps. Assembly interpolates 30 fps; no claim of native 1080p character animation.'
 master=OUT/'pepe-e01-motion-master-v001.blend';S.frame_set(1001);S.camera=cam;bpy.ops.wm.save_as_mainfile(filepath=str(master))
 records=[];folder=OUT/'motion';folder.mkdir(exist_ok=True)
 crop=None
 if args.motion_crop:
  # Original 3D region rendering over its own invariant background. No sheet crops.
  from bpy_extras.object_utils import world_to_camera_view
  S.frame_set(1001);S.camera=cam
  for ob in [pio,*pio.children_recursive]:ob.hide_render=True
  S.render.filepath=str(OUT/'motion-background.png');bpy.ops.render.render(write_still=True)
  projected=[world_to_camera_view(S,cam,Vector((x,y,z))) for x in (-2.15,1.55) for y in (-.85,.8) for z in (-.12,1.45)]
  w,h=1280,720;x0=max(0,int((min(p.x for p in projected)-.035)*w));x1=min(w,int((max(p.x for p in projected)+.035)*w)+1);y0=max(0,int((min(p.y for p in projected)-.035)*h));y1=min(h,int((max(p.y for p in projected)+.035)*h)+1)
  S.render.use_border=True;S.render.use_crop_to_border=True;S.render.border_min_x=x0/w;S.render.border_max_x=x1/w;S.render.border_min_y=y0/h;S.render.border_max_y=y1/h;crop=[x0,y0,x1,y1]
  (OUT/'motion-crop.json').write_text(json.dumps({'crop_bottom_left':crop,'canvas':[w,h],'fps':12,'frames':args.motion_total,'background':'motion-background.png','technique':'Actual Cycles region renders composited onto the same static 3D camera background; all foreground occlusions and lighting rendered in 3D.'},indent=2)+'\n')
 for k in range(args.motion_start,args.motion_end):
  S.frame_set(1001+k);S.camera=cam;target=folder/f'frame-{k:04}.png';S.render.filepath=str(target);start=time.time();bpy.ops.render.render(write_still=True);records.append({'frame':k,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'seconds':round(time.time()-start,3),'native_dimensions':([crop[2]-crop[0],crop[3]-crop[1]] if crop else [1280,720]),'canvas':[1280,720],'region_render':crop,'fps':12,'blender_version':bpy.app.version_string});print('PEPE_MOTION',k,flush=True)
 (OUT/f'motion-{args.motion_start:03}.json').write_text(json.dumps(records,indent=2)+'\n')
 raise SystemExit(0)
records=[]
for n in (args.shots or list(range(1,27))):
 S.frame_set(n);S.camera=cameras[n-1];target=OUT/'media'/f'shot-{n:02}.png'
 if args.preview:target=OUT/f'preview-{n:02}.png'
 S.render.filepath=str(target);start=time.time();bpy.ops.render.render(write_still=True);record={'shot':n,'file':target.name,'seconds':round(time.time()-start,3),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'native_resolution':[int(S.render.resolution_x*S.render.resolution_percentage/100),int(S.render.resolution_y*S.render.resolution_percentage/100)],'render_engine':'Cycles CPU','blender_version':bpy.app.version_string,'samples':S.cycles.samples,'reference_sheet_used':False};records.append(record);(OUT/f'render-shot-{n:02}.json').write_text(json.dumps(record,indent=2)+'\n');print('PEPE_RENDER',json.dumps(record),flush=True)
(OUT/('preview-render.json' if args.preview else 'render-'+str((args.shots or [0])[0])+'.json')).write_text(json.dumps(records,indent=2)+'\n')
