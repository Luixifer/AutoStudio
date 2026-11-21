"""Bounded, private, content-verified render cache on the user's own draft releases.
No paid cache service. Source assets, credentials and final movie are excluded.
"""
import json,re,stat,zipfile,hashlib,os
from pathlib import Path
from scripts.director.cloud import get_json,asset_stream,download,upload
from scripts.director.project import digest
MAX=512*1024*1024
NODES={'scene-cache':{'complete.json','visual.mp4','narration.wav','spoken.wav'},'visual-cache':{'complete.json','visual.mp4'},'narration-cache':{'complete.json','spoken.wav'}}

def allowed(name):
 parts=Path(name).parts
 if '\\' in name or ':' in name or '..' in parts or Path(name).is_absolute():return False
 if parts and parts[0] in NODES:return len(parts)==3 and bool(re.fullmatch('[a-f0-9]{64}',parts[1])) and parts[2] in NODES[parts[0]]
 return len(parts)==2 and bool(re.fullmatch('[a-zA-Z0-9_-]{1,64}',parts[0])) and parts[1] in ('chapter.mp4','chapter.json')

def restore_zip(archive,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(archive) as z:
  items=z.infolist();names=set()
  if len(items)>5000 or sum(i.file_size for i in items)>MAX:raise ValueError('Cache exceeds budget')
  for item in items:
   if item.filename in names or not allowed(item.filename) or stat.S_ISLNK(item.external_attr>>16) or item.is_dir():raise ValueError('Unsafe render cache')
   names.add(item.filename)
  for item in items:
   target=out/item.filename;target.parent.mkdir(parents=True,exist_ok=True)
   with z.open(item) as source,target.open('wb') as dest:
    for block in iter(lambda:source.read(1024*1024),b''):dest.write(block)
 return len(items)

class RemoteCache:
 def __init__(self,project_id,release,work,request_id):
  self.project_id=project_id;self.release=release;self.work=Path(work);self.request_id=request_id;self.last=None;self.uploaded=0;self.sequence=0
  self.stats={'enabled':bool(re.fullmatch('[a-f0-9]{32}',project_id or '')),'restored':False,'saved':False,'uploaded_bytes':0,'restored_files':0,'warnings':[]}
 def restore(self,out):
  if not self.stats['enabled']:return
  try:
   for page in range(1,4):
    releases=get_json('/releases?per_page=100&page='+str(page))
    for release in releases:
     if not release.get('draft') or release['id']==self.release['id']:continue
     try:body=json.loads(release.get('body','{}'))
     except ValueError:continue
     if body.get('project_id')!=self.project_id or body.get('autostudio_director')!=1:continue
     assets={a['name']:a for a in release['assets']};manifests=sorted((n for n in assets if re.fullmatch(r'render-cache-\d{3}\.json',n)),reverse=True)
     for name in manifests:
      with asset_stream(assets[name]) as stream:raw=stream.read(65537)
      if len(raw)>65536:raise ValueError('Cache manifest too large')
      manifest=json.loads(raw);zipname=name[:-5]+'.zip'
      if manifest.get('schema')!='director-render-cache/1' or manifest.get('project_id')!=self.project_id or zipname not in assets:continue
      if not re.fullmatch('[a-f0-9]{64}',manifest.get('sha256','')) or assets[zipname]['size']>MAX:raise ValueError('Invalid cache identity')
      path=self.work/'restored-cache.zip';download(assets[zipname],path,manifest['sha256'],MAX)
      files=restore_zip(path,out);self.stats.update(restored=True,restored_files=files,source_request=body.get('request_id'));return
    if len(releases)<100:break
  except Exception as error:self.stats['warnings'].append('Cache no reutilizada: '+str(error)[:200])
 def save(self,out):
  if not self.stats['enabled']:return
  try:
   out=Path(out);files=[]
   for namespace,allowed_files in NODES.items():
    base=out/namespace
    if base.exists():
     for folder in base.iterdir():
      if not folder.is_dir() or not (folder/'complete.json').is_file():continue
      files.extend(p for p in folder.iterdir() if p.is_file() and p.name in allowed_files and allowed(str(p.relative_to(out))))
   for folder in out.iterdir():
    if folder.is_dir() and (folder/'chapter.json').is_file():files.extend(p for p in (folder/'chapter.json',folder/'chapter.mp4') if p.is_file() and allowed(str(p.relative_to(out))))
   total=sum(p.stat().st_size for p in files)
   if not files:return
   if total>MAX-512*1024 or total+self.uploaded>MAX-512*1024:
    if 'Cache limitada a 512 MiB por producción' not in self.stats['warnings']:self.stats['warnings'].append('Cache limitada a 512 MiB por producción')
    return
   fingerprint=hashlib.sha256(json.dumps({str(p.relative_to(out)):digest(p) for p in sorted(files)},sort_keys=True).encode()).hexdigest()
   if fingerprint==self.last:return
   self.sequence+=1;name=f'render-cache-{self.sequence:03}';archive=self.work/(name+'.zip')
   with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
    for file in files:z.write(file,file.relative_to(out))
   upload(self.release,archive);manifest={'schema':'director-render-cache/1','project_id':self.project_id,'request_id':self.request_id,'sha256':digest(archive),'bytes':archive.stat().st_size,'files':len(files)}
   path=self.work/(name+'.json');path.write_text(json.dumps(manifest)+'\n');upload(self.release,path)
   self.last=fingerprint;self.uploaded+=archive.stat().st_size;self.stats.update(saved=True,uploaded_bytes=self.uploaded)
  except Exception as error:self.stats['warnings'].append('Cache no guardada: '+str(error)[:200])
