"""Versioned documentary contract. Input is data, never code or network URLs."""
from __future__ import annotations
import hashlib,json,math,re,subprocess,zipfile,stat
from pathlib import Path

SCHEMA='autostudio-director/1'
FORMATS={'horizontal':(1920,1080),'vertical':(1080,1920)}
ID=re.compile(r'[a-zA-Z0-9_-]{1,64}')
LICENSES={'original_user','own_creation','cc0','cc_by_4','cc_by_sa_4','public_domain_verified','other_verified'}
MAX_BUNDLE=200*1024*1024

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def number(value,low,high,label):
    if type(value) not in (int,float) or not math.isfinite(value) or not low<=value<=high:
        raise ValueError('Valor inválido: '+label)
    return float(value)

def media_file(root,name,extensions):
    if not isinstance(name,str) or not name or len(name)>240 or '\\' in name or any(ord(c)<32 for c in name):
        raise ValueError('Ruta de recurso inválida')
    rel=Path(name)
    if rel.is_absolute() or '..' in rel.parts or ':' in name:raise ValueError('Ruta fuera del proyecto')
    base=Path(root).resolve();p=base/rel
    # Inspect the un-resolved chain too: a symlink inside the root is not input media.
    if any(x.is_symlink() for x in [p,*p.parents] if x!=base.parent):raise ValueError('Enlace simbólico no permitido')
    p=p.resolve(strict=True)
    if base not in p.parents or not p.is_file() or p.suffix.lower() not in extensions:raise ValueError('Recurso no permitido: '+name)
    if not 0<p.stat().st_size<=MAX_BUNDLE:raise ValueError('Recurso vacío o demasiado grande')
    return p

def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],text=True,timeout=45))

def rights(item):
    r=item.get('rights',{})
    if r.get('license') not in LICENSES:raise ValueError('Falta licencia declarada del recurso')
    if r['license'] not in {'original_user','own_creation','cc0'} and (not r.get('credit') or not str(r.get('source_url','')).startswith('https://')):
        raise ValueError('Falta autor o procedencia del recurso ajeno')

def validate_visual(scene,root,media_seen,strict):
    m=scene.get('media',{});kind=m.get('kind')
    if kind not in ('image','video'):raise ValueError('Tipo de medio inválido')
    media_file(root,m.get('path'),{'.jpg','.jpeg','.png','.webp'} if kind=='image' else {'.mp4'})
    rights(m)
    if strict:
        if type(m.get('allow_reuse',False)) is not bool:raise ValueError('La autorización de reutilización debe ser explícita y booleana')
        fingerprint=digest(media_file(root,m.get('path'),{'.jpg','.jpeg','.png','.webp','.mp4'}))
        if fingerprint in media_seen and not m.get('allow_reuse',False):raise ValueError('Recurso repetido entre párrafos sin autorización explícita')
        media_seen.add(fingerprint)
    if m.get('fit','contain') not in ('contain','cover','blur'):raise ValueError('Ajuste de imagen inválido')
    number(m.get('trim_start',0),0,3600,'inicio del clip')
    if m.get('source_audio',False) is not False:raise ValueError('Audio de clips silenciado en esta revisión; importa la pista como narración o efecto')
    if type(m.get('loop',False)) is not bool:raise ValueError('Bucle inválido')
    keys=scene.get('camera',{}).get('keyframes',[])
    if keys:
        if kind!='image' or not 2<=len(keys)<=8:raise ValueError('Fotogramas clave solo para imágenes (2–8)')
        previous=-1
        for k in keys:
            t=number(k.get('at'),0,1,'tiempo de cámara')
            if t<=previous:raise ValueError('Fotogramas clave fuera de orden')
            previous=t
            for axis in ('x','y'):number(k.get(axis,.5),0,1,axis)
            number(k.get('zoom',1.05),1,1.25,'zoom')
        if keys[0]['at']!=0 or keys[-1]['at']!=1:raise ValueError('Cámara debe cubrir 0–1')
    for layer in m.get('layers',[]):
        if kind!='image':raise ValueError('Parallax solo con imágenes')
        media_file(root,layer.get('path'),{'.png','.webp'});rights(layer)
        for point in ('from','to'):
            values=layer.get(point,[0,0])
            if not isinstance(values,list) or len(values)!=2:raise ValueError('Posición parallax inválida')
            for v in values:number(v,-.04,.04,'desplazamiento de capa')
    if len(m.get('layers',[]))>3:raise ValueError('Máximo tres capas parallax')
    tr=scene.get('transition',{'type':'cut','seconds':0})
    if tr.get('type') not in ('cut','dissolve','wipeleft','smoothleft'):raise ValueError('Transición no compatible')
    number(tr.get('seconds',0),0,1,'transición')

