"""Fetch short, traceable evidence passages from a small NASA page allowlist.

No whole-article republication, no scientific verification, no video generation.
Do not follow non-NASA redirects or trust unlisted hosts.
"""
from html.parser import HTMLParser
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from scripts.external_sources import NASA_BLACK_HOLE_PAGES, AGENT
from scripts.source_quality import black_hole_question

MAX_HTML = 1_200_000
MAX_PASSAGES = 5
KNOWN_URLS = frozenset(url for _,url in NASA_BLACK_HOLE_PAGES)
TARGET = ("event horizon", "inside", "interior", "singularity",
          "point of no return", "fall into", "falling into",
          "tidal", "spaghettification", "space-time")
NOISE = ("cookie", "subscribe", "newsletter", "privacy policy",
         "share this", "read more", "javascript")

class MainText(HTMLParser):
    """Extract prose from <main> and prefer paragraphs; skip scripts/nav."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.main_depth = 0
        self.depth = 0
        self.blocked = 0
        self.paragraph = 0
        self.current = []
        self.paragraphs = []
    def handle_starttag(self,tag,attrs):
        if tag=="main":
            self.main_depth+=1
        if tag in ("script","style","nav","footer","header","noscript","svg","form"):
            self.blocked+=1
        if tag in ("p","li") and self.main_depth and not self.blocked:
            self.paragraph+=1
            if self.paragraph==1:
                self.current=[]
    def handle_endtag(self,tag):
        if tag in ("p","li") and self.paragraph:
            self.paragraph-=1
            if self.paragraph==0:
                text=" ".join(" ".join(self.current).split())
                if text:
                    self.paragraphs.append(text)
                self.current=[]
        if tag in ("script","style","nav","footer","header","noscript","svg","form"):
            self.blocked=max(0,self.blocked-1)
        if tag=="main":
            self.main_depth=max(0,self.main_depth-1)
    def handle_data(self,data):
        if self.main_depth and self.paragraph and not self.blocked:
            self.current.append(data)


def evidence_from_page(url, html, max_passages=MAX_PASSAGES):
    if url not in KNOWN_URLS:
        raise ValueError("Página NASA no incluida en la lista autorizada.")
    if not isinstance(html, str):
        raise ValueError("HTML inválido.")
    parser=MainText()
    parser.feed(html)
    found=[]
    for paragraph in parser.paragraphs:
        normalized=paragraph.casefold()
        if not 65 <= len(paragraph) <= 1600:
            continue
        if not any(cue in normalized for cue in TARGET):
            continue
        if any(noise in normalized[:80] for noise in NOISE):
            continue
        if ("black hole" not in normalized and
                not any(cue in normalized for cue in ("event horizon","singularity"))):
            continue
        # Short verbatim *review excerpt*, not narrated script.
        fragment=paragraph[:240].rsplit(" ",1)[0]
        if fragment and fragment not in found:
            found.append(fragment)
        if len(found)>=max_passages:
            break
    return found


def fetch_nasa_evidence(topic, opener=urlopen):
    if not black_hole_question(topic):
        return {"status":"unsupported_topic", "passages":[], "errors":[]}
    passages=[]
    errors=[]
    for title,url in NASA_BLACK_HOLE_PAGES:
        if url not in KNOWN_URLS:
            continue
        request=Request(url,headers={
            "User-Agent":AGENT, "Accept":"text/html",
        })
        try:
            with opener(request,timeout=15) as response:
                final_url=response.geturl()
                target=urlsplit(final_url)
                if target.scheme!="https" or target.hostname not in ("science.nasa.gov",):
                    raise ValueError("Redirección fuera del dominio NASA.")
                media=response.headers.get("Content-Type","")
                if "text/html" not in media:
                    raise ValueError("La respuesta no es HTML.")
                raw=response.read(MAX_HTML+1)
                if len(raw)>MAX_HTML:
                    raise ValueError("Respuesta NASA demasiado grande.")
                html=raw.decode("utf-8","replace")
            selected=evidence_from_page(url,html)
            for excerpt in selected:
                passages.append({
                    "source_title":title,"source_url":url,"excerpt_original_en":excerpt,
                    "content_fetched":True,
                    "factual_verification":"pending_editorial_review",
                    "ready_for_narration":False,
                })
        except (HTTPError,URLError,TimeoutError,OSError,ValueError) as error:
            errors.append({"url":url,"type":type(error).__name__})
    return {"status":"evidence_passages_unverified" if passages else "no_passages",
            "passages":passages[:10],"errors":errors,
            "note":"Fragmentos de evidencia textual oficiales sin revisión; no son un guion, ni traducciones ni autorizaciones para publicar."}
