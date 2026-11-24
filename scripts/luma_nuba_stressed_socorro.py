"""Nuba: held stressed CO and fading -rro for a restrained cry.

Elvira es-ES. The original orthographic word remains 'socorro' in story.
Auditions use a combination of expressive spelling and pitch-preserving
time stretching in vowel regions (approximate boundaries).
"""
import asyncio, json, subprocess, tempfile, wave
from pathlib import Path
import numpy as np
import edge_tts
from scipy.signal import resample_poly

OUT=Path("out/luma-nuba-socooorrooo")
SR=24000
VOICE="es-ES-ElviraNeural"
PRESETS=[
 ("01_socooorrooo_texto","¡Socooorrooo!","-12%","+2Hz",0.50),
 ("02_socorro_co_sostenida","¡Socorro!","-10%","+4Hz",0.46),
 ("03_socorro_co_larga_final_suave","¡Socorro!","-15%","+3Hz",0.60),
]
def ffmpeg(*args):
 subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",*map(str,args)],check=True)
async def speak(text,voice,rate,pitch,dest):
 err=None
 for i in range(3):
  try:
   await edge_tts.Communicate(text,voice=voice,rate=rate,pitch=pitch).save(str(dest))
   if dest.stat().st_size<2000:raise RuntimeError("empty voice audio")
   return
  except Exception as e:
   err=e
   if i<2:await asyncio.sleep(i+2)
 raise RuntimeError(repr(err))

def decode(source,dest):
 ffmpeg("-i",source,"-f","f32le","-ar",str(SR),"-ac","1",dest)
 arr=np.fromfile(dest,dtype="<f4")
 if arr.size<SR//3:raise RuntimeError("speech missing")
 return arr

def time_stretch(pcm, factor):
 # Phaser vocoder via librosa preserves speech pitch rather than lowering it.
 import librosa
 return librosa.effects.time_stretch(pcm.astype(np.float32),rate=1.0/factor)

def edit_stress(y, middle_factor, ending_factor):
 # Find active word bounds; keep the 'so' onset and consonant transitions.
 window=int(.012*SR)
 power=np.convolve(y*y,np.ones(window)/window,mode="same")
 active=np.flatnonzero(power>max(.000006,float(power.max())*.004))
 lo=max(0,int(active[0]-.04*SR))
 hi=min(len(y),int(active[-1]+.04*SR))
 leading=y[:lo]; core=y[lo:hi];trailing=y[hi:]
 n=len(core)
 # co vowel broad region estimated from the word duration.
 a=int(n*.33);b=int(n*.63);c=int(n*.79)
 # Blend ~20ms at each boundary so the edited syllables do not click.
 parts=[core[:a],time_stretch(core[a:b],middle_factor),core[b:c],time_stretch(core[c:],ending_factor)]
 out=np.concatenate(parts)
 # Small fade on ending evokes a whispered plea fading away.
 fade=min(len(out)//3,int(.28*SR))
 out[-fade:]*=np.linspace(1,.25,fade,dtype=np.float32)
 return np.concatenate((leading,out,trailing)).astype(np.float32)

def export(samples,path,temp):
 raw=temp/(path.stem+".raw")
 np.clip(samples,-.98,.98).astype("<f4").tofile(raw)
 ffmpeg("-f","f32le","-ar",str(SR),"-ac","1","-i",raw,"-codec:a","libmp3lame","-q:a","3",path)

async def main():
 OUT.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory() as td:
  temp=Path(td); results=[]
  for i,(key,word,rate,pitch,pause) in enumerate(PRESETS):
   src=temp/f"{key}.mp3"
   await speak(word,VOICE,rate,pitch,src)
   y=decode(src,temp/f"{key}.raw")
   if i==1: y=edit_stress(y,1.48,1.28)
   if i==2: y=edit_stress(y,1.75,1.45)
   else:
    # Text variant gentle trailing fade.
    fade=min(len(y)//4,int(.24*SR));y[-fade:]*=np.linspace(1,.35,fade)
   only=OUT/f"{key}_solo.mp3";export(y,only,temp)
   question_src=temp/f"{key}_question.mp3"
   await speak("¿Hay alguien ahí?",VOICE,"-17%","-6Hz",question_src)
   q=decode(question_src,temp/f"{key}_question.raw")*.64
   line=np.concatenate((y*.78,np.zeros(round(pause*SR),dtype=np.float32),q.astype(np.float32)))
   whole=OUT/f"{key}_dialogo.mp3";export(line,whole,temp)
   results.append({"name":key,"dialogue":whole.name,"only_cry":only.name,"cry_s":round(len(y)/SR,2),"pause_s":pause,"mode":"elongated spelling" if i==0 else "pitch-preserving stretched vowel"})
   print("VOICE_OK",key,len(line)/SR,whole.stat().st_size,flush=True)
  (OUT/"manifest.json").write_text(json.dumps({"voice":VOICE,"target":"soCOOrrooo","samples":results,"disclaimer":"Approximate shaping only; not a genuine whisper/scream model."},ensure_ascii=False,indent=2))
if __name__=="__main__":asyncio.run(main())
