"""Fetch official research pages; access is not a licence or fact approval."""
import hashlib,json,re,urllib.request,urllib.parse
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.skip=0;self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'):self.skip+=1
  if tag=='a':self.links.extend(v for k,v in attrs if k=='href')
 def handle_endtag(self,tag):
  if tag in ('script','style'):self.skip=max(0,self.skip-1)
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
def collect(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);items=[]
 urls=['https://www.hessdalen.org/','https://www.hessdalen.org/reports/hpreport84.shtml','https://www.hessdalen.org/station/','https://www.hessdalen.org/reports/']
 for url in urls:
  item={'url':url,'checked_utc':datetime.now(timezone.utc).isoformat(),'rights':'NOT ESTABLISHED; reference access does not permit footage reuse','facts_approved':False}
  try:
   request=urllib.request.Request(url,headers={'User-Agent':'AutoStudio-research/1.0'})
   with urllib.request.urlopen(request,timeout=35) as response:raw=response.read(2_000_001);item.update(status=response.status,final_url=response.url)
   if len(raw)>2_000_000:raise ValueError('Page too large')
   parser=Text();parser.feed(raw.decode('utf-8',errors='replace'));text=' '.join(' '.join(parser.parts).split());item['sha256']=hashlib.sha256(raw).hexdigest()
   # Short contextual excerpts only, never a copied paper or image collection.
   item['year_excerpts']=[text[max(0,m.start()-120):m.end()+180] for m in list(re.finditer(r'\b(?:1981|1984|1998)\b',text))[:6]]
   item['research_links']=[urllib.parse.urljoin(url,l) for l in parser.links if any(w in l.lower() for w in ('report','histor','station','1984','1998'))][:30]
  except Exception as e:item['error']=str(e)[:250]
  items.append(item)
 (out/'official-source-access.json').write_text(json.dumps({'pages':items,'human_fact_review':'pending','licensing':'pending'},ensure_ascii=False,indent=2)+'\n')
 # Read ALL public comments. No private drafts, assets or user credentials logged.
 from scripts.director.cloud import get_json
 comments=[]
 for page in range(1,11):
  batch=get_json('/issues/80/comments?per_page=100&page='+str(page));comments.extend({'url':c['html_url'],'body':c['body']} for c in batch)
  if len(batch)<100:break
 (out/'issue80-public-comments.json').write_text(json.dumps(comments,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':collect('reports/director')
