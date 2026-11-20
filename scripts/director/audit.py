"""Actual input metadata and source-quality warnings, never invented detail."""
from fractions import Fraction
from pathlib import Path
from PIL import Image,ImageOps
from scripts.director.project import load,probe,FORMATS,digest

def audit(project_path):
 path=Path(project_path);p=load(path);size=FORMATS[p['format']];report={'schema':1,'title':p['title'],'output_size':list(size),'scenes':[],'warnings':[],'human_quality_approved':False}
 for chapter in p['chapters']:
  for scene in chapter['scenes']:
   m=scene['media'];file=path.parent/m['path'];item={'id':scene['id'],'kind':m['kind'],'path':m['path'],'sha256':digest(file),'rights':m['rights'],'warnings':[]}
   if m['kind']=='image':
    with Image.open(file) as image:
     if image.width*image.height>40_000_000:raise ValueError('Imagen superior a 40 megapíxeles: prepara una copia optimizada')
     dims=image.size
     im=ImageOps.exif_transpose(image);w,h=im.size;item.update({'actual_format':image.format,'width':w,'height':h})
    ratio=max(size[0]/w,size[1]/h) if m.get('fit')=='cover' else min(size[0]/w,size[1]/h)
    zoom=max([k.get('zoom',1.05) for k in scene.get('camera',{}).get('keyframes',[])]+[1.08])
    item['effective_upscale']=round(ratio*zoom,3)
    if ratio*zoom>1.25:item['warnings'].append('Ampliación superior a 1,25×: no se inventa detalle; revisa nitidez')
    for layer in m.get('layers',[]):
     with Image.open(path.parent/layer['path']) as im:
      if im.size!=dims:raise ValueError('Las capas parallax deben compartir el lienzo y anclajes de la imagen base')
      if 'A' not in im.getbands() or im.getextrema()[-1][0]==255:raise ValueError('Capa parallax sin alpha real')
   else:
    details=probe(file);v=next((s for s in details['streams'] if s['codec_type']=='video'),None)
    if not v:raise ValueError('El MP4 no contiene vídeo')
    item.update({key:v.get(key) for key in ['codec_name','width','height','avg_frame_rate','color_transfer','color_primaries','sample_aspect_ratio']})
    item['hdr_to_sdr']=v.get('color_transfer') in ('smpte2084','arib-std-b67')
    if item['hdr_to_sdr']:item['warnings'].append('HDR convertido a SDR Rec.709; revisar apariencia en el teléfono')
   report['scenes'].append(item);report['warnings'].extend(scene['id']+': '+w for w in item['warnings'])
 return report
