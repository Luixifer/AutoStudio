"""Readable cues from measured acoustic words, bounded to one scene."""
import re

def phrases(words,style='documentary'):
 if not words:raise ValueError('Escena sin tiempos acústicos')
 limit=5 if style=='dynamic' else 13 if style=='cinematic' else 11
 chunks=[];current=[]
 for word in words:
  current.append(word);text=' '.join(w['word'] for w in current)
  sentence=bool(re.search(r'[.!?][”»\"]?$',word['word']))
  pause=len(current)>=5 and word['word'].endswith((',',':',';'))
  if sentence or pause or len(current)>=limit or len(text)>82:chunks.append(current);current=[]
 if current:chunks.append(current)
 # Avoid an isolated tail unless it is a complete short sentence.
 if len(chunks)>1 and len(chunks[-1])<3 and len(' '.join(w['word'] for w in chunks[-2]+chunks[-1]))<=100:
  chunks[-2].extend(chunks.pop())
 return [{'start':part[0]['start'],'end':part[-1]['end'],'text':' '.join(w['word'] for w in part)} for part in chunks]
