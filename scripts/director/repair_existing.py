"""Reprocess an authorized existing user test in a NEW PRIVATE draft.
Never modifies or publicly publishes the original script, media, release or result.
"""
import argparse,hashlib,json,os,re,zipfile,tempfile
from pathlib import Path
from scripts.director.cloud import get_json,download,upload,api,execute
from scripts.director.project import extract_bundle,digest,validate

REF='codex/director-2-scene-integrity'
def repair(source_id,out):
 if not re.fullmatch('[a-f0-9]{32}',source_id):raise ValueError('Invalid source request')
 release=None
 for page in range(1,4):
  entries=get_json('/releases?per_page=100&page='+str(page));release=next((r for r in entries if r.get('draft') and r.get('tag_name')=='director-'+source_id),None)
  if release or len(entries)<100:break
 if not release:raise ValueError('Source private draft unavailable')
 intent=json.loads(release['body']);asset=next(a for a in release['assets'] if a['name']=='project.zip')
 out=Path(out);out.mkdir(parents=True,exist_ok=True);archive=out/'original.zip';download(asset,archive,intent['bundle_sha256']);p=extract_bundle(archive,out/'input');raw=p.get('_quick',{}).get('text','')
 paragraphs=[part.strip() for part in re.split(r'\n\s*\n',raw.replace('\r\n','\n').replace('\r','\n')) if part.strip() and not part.strip().startswith('#')];images=p.get('_quick',{}).get('images',[])
 if not paragraphs or len(paragraphs)!=len(images):raise ValueError('User mapping required: '+str(len(paragraphs))+' paragraphs and '+str(len(images))+' resources; no guessed associations')
 old=[s for c in p['chapters'] for s in c['scenes']]
 if any(s.get('voice',{}).get('mode')=='file' for s in old) or p.get('voice',{}).get('mode')=='file':raise ValueError('External narration needs explicit paragraph mapping; not reassigned automatically')
 media={s['media']['path']:s['media'] for s in old};scenes=[]
 for i,(text,path) in enumerate(zip(paragraphs,images)):
  if path not in media:raise ValueError('Original resource not present in the original approved package')
  scenes.append({'id':'repaired-paragraph-'+str(i+1),'narration':text,'pause_after':.35,'media':media[path],'camera':{'movement':'zoom_in'},'transition':{'type':'dissolve','seconds':.35}})
 p.update(scene_policy='paragraph/1',subtitles={'enabled':True,'style':'documentary'},chapters=[{'id':'repaired-test','scenes':scenes}]);p['_quick']={'text':raw,'images':images,'confirmed':True};validate(p,out/'input')
 project=out/'input/project.json';project.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
 target=out/'project.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_STORED) as z:
  for path in (out/'input').rglob('*'):
   if path.is_file():z.write(path,path.relative_to(out/'input'))
 run=os.environ['GITHUB_RUN_ID'];new_id=hashlib.sha256(('repair:'+source_id+':'+run).encode()).hexdigest()[:32]
 body={'autostudio_director':1,'request_id':new_id,'source_ref':REF,'bundle_sha256':digest(target),'repair_of':source_id}
 with api('/releases','POST',{'tag_name':'director-'+new_id,'target_commitish':os.environ['GITHUB_SHA'],'name':'Director 2 · revisión privada '+source_id[:8],'draft':True,'prerelease':True,'body':json.dumps(body)}) as response:new_release=json.load(response)
 upload(new_release,target);execute(new_id,out/'production')
 qa=json.loads((out/'production/render/validation.json').read_text())
 # Download the actual private delivered MP4 again using the existing safe transport.
 result=json.loads((out/'production/result.json').read_text());delivered=get_json('/releases/'+str(new_release['id']));movie=next(a for a in delivered['assets'] if a['id']==result['asset_id']);download(movie,out/'downloaded-private.mp4',result['sha256'])
 report={'passed':qa['passed'],'source_request':source_id,'new_request':new_id,'run_id':run,'source_commit':os.environ['GITHUB_SHA'],'paragraphs':len(paragraphs),'scenes':len(scenes),'seconds':qa['duration'],'mp4_sha256':qa['sha256'],'private_release_url':new_release['html_url'],'requires_repository_owner_login':True,'original_release_unchanged':True,'downloaded_result_sha256_verified':True,'topic_hessdalen':('hessdalen' in (raw+' '+p.get('title','')).lower()),'contains_user_material':True,'publication':'New private draft only. No source text or images in public diagnostic.','human_listening_approved':False}
 (out/'safe-repair-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))
 return report
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--out',type=Path,required=True);a=parser.parse_args();repair(a.source,a.out)
