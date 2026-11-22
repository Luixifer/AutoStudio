"""Original procedural score and gentle foley. No music samples/downloads.
Not recorded human laughter or real animal field recordings; synthetic originals.
"""
import argparse,json,math,wave,hashlib
from pathlib import Path
import numpy as np
RATE=24000

def save(path,a):
 a=np.asarray(a,dtype=np.float32);a=np.clip(a,-.85,.85)
 with wave.open(str(path),'wb') as w:w.setnchannels(1 if a.ndim==1 else a.shape[1]);w.setsampwidth(2);w.setframerate(RATE);w.writeframes((a*32767).astype('<i2').tobytes())
def midi(n):return 440*2**((n-69)/12)
def note(n,duration,style='bell'):
 t=np.arange(round(duration*RATE))/RATE;f=midi(n);attack=np.minimum(t/.035,1);release=np.minimum((duration-t)/.12,1)
 if style=='bell':signal=np.sin(2*np.pi*f*t)+.20*np.sin(2*np.pi*f*2.01*t)+.06*np.sin(2*np.pi*f*3.98*t);env=attack*np.exp(-t*3.0)*release
 elif style=='flute':phase=2*np.pi*f*t+.02*np.sin(2*np.pi*4.2*t);signal=np.sin(phase)+.08*np.sin(2*phase);env=attack*np.exp(-t*.85)*release
 else:signal=np.sin(2*np.pi*f*t)+.13*np.sin(2*np.pi*f*2*t);env=attack*np.exp(-t*1.7)*release
 return signal*env

def score(seconds):
 a=np.zeros((round(seconds*RATE),2),np.float32);beat=.625;bar=4*beat
 chords=[(50,57,62,66),(55,59,62,67),(52,59,64,67),(45,57,61,64),(50,57,62,66),(47,59,62,66),(55,59,62,67),(45,57,61,64)]
 melody=[(74,69,66),(71,67,74),(76,71,67),(73,69,76),(74,78,76),(74,71,66),(71,74,79),(76,73,69)]
 def add(at,x,gain,pan=0):
  if at>=seconds:return
  start=round(at*RATE);end=min(len(a),start+len(x));x=x[:end-start];a[start:end,0]+=x*gain*(.8-.2*pan);a[start:end,1]+=x*gain*(.8+.2*pan)
 for b in range(math.ceil(seconds/bar)):
  chord=chords[b%8];at=b*bar;add(at,note(chord[0],2.1,'bass'),.08)
  for j,n in enumerate(chord[1:]):add(at+.08+j*.035,note(n,2.4,'flute'),.026,(j-1)*.4)
  for j,n in enumerate(melody[b%8]):add(at+(j*.85+.25)*beat,note(n if b%16<8 else n-12,1.2,'bell'),.075,(-1 if j%2 else 1)*.3)
 # Original final tonic cadence, never prolong narration to fit music.
 for j,n in enumerate((62,66,69,74)):add(max(0,seconds-3)+j*.13,note(n,2.5,'bell'),.08,j*.15)
 t=np.arange(len(a))/RATE;fade=np.minimum(t/1.2,1)*np.minimum((seconds-t)/2.5,1);a*=fade[:,None];return a

