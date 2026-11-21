"""Bounded sentence inference inside ONE scene. Image and scene ID never change.
Long Kokoro batches can omit boundary whitespace in their timing tokens; separate
sentence inference retains explicit acoustic word boundaries without guessed times.
"""
from pathlib import Path
import re,wave

def chunks(text,limit=40):
 result=[]
 for sentence in re.split(r'(?<=[.!?;:])\s+',text.strip()):
  words=sentence.split()
  for index in range(0,len(words),limit):result.append(' '.join(words[index:index+limit]))
 if ' '.join(result).split()!=text.split():raise ValueError('La segmentación de voz alteró el texto')
 return result

def synthesize(narrator,text,target):
 from scripts.director.engine import join_wavs,pcm_seconds
 folder=Path(target).parent/'speech-parts';folder.mkdir(exist_ok=True);parts=[];words=[];offset=0;metadata=None
 def segment(piece):
  nonlocal offset,metadata
  path=folder/f'{len(parts):04}.wav'
  try:info=narrator.synthesize(piece,path)
  except ValueError:
   tokens=piece.split()
   if len(tokens)<2:raise
   mid=len(tokens)//2;segment(' '.join(tokens[:mid]));segment(' '.join(tokens[mid:]));return
  metadata=info;parts.append(path)
  words.extend({**w,'start':w['start']+offset,'end':w['end']+offset} for w in info['words']);offset+=pcm_seconds(path)
 for piece in chunks(text):segment(piece)
 join_wavs(parts,target)
 return {**metadata,'words':words,'inference_fragments':len(parts),'timing_method':'same-model acoustic boundaries per sentence; joined using exact PCM frame counts; one paragraph remains one visual scene'}
