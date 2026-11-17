"""Verify the real MP4 container, full decode and decoded audio; no simulated success."""
import argparse, array, hashlib, json, math, subprocess
from fractions import Fraction
from pathlib import Path


def inspect_video(path: Path):
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError('Missing or empty MP4.')
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],text=True))
    video=[s for s in info['streams'] if s['codec_type']=='video'];audio=[s for s in info['streams'] if s['codec_type']=='audio'];errors=[]
    def require(ok,message):
        if not ok:errors.append(message)
    require(len(video)==1 and len(audio)==1,'Expected one video and one audio stream.')
    if not video or not audio:raise ValueError('; '.join(errors))
    v,a=video[0],audio[0];duration=float(info['format']['duration'])
    require(v['codec_name']=='h264' and v.get('pix_fmt')=='yuv420p','Require H.264 / yuv420p.')
    require((v['width'],v['height'])==(720,1280),'Require actual 720×1280 portrait frames.')
    require(Fraction(v['avg_frame_rate'])==25,'Require 25 fps output.')
    require(a['codec_name']=='aac' and int(a['sample_rate'])==48000 and a['channels']==2,'Require AAC stereo at 48 kHz.')
    require(3<duration<180,'Duration outside the MVP Short budget.')
    require(path.stat().st_size<20*1024*1024,'Preview exceeds the 20 MiB download budget.')
    if 'duration' in a and 'duration' in v:require(abs(float(a['duration'])-float(v['duration']))<.35,'Audio/video durations diverge.')
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=240)
    pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-ac','1','-ar','16000','-f','s16le','-'],timeout=180)
    samples=array.array('h');samples.frombytes(pcm)
    if not samples:raise ValueError('Audio decoded to zero samples.')
    rms=math.sqrt(sum(x*x for x in samples)/len(samples));dbfs=20*math.log10(max(rms,1e-12)/32768);peak=max(abs(x) for x in samples)/32768
    active=0;windows=0
    for start in range(0,len(samples),1600):
        values=samples[start:start+1600]
        if not values:continue
        windows+=1;active+=math.sqrt(sum(x*x for x in values)/len(values))>32768*10**(-40/20)
    clipped=sum(abs(x)>=32760 for x in samples)/len(samples)
    require(dbfs>-40,'Decoded narration is silent or too quiet.');require(active/windows>.30,'Insufficient active audio windows.');require(clipped<.001,'Excessive full-scale clipping.')
    atoms=[];offset=0
    with path.open('rb') as f:
        while offset<path.stat().st_size:
            f.seek(offset);head=f.read(8)
            if len(head)<8:break
            size=int.from_bytes(head[:4],'big');name=head[4:].decode('ascii',errors='replace')
            if size==1:size=int.from_bytes(f.read(8),'big')
            if size==0:size=path.stat().st_size-offset
            if size<8:break
            atoms.append(name);offset+=size
    require('moov' in atoms and 'mdat' in atoms and atoms.index('moov')<atoms.index('mdat'),'MP4 is not fast-start optimized.')
    return {'passed':not errors,'errors':errors,'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'duration_seconds':duration,'video':{'codec':v['codec_name'],'width':v['width'],'height':v['height'],'pixel_format':v['pix_fmt'],'fps':str(v['avg_frame_rate']),'frames':v.get('nb_frames')},'audio':{'codec':a['codec_name'],'channels':a['channels'],'sample_rate':int(a['sample_rate']),'decoded_rms_dbfs':round(dbfs,2),'decoded_peak_dbfs':round(20*math.log10(max(peak,1e-12)),2),'active_100ms_windows_fraction':round(active/windows,4),'full_scale_samples_fraction':clipped,'scope':'Signal and decodability only; not speech recognition or an editorial quality approval.'},'full_decode':'passed','fast_start':True,'physical_samsung_tested':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('video',type=Path);p.add_argument('--report',type=Path);a=p.parse_args();report=inspect_video(a.video)
    if a.report:a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(0 if report['passed'] else 1)
