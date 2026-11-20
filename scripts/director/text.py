"""Spanish numeric expansion with measured acoustic spans, never guessed times.
Original script/caption text is preserved. Ambiguous separators fail explicitly.
"""
import re
from scripts.audio_ai_qa import normalized_words
NUM=re.compile(r'''^([¿¡(\[«"']*)([+\-−]?[0-9]+(?:[.,][0-9]+)?)(%?)([).,;:!?\]»"']*)$''')
PUNCT=set('.,;:!?¿¡—–-()[]«»"\'')

def expand_token(token):
 m=NUM.fullmatch(token)
 if not m:return token
 prefix,value,percent,suffix=m.groups();sign=''
 if value[:1] in ('-','−','+'):
  sign='menos ' if value[0]!='+' else 'más ';value=value[1:]
 if len(value)>24:raise ValueError('Cifra demasiado larga; escribe su pronunciación en el guion')
 if '.' in value and len(value.rsplit('.',1)[1])==3:
  raise ValueError('Separador numérico ambiguo; escribe la cantidad con letras para conservar su significado')
 from num2words import num2words
 parts=re.split('[.,]',value)
 integer=parts[0]
 if len(integer)>18:raise ValueError('Escribe esta cantidad con letras')
 spoken=' '.join(num2words(int(d),lang='es') for d in integer) if len(integer)>1 and integer.startswith('0') else num2words(int(integer),lang='es')
 if len(parts)==2:spoken+=' coma '+' '.join(num2words(int(d),lang='es') for d in parts[1])
 return prefix+sign+spoken+(' por ciento' if percent else '')+suffix

def expand(text):
 groups=[];pieces=[];leading=[];changed=False
 for token in text.split():
  if token and all(c in PUNCT for c in token):
   changed=True
   if groups:groups[-1]['original']+=' '+token;pieces[-1]+=token
   else:leading.append(token)
   continue
  spoken=expand_token(token);changed|=spoken!=token;original=' '.join([*leading,token]);prefix=''.join(leading);leading=[]
  groups.append({'original':original,'spoken':prefix+spoken});pieces.append(prefix+spoken)
 if leading:raise ValueError('Guion sin palabras pronunciables')
 return (' '.join(pieces) if changed else text),groups

def align(original,observed):
 """Project measured model/ASR word or phrase spans onto original script tokens.
 If one acoustic token represents several script words, keep a phrase span;
 do not invent separate word times within it.
 """
 spoken,groups=expand(original);expected=[];ranges=[]
 for group in groups:
  values=normalized_words(group['spoken']);ranges.append((len(expected),len(expected)+len(values),group['original']));expected.extend(values)
 actual=[];owners=[]
 for word in observed:
  values=normalized_words(expand_token(word['word']));actual.extend(values);owners.extend([word]*len(values))
 if expected!=actual:raise ValueError('La transcripción no coincide con el guion; revisa el audio y la pronunciación de nombres o cifras')
 result=[]
 for start,end,text in ranges:
  span=owners[start:end]
  if not span:raise ValueError('Texto sin duración acústica comprobable')
  item={'word':text,'start':min(w['start'] for w in span),'end':max(w['end'] for w in span)}
  if result and item['start']<result[-1]['end']-.002:
   result[-1]['word']+=' '+item['word'];result[-1]['end']=max(result[-1]['end'],item['end'])
  else:result.append(item)
 return result
