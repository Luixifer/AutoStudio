"""Explicit technical fixture. NOT Hessdalen footage or a finished documentary."""
import argparse,json,shutil,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
from scripts.director.project import SCHEMA
ROOT=Path(__file__).resolve().parents[2]

def create(out,format='horizontal'):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 for i in (1,2):shutil.copy2(ROOT/f'assets/science_v04/auroras/auroras_0{i}.jpg',out/f'image{i}.jpg')
 subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=640x360:rate=24:duration=3','-c:v','libx264','-pix_fmt','yuv420p',str(out/'clip.mp4')],check=True)
 overlay=Image.new('RGBA',(864,1536),(0,0,0,0));d=ImageDraw.Draw(overlay);d.ellipse((280,400,480,600),fill=(255,200,20,90));overlay.save(out/'layer.png')
 from scripts.soundscape import write_ambience
 write_ambience(out/'music.wav',40,[])
 own={'license':'own_creation','credit':'AutoStudio; material de ensayo, no grabación de Hessdalen'}
 def media(path,kind='image'):return {'path':path,'kind':kind,'rights':own,'fit':'contain'}
 first=media('image1.jpg');first['layers']=[{'path':'layer.png','rights':own,'from':[-.01,0],'to':[.01,0]}]
 scenes=[{'id':'prueba-imagen','narration':'Esta es una prueba técnica del montaje. La ilustración permite comprobar el movimiento de cámara y las capas transparentes.','media':first,'transition':{'type':'dissolve','seconds':.4},'camera':{'keyframes':[{'at':0,'zoom':1,'x':.4,'y':.5},{'at':1,'zoom':1.1,'x':.6,'y':.5}]}},
 {'id':'prueba-clip','narration':'El siguiente fragmento es un patrón de prueba de vídeo. No es una grabación científica ni una escena de Hessdalen.','media':{**media('clip.mp4','video'),'loop':True},'transition':{'type':'dissolve','seconds':.4}},
 {'id':'prueba-audio','narration':'La narración determina cuánto dura cada escena. El resultado necesita una revisión humana antes de considerarlo un documental terminado.','media':media('image2.jpg')}]
 p={'schema':SCHEMA,'title':'ENSAYO TÉCNICO — NO ES HESSDALEN','youtube_enabled':False,'format':format,'fps':30,'voice':{'mode':'kokoro','voice':'em_alex'},'music':{'path':'music.wav','rights':own,'gain':.1},'chapters':[{'id':'ensayo','scenes':scenes}]}
 media_dir=out/'media';media_dir.mkdir(exist_ok=True)
 def relocate(obj):
  if isinstance(obj,dict):
   if 'path' in obj:
    src=out/obj['path'];dest=media_dir/src.name
    if src.is_file():src.replace(dest)
    obj['path']='media/'+src.name
   for v in obj.values():relocate(v)
  elif isinstance(obj,list):
   for v in obj:relocate(v)
 relocate(p)
 (out/'project.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n');return out/'project.json'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--format',default='horizontal',choices=['horizontal','vertical']);a=p.parse_args();print(create(a.out,a.format))
