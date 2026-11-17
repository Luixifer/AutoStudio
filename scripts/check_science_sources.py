"""Retrieve scientific source pages, report actual HTTP/text evidence, no paid API."""
import hashlib,json,os,re,subprocess,urllib.request,urllib.error
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
class Text(HTMLParser):
    def __init__(self):super().__init__();self.skip=0;self.parts=[];self.intitle=False;self.title=[]
    def handle_starttag(self,t,a):
        if t in ['script','style']:self.skip+=1
        if t=='title':self.intitle=True
    def handle_endtag(self,t):
        if t in ['script','style']:self.skip=max(0,self.skip-1)
        if t=='title':self.intitle=False
    def handle_data(self,s):
        if self.intitle:self.title.append(s)
        if not self.skip and s.strip():self.parts.append(s.strip())
def main():
    requests=json.loads((ROOT/'research/source-requests.json').read_text());report={'schema':1,'managed_by':'autostudio-science-sources','github_run_id':os.environ.get('GITHUB_RUN_ID'),'topics':{}}
    for topic,data in requests.items():
        pages=[]
        for source in data['sources']:
            item=dict(source)
            try:
                req=urllib.request.Request(source['url'],headers={'User-Agent':'AutoStudio-Educational-Review/0.4 (source verification; no media scraping)','Accept':'text/html'})
                with urllib.request.urlopen(req,timeout=35) as r:body=r.read(5*1024*1024);item.update(status=r.status,final_url=r.url,sha256=hashlib.sha256(body).hexdigest())
                p=Text();p.feed(body.decode('utf-8',errors='replace'));text=' '.join(p.parts);item['title']=' '.join(p.title);terms={'auroras':['aurora','oxygen','nitrogen','solar wind'],'dna':['DNA','bases','protein','expression'],'volcanoes':['magma','lava','mantle','gas','pressure']}[topic]
                snippets=[]
                for term in terms:
                    m=re.search(r'\b'+re.escape(term)+r'\b',text,re.I)
                    if m:snippets.append({'term':term,'excerpt':text[max(0,m.start()-120):m.start()+900]})
                item['excerpts']=snippets;item['retrieved']=item['status']==200 and len(text)>1000 and bool(snippets)
            except Exception as e:item.update(retrieved=False,error=type(e).__name__+': '+str(e))
            pages.append(item)
        report['topics'][topic]={'pages':pages,'at_least_one_source_retrieved':any(p['retrieved'] for p in pages)}
    report['passed']=all(t['at_least_one_source_retrieved'] for t in report['topics'].values());out=ROOT/'reports/science-source-report.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if os.environ.get('GITHUB_ACTIONS')=='true':
        payload=out.read_bytes();subprocess.run(['git','fetch','--no-tags','origin'],check=True)
        found=subprocess.check_output(['git','ls-remote','--heads','origin','refs/heads/science-sources'],text=True).strip()
        if found:
            subprocess.run(['git','fetch','origin','refs/heads/science-sources'],check=True);old=json.loads(subprocess.check_output(['git','show','FETCH_HEAD:report.json'],text=True));assert old.get('managed_by')==report['managed_by'];subprocess.run(['git','switch','-c','source-review','FETCH_HEAD'],check=True)
        else:subprocess.run(['git','switch','--orphan','source-review'],check=True)
        (ROOT/'report.json').write_bytes(payload);subprocess.run(['git','config','user.name','AutoStudio Sources'],check=True);subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],check=True);subprocess.run(['git','add','--','report.json'],check=True);subprocess.run(['git','commit','-m','Record actual scientific source retrieval'],check=True);subprocess.run(['git','push','origin','HEAD:refs/heads/science-sources'],check=True)
    print('SOURCE_RETRIEVAL_PASSED',report['passed']);raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
