"""GitHub-only transport: temporary draft release assets, never media in Git.

Authentication is sent only to api.github.com or uploads.github.com. Signed asset
redirects are fetched without credentials. No paid API/Artifacts/cache services.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,subprocess,urllib.request,urllib.error,urllib.parse
from pathlib import Path
from scripts.director.project import MAX_BUNDLE,extract_bundle,digest
REPO='Luixifer/AutoStudio'
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None

def api(path,method='GET',body=None,accept='application/vnd.github+json'):
 token=os.environ.get('GITHUB_TOKEN')
 if not token:raise RuntimeError('Falta autorización GitHub; no hay credenciales incluidas')
 url='https://api.github.com/repos/'+REPO+path
 headers={'Authorization':'Bearer '+token,'Accept':accept,'User-Agent':'AutoStudio-Director','X-GitHub-Api-Version':'2022-11-28'}
 if body is not None:headers['Content-Type']='application/json'
 request=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
 return urllib.request.build_opener(NoRedirect).open(request,timeout=60)

def get_json(path):
 with api(path) as response:return json.load(response)

def download(asset,path,expected):
 try:r=api('/releases/assets/'+str(asset['id']),accept='application/octet-stream')
 except urllib.error.HTTPError as e:
  if e.code not in (301,302,303,307,308):raise
  location=e.headers.get('Location','');u=urllib.parse.urlparse(location)
  if u.scheme!='https' or u.username or u.port or not (u.hostname=='release-assets.githubusercontent.com' or (u.hostname or '').endswith('.blob.core.windows.net')):
   raise RuntimeError('Redirección de descarga no reconocida')
  r=urllib.request.build_opener(NoRedirect).open(urllib.request.Request(location,headers={'User-Agent':'AutoStudio-Director'}),timeout=120)
 total=0
 with r,Path(path).open('xb') as out:
  for block in iter(lambda:r.read(1024*1024),b''):
   total+=len(block)
   if total>MAX_BUNDLE:raise ValueError('Paquete demasiado grande')
   out.write(block)
 if total!=asset['size'] or digest(path)!=expected:raise ValueError('La descarga no coincide con su SHA-256')

def upload(release,path):
 import http.client
 path=Path(path)
 if path.stat().st_size>=2*1024**3:raise ValueError('Resultado superior a 2 GiB; entrega capítulos por separado')
 # Use streaming HTTP, never read a 60-minute documentary into Python memory.
 uri='/repos/'+REPO+'/releases/'+str(release['id'])+'/assets?name='+urllib.parse.quote(path.name)
 conn=http.client.HTTPSConnection('uploads.github.com',timeout=300)
 try:
  conn.putrequest('POST',uri);conn.putheader('Authorization','Bearer '+os.environ['GITHUB_TOKEN']);conn.putheader('User-Agent','AutoStudio-Director');conn.putheader('Content-Type','application/octet-stream');conn.putheader('Content-Length',str(path.stat().st_size));conn.endheaders()
  with path.open('rb') as f:
   for block in iter(lambda:f.read(1024*1024),b''):conn.send(block)
  response=conn.getresponse();body=response.read(1024*1024)
  if response.status!=201:raise RuntimeError('No se pudo adjuntar el resultado a GitHub: HTTP '+str(response.status))
  return json.loads(body)
 finally:conn.close()

def execute(request_id,work):
 if not re.fullmatch('[a-f0-9]{32}',request_id):raise ValueError('Solicitud no válida')
 if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!=REPO:raise RuntimeError('Este transporte solo se ejecuta en el repositorio autorizado de Actions')
 try:release=get_json('/releases/tags/director-'+request_id)
 except urllib.error.HTTPError as error:
  if error.code!=404:raise
  release=None
  for page in range(1,4):
   items=get_json('/releases?per_page=100&page='+str(page))
   release=next((r for r in items if r.get('tag_name')=='director-'+request_id and r.get('draft')),None)
   if release or len(items)<100:break
  if release is None:raise ValueError('No se encuentra el borrador de esta solicitud')
 if not release.get('draft') or release['tag_name']!='director-'+request_id:raise ValueError('Se requiere una entrega de revisión, no una publicación')
 intent=json.loads(release.get('body','{}'))
 if intent.get('autostudio_director')!=1 or intent.get('request_id')!=request_id or not re.fullmatch('[a-f0-9]{64}',intent.get('bundle_sha256','')):raise ValueError('La solicitud no tiene integridad verificable')
 if intent.get('source_ref') not in ('codex/autostudio-director','codex/director-2-scene-integrity') or os.environ.get('DIRECTOR_EXPECTED_REF',intent.get('source_ref'))!=intent.get('source_ref'):raise ValueError('Revisión de motor no autorizada')
 assets=release['assets'];bundles=[a for a in assets if a['name']=='project.zip']
 if len(bundles)!=1 or bundles[0]['size']>MAX_BUNDLE:raise ValueError('Falta el paquete de entrada válido')
 if any(a['name']=='result.json' for a in assets):raise ValueError('Solicitud ya procesada; no se sobrescribe un resultado')
 work=Path(work);work.mkdir(parents=True,exist_ok=True);result={'request_id':request_id,'status':'failed','github_run_id':os.environ.get('GITHUB_RUN_ID'),'source_commit':os.environ.get('GITHUB_SHA'),'youtube_enabled':False,'physical_samsung_tested':False}
 try:
  bundle=work/'project.zip';download(bundles[0],bundle,intent['bundle_sha256']);extract_bundle(bundle,work/'input')
  from scripts.director.engine import produce
  report=produce(work/'input/project.json',work/'render')
  for name in ('documental-REVISION.mp4','captions.srt','validation.json','timeline.json','input-audit.json','SHA256SUMS'):
   asset=upload(release,work/'render'/name)
   if name.endswith('.mp4'):result.update({'asset_id':asset['id'],'bytes':asset['size'],'sha256':report['sha256'],'duration':report['duration'],'width':report['width'],'height':report['height']})
  result['scenes']=[{'id':s['id'],'voice_seconds':s['voice_seconds'],'text_sha256':__import__('hashlib').sha256(s['original_text'].encode()).hexdigest(),'media_sha256':s['input_media_sha256']} for s in json.loads((work/'render/timeline.json').read_text())['scenes']]
  if (work/'render/correspondence.json').is_file():upload(release,work/'render/correspondence.json')
  result['status']='completed'
 except Exception as error:
  result['error']=str(error)[:1500];raise
 finally:
  p=work/'result.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');upload(release,p)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--request-id',required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();execute(a.request_id,a.work)
