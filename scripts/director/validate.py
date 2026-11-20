"""Full decoded-video QA, not a professional/artistic or speech-quality claim."""
import json,re,subprocess
from fractions import Fraction
from pathlib import Path
from scripts.director.project import probe,digest

def inspect(path,size,fps,expected,cues):
    path=Path(path);info=probe(path);errors=[]
    def require(condition,message):
        if not condition:errors.append(message)
    video=[s for s in info['streams'] if s['codec_type']=='video'];audio=[s for s in info['streams'] if s['codec_type']=='audio']
    require(len(video)==len(audio)==1,'Se requieren exactamente vídeo y audio')
    if not video or not audio:raise ValueError('Faltan pistas')
    v,a=video[0],audio[0];actual=float(info['format']['duration'])
    require((v['width'],v['height'])==tuple(size),'Resolución incorrecta')
    require(v['codec_name']=='h264' and v.get('pix_fmt')=='yuv420p','Formato de vídeo no compatible')
    require(Fraction(v['avg_frame_rate'])==fps,'FPS incorrectos')
    require(a['codec_name']=='aac' and int(a['sample_rate'])==48000 and a['channels']==2,'Formato de audio incorrecto')
    require(abs(actual-expected)<max(.12,2/fps),'Duración real diferente de la línea temporal')
    require(abs(float(v.get('duration',actual))-float(a.get('duration',actual)))<.15,'Audio y vídeo desincronizados')
    for i,c in enumerate(cues):
        require(0<=c['start']<c['end']<=actual+.04,'Subtítulo fuera de duración')
        if i:require(c['start']>=cues[i-1]['end']-.002,'Subtítulos solapados')
    # Decode every frame/audio packet. astats uses bounded memory even at 60 min.
    result=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-xerror','-i',str(path),'-vf','blackdetect=d=0.12:pix_th=0.02:pic_th=0.98','-af','astats=metadata=0:reset=0','-f','null','-'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,timeout=7200)
    require(result.returncode==0,'Error de decodificación completa')
    black=[{'start':float(s),'end':float(e),'seconds':float(d)} for s,e,d in re.findall(r'black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)',result.stderr)]
    require(not black,'Fotogramas negros: requieren revisión antes de aceptar el montaje')
    rms=re.findall(r'RMS level dB: (-?[\d.]+|-inf)',result.stderr);peak=re.findall(r'Peak level dB: (-?[\d.]+|-inf)',result.stderr)
    require(bool(rms) and float(rms[-1])>-45,'Audio silencioso o sin medición válida')
    require(bool(peak) and float(peak[-1])<=-.5,'Pico de audio excesivo')
    atoms=[];offset=0
    with path.open('rb') as f:
        while offset<path.stat().st_size:
            f.seek(offset);b=f.read(8)
            if len(b)!=8:break
            n=int.from_bytes(b[:4],'big');atoms.append(b[4:].decode('ascii','replace'))
            if n==1:n=int.from_bytes(f.read(8),'big')
            if n<8:break
            offset+=n
    require('moov' in atoms and 'mdat' in atoms and atoms.index('moov')<atoms.index('mdat'),'Falta faststart')
    return {'schema':1,'passed':not errors,'errors':errors,'video':path.name,'duration':actual,'expected_duration':expected,'width':v['width'],'height':v['height'],'fps':str(v['avg_frame_rate']),'sha256':digest(path),'bytes':path.stat().st_size,'full_decode':result.returncode==0,'black_intervals':black,'audio_rms_dbfs':float(rms[-1]) if rms else None,'audio_peak_dbfs':float(peak[-1]) if peak else None,'caption_count':len(cues),'timing_scope':'Measured narration and subtitle ranges, not an independent listening/alignment approval','human_artistic_approved':False,'physical_samsung_tested':False,'youtube_enabled':False}
