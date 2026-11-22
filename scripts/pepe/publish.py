"""Publish genuine original episode assets/movie, never technical substitutes."""
import argparse,json,os,zipfile
from pathlib import Path
from scripts.director.cloud import api,upload
from scripts.director.project import digest

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--part',required=True);a=p.parse_args()
 if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='Luixifer/AutoStudio':raise RuntimeError('Authorized genuine Actions only')
 run=os.environ['GITHUB_RUN_ID'];root=a.input;target=root.parent/(a.part+'.zip');files=[]
 if a.part.startswith('stills'):
  files=[*root.glob('media/shot-*.png'),*root.glob('render-*.json')]
  if a.part.endswith('0'):files.append(root/'pepe-e01-master-v001.blend')
 elif a.part.startswith('motion'):
  files=[*root.glob('motion/*.png'),*root.glob('motion-*.json')]
  if a.part.endswith('0'):files.append(root/'pepe-e01-motion-master-v001.blend')
 else:raise ValueError('Unknown part')
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
  for f in files:z.write(f,f.relative_to(root))
 manifest={'part':a.part,'source_commit':os.environ['GITHUB_SHA'],'run_id':run,'sha256':digest(target),'bytes':target.stat().st_size,'files':{str(f.relative_to(root)):digest(f) for f in files},'is_final_movie':False,'paid_services_used':False,'youtube_enabled':False};mp=root.parent/(a.part+'.json');mp.write_text(json.dumps(manifest,indent=2)+'\n')
 with api('/releases','POST',{'tag_name':f'pepe81-art-{run}-{a.part}','target_commitish':os.environ['GITHUB_SHA'],'name':f'Pepe E01 · original art {a.part} · {run}','prerelease':True,'draft':False,'body':'Original Blender renders. Production assets, NOT the final episode. No supplied reference sheets or music used. No artistic approval claimed.'}) as r:release=json.load(r)
 upload(release,target);upload(release,mp);print(release['html_url'])
if __name__=='__main__':main()
