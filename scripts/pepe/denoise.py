"""External official OIDN CPU; preserves native dimensions and raw source PNGs."""
import argparse,json,subprocess,hashlib,tempfile,shutil,os
from pathlib import Path
import numpy as np
from PIL import Image
OIDN=Path('/workspace/autostudio-toolchain/oidn/oidn-2.3.3.x86_64.linux/bin/oidnDenoise')
def denoise(source,target,tool=OIDN):
 source=Path(source);target=Path(target);im=Image.open(source).convert('RGB');rgb=np.asarray(im,dtype=np.float32)/255;h,w=rgb.shape[:2]
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/'color.pfm';out=Path(td)/'clean.pfm'
  with p.open('wb') as f:f.write(f'PF\n{w} {h}\n-1.0\n'.encode());f.write(np.flipud(rgb).astype('<f4').tobytes())
  subprocess.run([str(tool),'--device','cpu','--ldr',str(p),'--srgb','--quality','high','--threads','4','--output',str(out)],check=True,capture_output=True)
  with out.open('rb') as f:
   assert f.readline().strip()==b'PF';dims=f.readline().strip().split();assert [int(x) for x in dims]==[w,h];scale=float(f.readline());assert scale<0;result=np.flipud(np.frombuffer(f.read(),'<f4').reshape(h,w,3))
  target.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(np.uint8(np.clip(result,0,1)*255+.5)).save(target)
 return {'raw_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'native_dimensions':[w,h],'resampled':False,'tool':'Open Image Denoise 2.3.3 CPU, high quality LDR sRGB','source_url':'https://github.com/RenderKit/oidn/releases/tag/v2.3.3','license':'Apache-2.0'}
def all_shots(root):
 root=Path(root);raw=root/'raw';raw.mkdir(exist_ok=True);records=[]
 for n in range(1,27):
  image=root/'media'/f'shot-{n:02}.png';original=raw/image.name
  if not original.exists():shutil.copy2(image,original)
  record=denoise(original,image);records.append({'shot':n,**record});print('DENOISED',n,flush=True)
 (root/'denoise.json').write_text(json.dumps(records,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--all',type=Path);p.add_argument('--source',type=Path);p.add_argument('--target',type=Path);a=p.parse_args()
 if a.all:all_shots(a.all)
 else:print(json.dumps(denoise(a.source,a.target),indent=2))
