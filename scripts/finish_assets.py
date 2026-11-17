"""Reduce CPU-render grain, preserving unfiltered originals outside the Git package.
Run after the Blender generator. Spatial filtering is documented, not extra detail.
"""
import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    path=ROOT/'assets/cinematic/manifest.json';manifest=json.loads(path.read_text())
    if manifest.get('postprocess'):raise RuntimeError('Assets already filtered; regenerate originals before filtering again.')
    rawdir=ROOT/'output/original-blender-stills';rawdir.mkdir(parents=True,exist_ok=True)
    for item in manifest['assets']:
        target=ROOT/item['file'];raw=rawdir/target.name;shutil.copy2(target,raw)
        subprocess.run(['ffmpeg','-y','-v','error','-i',str(raw),'-vf','nlmeans=s=8:p=7:r=21','-frames:v','1','-q:v','2',str(target)],check=True,timeout=180)
        item['raw_sha256']=hashlib.sha256(raw.read_bytes()).hexdigest();item['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    manifest['postprocess']='FFmpeg nlmeans=s=8:p=7:r=21, JPEG q=2; spatial noise reduction, no enlargement or new image detail'
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('Filtered and verified',len(manifest['assets']),'original illustrations')
if __name__=='__main__':main()
