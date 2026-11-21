"""Read-only audit of the latest real user Director input; never publish user media/text."""
import argparse,json,tempfile,zipfile,urllib.request,re
from pathlib import Path
from scripts.director.cloud import get_json,download,api

def audit():
 releases=get_json('/releases?per_page=100');checked=0
 for release in releases:
  if not release.get('draft'):continue
  try:intent=json.loads(release.get('body','{}'))
  except ValueError:continue
  if intent.get('autostudio_director')!=1:continue
  assets={a['name']:a for a in release['assets']}
  if not {'project.zip','result.json'}<=assets.keys():continue
  checked+=1
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'input.zip';download(assets['project.zip'],path,intent['bundle_sha256'])
   with zipfile.ZipFile(path) as z:
    if z.getinfo('project.json').file_size>2_000_000:raise ValueError('Project metadata too large')
    project=json.loads(z.read('project.json'))
  title=project.get('title','').upper()
  if any(word in title for word in ('ENSAYO','NO HESSDALEN','EDITOR SENCILLO')):continue
  # Public API authenticated asset request, with token stripped on signed redirect.
  from scripts.director.cloud import NoRedirect
  import os,urllib.error
  request=urllib.request.Request(assets['result.json']['url'],headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/octet-stream','User-Agent':'AutoStudio-Director'})
  try:response=urllib.request.build_opener(NoRedirect).open(request,timeout=30)
  except urllib.error.HTTPError as error:
   if error.code not in (301,302,303,307):raise
   target=error.headers['Location'];host=__import__('urllib.parse',fromlist=['urlparse']).urlparse(target).hostname
   if host!='release-assets.githubusercontent.com' and not host.endswith('.blob.core.windows.net'):raise ValueError('Invalid signed asset host')
   response=urllib.request.urlopen(target,timeout=30)
  with response:result=json.load(response)
  raw=project.get('_quick',{}).get('text','');paragraphs=[p.strip() for p in re.split(r'\n\s*\n',raw.replace('\r','')) if p.strip() and not p.strip().startswith('#')]
  scenes=[s for c in project.get('chapters',[]) for s in c.get('scenes',[])]
  exact=len(paragraphs)==len(scenes) and all(a.split()==s.get('narration','').split() for a,s in zip(paragraphs,scenes))
  paths=[s.get('media',{}).get('path') for s in scenes]
  return {'found_user_input':True,'request_id':intent['request_id'],'source_ref':intent.get('source_ref'),'renderer_source_commit':result.get('source_commit'),'renderer_run_id':result.get('github_run_id'),'renderer_status':result.get('status'),'rendered_seconds':result.get('duration'),'original_paragraph_count':len(paragraphs),'rendered_scene_count':len(scenes),'paragraphs_preserved_1_to_1':exact,'repeated_resource_assignments':len(paths)-len(set(paths)),'scope':'Read-only inspection of actual uploaded JSON and production result. No user text, titles, images or media exported.'}
 return {'found_user_input':False,'checked_drafts':checked,'scope':'No completed non-fixture Director input found among latest releases; source-code audit remains applicable'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(audit(),ensure_ascii=False,indent=2)+'\n')