def validate(data,root):
    if not isinstance(data,dict) or data.get('schema')!=SCHEMA:raise ValueError('Formato Director no compatible')
    if data.get('youtube_enabled') is not False:raise ValueError('YouTube debe permanecer desactivado')
    if not isinstance(data.get('title'),str) or not 3<=len(data['title'])<=160:raise ValueError('Título inválido')
    if data.get('scene_policy') not in (None,'paragraph/1'):raise ValueError('Política de escenas desconocida')
    subtitles=data.get('subtitles',{})
    if not isinstance(subtitles,dict) or type(subtitles.get('enabled',True)) is not bool or subtitles.get('style','documentary') not in ('documentary','cinematic','dynamic'):raise ValueError('Ajuste de subtítulos inválido')
    strict=data.get('scene_policy')=='paragraph/1';media_seen=set()
    if data.get('format') not in FORMATS or data.get('fps',30) not in (30,60):raise ValueError('Formato o FPS no compatible')
    chapters=data.get('chapters');seen=set();count=0
    if not isinstance(chapters,list) or not 1<=len(chapters)<=24:raise ValueError('Se requieren entre 1 y 24 capítulos')
    for chapter in chapters:
        if not isinstance(chapter,dict):raise ValueError('Capítulo inválido')
        if chapter.get('id') in ('scene-cache','visual-cache','narration-cache'):raise ValueError('ID de capítulo reservado para caché')
        scenes=chapter.get('scenes')
        if not isinstance(scenes,list) or not 1<=len(scenes)<=30:raise ValueError('Máximo 30 escenas por capítulo; divide el guion')
        for obj in [chapter,*scenes]:
            ident=obj.get('id')
            if not isinstance(ident,str) or not ID.fullmatch(ident) or ident in seen:raise ValueError('IDs ausentes o duplicados')
            seen.add(ident)
        for scene in scenes:
            count+=1
            if not isinstance(scene.get('narration'),str) or not 1<=len(scene['narration'])<=6000:raise ValueError('Narración de escena inválida')
            number(scene.get('pause_after',.35),0,10,'pausa posterior')
            if strict and len(re.split(r'\n\s*\n',scene['narration'].replace('\r\n','\n').replace('\r','\n').strip()))!=1:raise ValueError('Cada escena debe contener un único párrafo')
            if 'subshots' in scene:
                if not strict:raise ValueError('Los subplanos requieren scene_policy paragraph/1')
                from scripts.director.subshots import ranges
                ranges(scene)
                for shot in scene['subshots']:
                    ident=shot.get('id')
                    if not isinstance(ident,str) or not ID.fullmatch(ident) or ident in seen:raise ValueError('ID de subplano ausente o repetido')
                    seen.add(ident);validate_visual(shot,root,media_seen,strict)
                    if shot.get('transition',{}).get('type','cut') not in ('cut','dissolve'):raise ValueError('Subplanos: corte o disolución en pausa')
                scene['media']=scene['subshots'][0]['media'] # backward-compatible poster; not another visual slot
            else:validate_visual(scene,root,media_seen,strict)
            n=scene.get('voice',data.get('voice',{'mode':'kokoro','voice':'em_alex'}))
            if n.get('mode')=='file':
                media_file(root,n.get('path'),{'.wav','.mp3'})
            elif n.get('mode')!='kokoro' or n.get('voice','em_alex') not in ('em_alex','em_santa','ef_dora'):
                raise ValueError('Narración no compatible')
            for effect in scene.get('effects',[]):
                media_file(root,effect.get('path'),{'.wav','.mp3'});rights(effect)
                number(effect.get('at',0),0,180,'posición de efecto');number(effect.get('gain',.2),0,.5,'volumen efecto')
    music=data.get('music')
    if music:
        media_file(root,music.get('path'),{'.wav','.mp3'});rights(music);number(music.get('gain',.12),0,.3,'volumen musical')
    return data

def load(path):
    p=Path(path)
    if p.stat().st_size>2_000_000:raise ValueError('Proyecto demasiado grande')
    return validate(json.loads(p.read_text(encoding='utf-8')),p.parent)

def extract_bundle(source,dest):
    """Bounded ZIP extraction; reject traversal, duplicate names, symlinks, bombs."""
    source=Path(source);dest=Path(dest)
    if source.stat().st_size>MAX_BUNDLE:raise ValueError('Paquete superior a 200 MiB')
    if dest.exists() and any(dest.iterdir()):raise ValueError('La carpeta de destino debe estar vacía')
    with zipfile.ZipFile(source) as z:
        infos=z.infolist();total=0;names=set()
        if len(infos)>3000:raise ValueError('Demasiados archivos')
        for i in infos:
            name=i.filename;rel=Path(name);total+=i.file_size
            if name in names or rel.is_absolute() or '..' in rel.parts or '\\' in name or ':' in name or stat.S_ISLNK(i.external_attr>>16):raise ValueError('ZIP no seguro')
            names.add(name)
            if total>MAX_BUNDLE or i.flag_bits&1:raise ValueError('ZIP cifrado o expansión excesiva')
        if 'project.json' not in names:raise ValueError('Falta project.json en la raíz del ZIP')
        dest.mkdir(parents=True,exist_ok=True)
        for i in infos:
            target=dest/i.filename
            if i.is_dir():target.mkdir(parents=True,exist_ok=True);continue
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(i) as src,target.open('xb') as out:
                for block in iter(lambda:src.read(1024*1024),b''):out.write(block)
    return load(dest/'project.json')
