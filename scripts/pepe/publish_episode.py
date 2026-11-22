"""Deliver only the complete, independently verified story to GitHub Releases."""
import argparse,json,os,shutil,tempfile,subprocess,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scripts.director.cloud import api,upload
from scripts.director.project import digest

def contact_from_movie(render,target):
 render=Path(render);t=json.loads((render/'timeline.json').read_text());slots=[(scene,slot) for scene in t['scenes'] for slot in scene['subshots']];indices=[round((s['start']+(v['narration_start']+v['narration_end'])/2)*30) for s,v in slots];expression='+'.join(f'eq(n\\,{i})' for i in indices)
 raw=subprocess.run(['ffmpeg','-v','error','-nostdin','-i',str(render/'documental-REVISION.mp4'),'-vf',f'select={expression},scale=320:180','-fps_mode','passthrough','-pix_fmt','rgb24','-f','rawvideo','pipe:1'],capture_output=True,check=True,timeout=900).stdout
 if len(raw)!=26*320*180*3:raise ValueError('Could not decode all 26 actual movie shots')
 frames=np.frombuffer(raw,np.uint8).reshape(26,180,320,3);sheet=Image.new('RGB',(1600,6*205),(245,242,222));d=ImageDraw.Draw(sheet)
 for n,a in enumerate(frames):x=n%5*320;y=n//5*205;sheet.paste(Image.fromarray(a),(x,y+23));d.text((x+6,y+4),f'P{n+1:02} · MP4 real · {indices[n]/30:.2f} s',fill=(30,62,56))
 sheet.save(target)

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--render',type=Path,required=True);p.add_argument('--archive',type=Path,required=True);a=p.parse_args()
 if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='Luixifer/AutoStudio':raise RuntimeError('Only genuine authorized Actions')
 qa=json.loads((a.render/'episode-quality.json').read_text());movie=a.render/'documental-REVISION.mp4'
 if not qa['passed'] or qa['actual_mp4_sha256']!=digest(movie) or qa['active_subshots']!=26 or qa['paragraphs']!=13:raise ValueError('Not a verified complete episode')
 run=os.environ['GITHUB_RUN_ID'];attempt=os.environ.get('GITHUB_RUN_ATTEMPT','1');tag=f'pepe-e01-{run}-r{attempt}'
 with tempfile.TemporaryDirectory() as td:
  stage=Path(td);delivery=[]
  for source,name in ((movie,'Pepe-El-gran-rescate-de-Pio-v001.mp4'),(a.archive,'Pepe-E01-Proyecto-editable-v001.zip'),(a.render/'episode-quality.json','Pepe-E01-Calidad.json'),(a.render/'captions.srt','Pepe-E01-Subtitulos.srt'),(a.render/'timeline.json','Pepe-E01-Linea-de-tiempo.json'),(a.render/'correspondence.json','Pepe-E01-Correspondencia.json')):
   dest=stage/name;shutil.copy2(source,dest);delivery.append(dest)
  contact=stage/'Pepe-E01-26-planos-del-video.jpg';contact_from_movie(a.render,contact);delivery.append(contact)
  ledger={'run_id':run,'attempt':attempt,'source_commit':os.environ['GITHUB_SHA'],'complete_story':True,'duration':qa['duration_seconds'],'paid_services_used':False,'youtube_published':False,'physical_samsung_tested':False,'artistic_approved':False,'files':{f.name:{'sha256':digest(f),'bytes':f.stat().st_size} for f in delivery}}
  mf=stage/'Pepe-E01-Entrega.json';mf.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');delivery.append(mf);sums=stage/'SHA256SUMS';sums.write_text(''.join(digest(f)+'  '+f.name+'\n' for f in delivery));delivery.append(sums)
  body=f'Episodio completo: El gran rescate de Pío. {qa["duration_seconds"]:.3f} s, 1920×1080, 30 fps, H.264/AAC. Trece párrafos originales y 26 planos originales. Un cruce 3D animado; el resto son ilustraciones 3D con movimientos suaves de cámara. Narración neuronal Dora; revisión auditiva humana y aprobación artística pendientes. No prueba física Samsung ni ensayo con niños. No es el demo técnico. Sin APIs de pago ni publicación en YouTube. Fuente: {os.environ["GITHUB_SHA"]}.'
  with api('/releases','POST',{'tag_name':tag,'target_commitish':os.environ['GITHUB_SHA'],'name':'Pepe el Gallo Travieso · El gran rescate de Pío · v001','prerelease':True,'draft':False,'body':body}) as response:release=json.load(response)
  for f in delivery:upload(release,f)
  print('COMPLETE_EPISODE_RELEASE',release['html_url'])
if __name__=='__main__':main()
