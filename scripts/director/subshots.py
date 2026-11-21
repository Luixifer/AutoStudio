"""Explicit shot ranges within ONE paragraph and ONE measured narration."""
from __future__ import annotations
import re,math

def tokens(text):return text.split()
def canonical(word):return word.strip('.,;:!?¿¡\"“”«»()[]').casefold() or word.casefold()
def locate(text,phrase,occurrence=None):
 if not isinstance(phrase,str) or not phrase.strip():raise ValueError('Falta la frase de anclaje del subplano')
 source=[canonical(w) for w in tokens(text)];query=[canonical(w) for w in tokens(phrase)]
 matches=[i for i in range(len(source)-len(query)+1) if source[i:i+len(query)]==query]
 if not matches:raise ValueError('El anclaje no aparece en el párrafo: '+phrase)
 if occurrence is None:
  if len(matches)!=1:raise ValueError('Anclaje ambiguo; amplía la frase o indica su aparición')
  return matches[0],matches[0]+len(query)
 if type(occurrence) is not int or not 1<=occurrence<=len(matches):raise ValueError('Aparición de anclaje inválida')
 i=matches[occurrence-1];return i,i+len(query)

def ranges(scene):
 shots=scene.get('subshots')
 if not isinstance(shots,list) or not 1<=len(shots)<=40:raise ValueError('Se requieren entre 1 y 40 subplanos por párrafo')
 result=[];cursor=0
 for shot in shots:
  start,_=locate(scene['narration'],shot.get('start_phrase'),shot.get('start_occurrence'))
  _,end=locate(scene['narration'],shot.get('end_phrase'),shot.get('end_occurrence'))
  if start!=cursor or end<=start:raise ValueError('Los subplanos tienen huecos, solapamientos o un orden incorrecto')
  result.append((start,end,shot));cursor=end
 if cursor!=len(tokens(scene['narration'])):raise ValueError('Los subplanos no cubren todo el párrafo')
 return result

def resolve(scene,words,fps,frames):
 text=tokens(scene['narration']);owners=[]
 for index,word in enumerate(words):owners.extend([index]*len(tokens(word['word'])))
 if ' '.join(w['word'] for w in words).split()!=text:raise ValueError('Audio y párrafo no coinciden')
 spans=ranges(scene);boundaries=[0];transitions=[]
 for index,(start,end,shot) in enumerate(spans):
  if index:
   if owners[start-1]==owners[start]:raise ValueError('El corte divide una cifra o unidad acústica; elige otra frase')
   previous=spans[index-1][2];transition=previous.get('transition',{'type':'cut','seconds':0});kind=transition.get('type','cut')
   if kind not in ('cut','dissolve'):raise ValueError('Subplanos: solo corte o disolución en pausa real')
   seconds=transition.get('seconds',0)
   if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<=seconds<=1:raise ValueError('Duración de transición inválida')
   duration=math.ceil(seconds*fps) if kind=='dissolve' else 0
   first=math.ceil(words[owners[start-1]]['end']*fps-1e-7)
   last=math.floor(words[owners[start]]['start']*fps+1e-7)-1
   if first+duration>last:raise ValueError('No hay pausa real suficiente entre los anclajes para este corte/transición; elige un final de frase')
   boundary=first+(last-first-duration)//2
   if boundary<=boundaries[-1] or boundary>=frames:raise ValueError('Subplano sin fotogramas útiles')
   boundaries.append(boundary);transitions.append(duration)
 boundaries.append(frames);transitions.append(0)
 plan=[]
 for index,(start,end,shot) in enumerate(spans):
  entry={'id':shot['id'],'start_word':start,'end_word':end,'start_frame':boundaries[index],'end_frame':boundaries[index+1],'transition_frames':transitions[index],'frames':boundaries[index+1]-boundaries[index]+transitions[index],'narration_start':words[owners[start]]['start'],'narration_end':words[owners[end-1]]['end'],'text':' '.join(text[start:end]),'media':shot['media'],'camera':shot.get('camera',scene.get('camera',{}))}
  plan.append(entry)
 return plan
