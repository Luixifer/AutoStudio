"""Full-frame original 3D illustrations with camera motion and word-timed captions.
No paragraph panel. Images are never labelled as real underwater footage.
"""
from pathlib import Path
import hashlib,json,math,random
from PIL import Image,ImageDraw,ImageEnhance,ImageFilter
from .artwork import font,wrap_pixels,WIDTH,HEIGHT
ROOT=Path(__file__).resolve().parents[1]

def verify_assets(manifest_path=None):
    path=(ROOT/(manifest_path or 'assets/cinematic/manifest.json')).resolve()
    if not path.is_relative_to((ROOT/'assets').resolve()):raise ValueError('Asset manifest escapes the library.')
    manifest=json.loads(path.read_text());found={}
    for asset in manifest['assets']:
        path=(ROOT/asset['file']).resolve()
        if not path.is_relative_to((ROOT/'assets').resolve()):raise ValueError('Resource escapes the asset library.')
        if asset['id'] in found:raise ValueError('Duplicate asset ID in manifest.')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=asset['sha256']:raise ValueError('Original illustration missing or changed: '+asset['id'])
        with Image.open(path) as im:
            if im.size!=(864,1536):raise ValueError('Unexpected source resolution.')
        found[asset['id']]=asset
    return found

def caption_layout(words,face=None):
    face=face or font(46,True);rows=[];row=[];width=0;space=face.getlength(' ')
    for i,word in enumerate(words):
        w=face.getlength(word['word'])
        if w>620:raise ValueError('A subtitle word exceeds the frame.')
        if row and width+space+w>620:rows.append(row);row=[];width=0
        row.append((i,word['word'],w));width+=w+(space if len(row)>1 else 0)
    if row:rows.append(row)
    if len(rows)>2:raise ValueError('Dynamic caption exceeds two safe lines.')
    return rows

class CinematicArtwork:
    def __init__(self,scene,number,count,assets=None):
        self.scene,self.number,self.count=scene,number,count;assets=assets or verify_assets()
        if scene.get('camera') not in {'push','pull','pan_left','pan_right','drift'}:raise ValueError('Unknown camera motion.')
        if scene.get('asset') not in assets:raise ValueError('Unknown cinematic asset.')
        self.asset=assets[scene['asset']]
        path=ROOT/self.asset['file']
        with Image.open(path) as im:self.source=im.convert('RGB')
        self.source=ImageEnhance.Color(self.source).enhance(1.07)
        self.source=ImageEnhance.Contrast(self.source).enhance(1.04)
        self.science_source=self.source.convert('RGBA') if scene.get('visual')=='science' else None
        self.face=font(46,True);self.small=font(17,True)
        self.shade=Image.new('RGBA',(WIDTH,HEIGHT));d=ImageDraw.Draw(self.shade)
        for y in range(HEIGHT):
            # Local soft support, not a rectangle or paragraph panel.
            alpha=int(130*max(0,(y-770)/(HEIGHT-770))**.6)
            if y<200:alpha=max(alpha,int(50*(1-y/200)))
            d.line((0,y,WIDTH,y),fill=(0,5,12,alpha))
        r=random.Random(210+number);self.particles=[(r.random(),r.random(),r.uniform(.5,2.0),r.uniform(.004,.015)) for _ in range(28)]
    def visual(self,t,duration):
        u=max(0,min(1,t/max(.1,duration)));ease=u*u*(3-2*u);mode=self.scene.get('camera','push')
        zoom=1.01+.10*ease if mode=='push' else 1.11-.10*ease if mode=='pull' else 1.08
        px=.5;py=.5
        if mode=='pan_left':px=.85-.70*ease
        if mode=='pan_right':px=.15+.70*ease
        if mode=='drift':px=.25+.5*ease;py=.35+.3*ease
        sw,sh=self.source.size;cw=sw/zoom;ch=sh/zoom;left=(sw-cw)*px;top=(sh-ch)*py
        source=self.source
        if self.science_source is not None:
            from .science_motion import overlay
            source=overlay(self.science_source,t,self.scene['animation']['topic'],self.asset.get('motion_paths',[]))
        image=source.transform((WIDTH,HEIGHT),Image.Transform.AFFINE,(cw/WIDTH,0,left,0,ch/HEIGHT,top),resample=Image.Resampling.BICUBIC).convert('RGBA')
        p=Image.new('RGBA',(WIDTH,HEIGHT));d=ImageDraw.Draw(p)
        for x,y,r,speed in self.particles:
            xx=(x+.012*math.sin(t*.23+y*8))*WIDTH;yy=((y-t*speed)%1)*HEIGHT;alpha=45 if r<1 else 65
            d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=(167,218,226,alpha))
        image=Image.alpha_composite(image,p)
        return image.convert('RGB')
    def frame(self,t,duration,caption,previous_visual=None):
        base=self.visual(t,duration)
        if previous_visual is not None and t<.18:base=Image.blend(previous_visual,base,min(1,t/.18))
        image=Image.alpha_composite(base.convert('RGBA'),self.shade);d=ImageDraw.Draw(image)
        d.text((44,48),'AUTOSTUDIO',font=self.small,fill=(214,236,241,210),stroke_width=1,stroke_fill=(0,0,0,100))
        label='ILUSTRACIÓN 3D' if self.scene.get('visual')!='science' else 'ILUSTRACIÓN · NO A ESCALA';d.text((WIDTH-44-self.small.getlength(label),48),label,font=self.small,fill=(214,236,241,205),stroke_width=1,stroke_fill=(0,0,0,100))
        headline=self.scene.get('headline')
        if headline and t<min(2.2,duration):
            face=font(54,True);lines=wrap_pixels(headline,face,620)
            if len(lines)>3:raise ValueError('Headline exceeds safe area.')
            yy=178
            for line in lines:
                x=(WIDTH-face.getlength(line))/2;d.text((x,yy),line,font=face,fill='#f3f6ef',stroke_width=3,stroke_fill=(0,9,16,210));yy+=64
        if caption:
            rows=caption_layout(caption['words'],self.face);y=1028 if len(rows)==1 else 991;space=self.face.getlength(' ')
            for row in rows:
                width=sum(w for _,_,w in row)+space*(len(row)-1);x=(WIDTH-width)/2
                for index,word,w in row:
                    fill='#ffd28c' if index==caption.get('active') else '#f8f7f1'
                    d.text((x,y),word,font=self.face,fill=fill,stroke_width=4,stroke_fill=(0,6,13,235));x+=w+space
                y+=58
        progress=((self.number-1)+min(1,t/max(duration,.01)))/self.count
        d.line((44,1197,676,1197),fill=(207,222,230,55),width=2);d.line((44,1197,44+632*progress,1197),fill=(142,216,211,160),width=3)
        return image.convert('RGB')
