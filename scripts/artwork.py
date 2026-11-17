"""Original schematic animation. No image API, stock footage or generative imagery."""
from functools import lru_cache
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont, ImageOps

WIDTH, HEIGHT = 720, 1280
MARGIN = 56
SAFE_BOTTOM = 1150

@lru_cache(maxsize=12)
def font(size, bold=False):
    path = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    if not path.is_file():
        raise RuntimeError('Install fonts-dejavu-core; do not silently replace the configured typeface.')
    return ImageFont.truetype(str(path), size)

def wrap_pixels(text, face, max_width):
    lines, line = [], ''
    for word in text.split():
        if face.getlength(word) > max_width:
            raise ValueError('A single word is too wide for the layout.')
        attempt = (line + ' ' + word).strip()
        if line and face.getlength(attempt) > max_width:
            lines.append(line); line = word
        else:
            line = attempt
    if line: lines.append(line)
    return lines

@lru_cache(maxsize=1)
def background():
    gradient = Image.linear_gradient('L').resize((WIDTH, HEIGHT))
    return ImageOps.colorize(gradient, '#071728', '#142e43').convert('RGB')

def text_lines(draw, lines, xy, face, spacing, fill):
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=face, fill=fill); y += spacing
    return y

class SceneArtwork:
    def __init__(self, scene, number, count):
        self.scene, self.number, self.count = scene, number, count
        self.base = background().copy()
        d = ImageDraw.Draw(self.base)
        d.text((MARGIN, 48), f'AUTOSTUDIO  /  CIENCIA {number:02}', font=font(22, True), fill='#76e5cf')
        title = wrap_pixels(scene['title'].upper(), font(48, True), WIDTH-2*MARGIN)
        if len(title) > 3: raise ValueError('Title exceeds the three-line safe area.')
        text_lines(d, title, (MARGIN, 102), font(48, True), 59, '#f2f8fc')
        d.text((MARGIN, 287), 'ESQUEMA ANIMADO · NO ES FILMACIÓN REAL', font=font(19, True), fill='#9fb6c7')
        caption = wrap_pixels(scene['caption'], font(29), WIDTH-2*MARGIN)
        if len(caption) > 3: raise ValueError('Caption exceeds its safe area.')
        text_lines(d, caption, (MARGIN, 741), font(29), 38, '#c4dce6')
        d.rounded_rectangle((38, 865, 682, 1149), radius=22, fill='#0a1c2b', outline='#294e61', width=2)
        d.text((MARGIN, 884), 'NARRACIÓN', font=font(18, True), fill='#76e5cf')
        d.text((MARGIN, 1230), 'PRUEBA DE PRODUCCIÓN · SIN PUBLICAR', font=font(18), fill='#89a5b7')

    def frame(self, time, duration, subtitle):
        image = self.base.copy(); d = ImageDraw.Draw(image)
        cx, cy = 360, 509
        visual = self.scene['visual']
        if visual == 'ocean':
            # Stylized depth/attenuation diagram, not an underwater reconstruction.
            for x in range(90, 650, 55):
                length = 90 + int(18*math.sin(time*.7+x))
                d.line((x, 340, x+18, 340+length), fill='#32697d', width=3)
            for i in range(1, 8):
                r = 22*i + 8*math.sin(time*.6+i*.35)
                d.ellipse((cx-r,cy-r,cx+r,cy+r), outline=(20,92+i*10,135+i*9), width=3)
            for i in range(14):
                x = 100+(i*113)%510 + 8*math.sin(time*.5+i)
                y = 368+((i*47-time*12)%320)
                d.ellipse((x,y,x+5,y+5),fill='#6dbbc8')
            d.text((242, 668), 'LUZ INSUFICIENTE', font=font(21,True), fill='#a3c5d4')
        elif visual == 'vent':
            d.polygon([(85,693),(171,583),(238,640),(299,508),(346,634),(416,562),(470,657),(551,580),(637,693)],fill='#294a5c')
            d.rounded_rectangle((321,497,369,685),radius=9,fill='#785d4b',outline='#d49c69',width=3)
            d.line((343,650,343,508),fill='#ffc079',width=10)
            for i in range(14):
                age=(time*.35+i/14)%1
                x=346+math.sin(age*8+i)*26*(.35+age);y=497-age*151;r=4+age*13
                d.ellipse((x-r,y-r,x+r,y+r),outline=(int(238-age*60),int(156-age*30),100),width=3)
            d.text((190, 701), 'REACCIONES QUÍMICAS',font=font(21,True),fill='#e3b78f')
        elif visual == 'microbes':
            points=[]
            for i in range(6):
                angle=i*math.tau/6
                points.append((cx+170*math.cos(angle)+6*math.sin(time*.6+i),cy+120*math.sin(angle)))
            for i,(x,y) in enumerate(points):
                nx,ny=points[(i+1)%6];d.line((x,y,nx,ny),fill='#477f86',width=4)
                pulse=(time*.2+i/6)%1;qx=x+(nx-x)*pulse;qy=y+(ny-y)*pulse
                d.ellipse((qx-5,qy-5,qx+5,qy+5),fill='#e8dc9e')
            for i,(x,y) in enumerate(points):
                r=27+2*math.sin(time*1.2+i)
                d.ellipse((x-r,y-r,x+r,y+r),fill='#2a9a98',outline='#7fe2cb',width=3)
                d.ellipse((x-9,y-6,x+9,y+6),fill='#a0d8bc')
            d.text((173, 682), 'BASE DE UNA RED ALIMENTARIA',font=font(21,True),fill='#a2decf')
        else:
            raise ValueError('Unknown schematic; refusing a misleading fallback.')
        lines=wrap_pixels(subtitle,font(31),WIDTH-2*MARGIN)
        if len(lines)>5:raise ValueError('Subtitle exceeds the safe area.')
        text_lines(d,lines,(MARGIN,929),font(31),41,'#edf5fa')
        d.rounded_rectangle((MARGIN,1194,WIDTH-MARGIN,1201),radius=3,fill='#2c4c5d')
        progress=((self.number-1)+min(1,time/max(duration,.001)))/self.count
        d.rounded_rectangle((MARGIN,1194,MARGIN+max(1,(WIDTH-2*MARGIN)*progress),1201),radius=3,fill='#76e5cf')
        return image