def effect(kind):
 rng=np.random.default_rng(8100+sum(map(ord,kind)))
 if kind=='stream':
  d=4.;t=np.arange(round(d*RATE))/RATE;noise=rng.normal(0,1,len(t));smooth=np.convolve(noise,np.ones(17)/17,mode='same');x=smooth*.24*(.75+.15*np.sin(2*np.pi*.7*t))
 elif kind in ('chick','rooster'):
  d=1.3 if kind=='chick' else 1.9;t=np.arange(round(d*RATE))/RATE;x=np.zeros(len(t))
  for k,at in enumerate((.06,.38,.76) if kind=='chick' else (.07,.36,.63,.97)):
   dur=.19 if kind=='chick' else (.18 if k<3 else .60);tt=np.arange(round(dur*RATE))/RATE;freq=(1450 if kind=='chick' else 540)+190*np.sin(np.pi*tt/dur)+(30*k);phase=2*np.pi*np.cumsum(freq)/RATE;s=np.sin(phase)+.12*np.sin(2*phase);env=np.sin(np.pi*tt/dur)**1.6;s*=env*.18;start=round(at*RATE);x[start:start+len(s)]+=s
 elif kind in ('steps','clap','flutter'):
  d=1.4;t=np.arange(round(d*RATE))/RATE;x=np.zeros(len(t))
  for at in ((.1,.45,.8,1.15) if kind!='flutter' else (.05,.22,.39,.56,.73,.90)):
   dur=.1 if kind!='flutter' else .055;tt=np.arange(round(dur*RATE))/RATE;n=rng.normal(0,1,len(tt));n=np.convolve(n,np.ones(9)/9,mode='same');s=n*np.sin(np.pi*tt/dur)**2*.28
   if kind=='steps':s+=.09*np.sin(2*np.pi*180*tt)*np.exp(-tt*35)*np.minimum(tt/.006,1)
   start=round(at*RATE);x[start:start+len(s)]+=s
 elif kind=='wood':
  d=1.4;t=np.arange(round(d*RATE))/RATE;x=(np.sin(2*np.pi*(180*t+10*np.sin(2*t)))+.15*np.sin(2*np.pi*290*t))*np.sin(np.pi*t/d)**2*.10
 elif kind=='wonder':
  d=2.;t=np.arange(round(d*RATE))/RATE;x=np.zeros(len(t))
  for i,n in enumerate((74,78,81,86)):
   s=note(n,1.1,'bell')*.17;start=round(i*.18*RATE);x[start:start+len(s)]+=s
 else:raise ValueError(kind)
 edge=np.minimum(t/.035,1)*np.minimum((d-t)/.08,1);return x*edge

def create(root):
 root=Path(root);p=json.loads((root/'project.json').read_text());shots=json.loads((root/'shots.json').read_text());seconds=shots['measured_total_seconds']
 media=root/'media';save(media/'pepe-original-music.wav',score(seconds+1));rights={'license':'own_creation','credit':'AutoStudio; original Python synthesis, scripts/pepe/sound.py; no original ZIP MP3 or third-party sample used'}
 for kind in ('stream','chick','rooster','steps','flutter','wood','clap','wonder'):save(media/f'sfx-{kind}.wav',effect(kind))
 # Cue positions are derived from measured word timestamps, never character estimates.
 cues={0:[('wonder',0,.10)],1:[('rooster',0,.17),('chick',1,.12)],2:[('flutter',0,.11)],3:[('stream',0,.14)],4:[('chick',0,.12),('steps',1,.16)],5:[('stream',0,.09)],6:[('steps',0,.10)],7:[('wood',0,.12),('wonder',1,.09)],8:[('wood',1,.13)],9:[('steps',0,.09),('stream',1,.08)],10:[('clap',1,.12),('wonder',1,.08)],11:[],12:[('chick',0,.07)]}
 events=[]
 for i,s in enumerate(p['chapters'][0]['scenes']):
  words=s['voice']['timed_words'];s['effects']=[]
  pair=shots['shots'][i*2:i*2+2];incoming=0 if i==0 else .30
  for kind,slot,gain in cues.get(i,[]):
   at=pair[slot]['narration_start'] # already includes paragraph incoming silence
   anchors={(1,'rooster'):'quiquiriquí',(2,'flutter'):'mariposa',(4,'steps'):'corrió',(6,'steps'):'Dio',(7,'wood'):'tabla',(8,'wood'):'colocaron',(9,'steps'):'pasito'}
   token=anchors.get((i,kind))
   if token:
    match=next((w for w in words if token.casefold() in w['word'].casefold()),None)
    if match:at=match['start']+incoming
   s['effects'].append({'path':f'media/sfx-{kind}.wav','at':round(at,6),'gain':gain,'rights':rights});events.append({'paragraph':s['id'],'shot':pair[slot]['id'],'kind':kind,'at_within_paragraph':at,'gain':gain})
 (root/'project.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
 files=[media/'pepe-original-music.wav',*sorted(media.glob('sfx-*.wav'))]
 (root/'audio-provenance.json').write_text(json.dumps({'score':'El paso de Pío; original procedural composition; warm bells, soft flute-like harmonics and gentle bass','score_seconds':seconds+1,'original_supplied_mp3_available':False,'third_party_music_used':False,'license':'own_creation','generated_files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'events':events,'synthetic_foley_not_real_animal_recordings':True,'human_listening_approved':False},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);a=p.parse_args();create(a.input)
