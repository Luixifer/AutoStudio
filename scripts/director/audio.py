"""Bounded PCM decoding for real long-form narration; no legacy 180 s QA cap."""
from pathlib import Path
import subprocess
import numpy as np
from scripts.director.project import probe

def pcm(path,max_seconds=3600):
 seconds=float(probe(path)['format']['duration'])
 if not .1<=seconds<=max_seconds+.1:raise ValueError('Duración de audio fuera del límite de esta operación')
 data=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(path),'-vn','-ac','1','-ar','16000','-f','f32le','pipe:1'],timeout=1800)
 if len(data)>round((max_seconds+.2)*16000)*4:raise ValueError('PCM excede la duración declarada')
 samples=np.frombuffer(data,np.float32)
 if not len(samples) or not np.all(np.isfinite(samples)):raise ValueError('PCM vacío o inválido')
 return samples
