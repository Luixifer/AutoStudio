"""Small deterministic glints following Blender-projected paths; illustrative, not physics."""
import math
from PIL import Image,ImageDraw
COLORS={'auroras':(85,247,194),'dna':(255,197,105),'volcanoes':(255,133,48)}
def overlay(source,t,topic,paths):
    if not paths:return source
    layer=Image.new('RGBA',source.size);d=ImageDraw.Draw(layer);w,h=source.size;color=COLORS[topic]
    for j,path in enumerate(paths[:8]):
        pts=path['points']
        for k in range(4):
            u=(t*.18+k*.25+j*.13)%1;position=u*(len(pts)-1);i=min(len(pts)-2,int(position));a=position-i
            visible=path.get('visible',[True]*len(pts))
            if not visible[i] or not visible[i+1]:continue
            x=(pts[i][0]*(1-a)+pts[i+1][0]*a)*w;y=(pts[i][1]*(1-a)+pts[i+1][1]*a)*h
            if not 0<=x<w or not 0<=y<h:continue
            r=2.5+(k%2);d.ellipse((x-r*3,y-r*3,x+r*3,y+r*3),fill=(*color,25));d.ellipse((x-r,y-r,x+r,y+r),fill=(*color,165));d.ellipse((x-1,y-1,x+1,y+1),fill=(255,247,214,210))
    return Image.alpha_composite(source,layer)
