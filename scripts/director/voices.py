"""Original listening samples. Generation never establishes voice approval."""
import argparse,json,subprocess
from pathlib import Path
from scripts.neural_narration import NeuralNarrator

def audition(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 text='Esta es una muestra de narración documental. Escucha el ritmo, las pausas y la pronunciación antes de elegir una voz para tu proyecto.'
 reports=[]
 for name in ('em_alex','em_santa'):
  wav=out/(name+'.wav');info=NeuralNarrator(voice=name).synthesize(text,wav)
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-af','loudnorm=I=-16:TP=-1.5:LRA=9','-c:a','libmp3lame','-b:a','128k',str(out/(name+'.mp3'))],check=True)
  reports.append(info)
 (out/'voices.json').write_text(json.dumps({'voices':reports,'human_listening_approved':False,'paid_api':False},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();audition(a.out)
