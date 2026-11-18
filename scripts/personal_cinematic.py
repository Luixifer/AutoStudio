"""Conservative cinematic image preparation for personal science Shorts.

This adjusts photographs or illustrations, it does not invent detail,
make a bad source image photorealistic, or certify scientific accuracy.
All adjustments are mild to preserve useful source information.
"""
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat


def cinematic_grade(source, strength=0.65):
    """Return RGB image. Grade before expensive 4x supersampling."""
    if not 0 <= strength <= 1:
        raise ValueError("La intensidad cinematográfica debe estar entre 0 y 1.")
    image=ImageOps.exif_transpose(source).convert("RGB")
    if strength==0:
        return image.copy()
    # Keep natural star colours and scientific displays recognisable.
    image=ImageEnhance.Contrast(image).enhance(1+.07*strength)
    image=ImageEnhance.Color(image).enhance(1+.06*strength)
    image=ImageEnhance.Sharpness(image).enhance(1+.12*strength)
    return image


def source_image_report(path):
    """Signal-only warning system: neither artistic quality nor subject detection."""
    with Image.open(path) as original:
        im=ImageOps.exif_transpose(original).convert("RGB")
    width,height=im.size
    sample=im.copy()
    sample.thumbnail((480,480),Image.Resampling.LANCZOS)
    gray=sample.convert("L")
    histogram=gray.histogram()
    count=sum(histogram)
    dark=sum(histogram[:16])/count
    bright=sum(histogram[245:])/count
    contrast=ImageStat.Stat(gray).stddev[0]
    edges=ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).mean[0]
    warnings=[]
    if width<720 or height<900:
        warnings.append("Imagen de baja resolución para un Short vertical.")
    if dark>.93 and contrast<14:
        warnings.append("Imagen casi negra; comprobar si el resultado es intencionado.")
    if bright>.93 and contrast<14:
        warnings.append("Imagen casi blanca o sobreexpuesta.")
    if edges<4 and contrast<8:
        warnings.append("Muy poco detalle visual; conviene otra imagen.")
    return {
        "width":width,"height":height,
        "dark_fraction":round(dark,4),
        "bright_fraction":round(bright,4),
        "contrast_proxy":round(contrast,2),
        "detail_proxy":round(edges,2),
        "warnings":warnings,
        "artistic_quality_verified":False
    }


def fit_for_camera(source, width, height, focal=(.5,.5)):
    """Fit image for moving full-frame camera, preserving safe focal framing.

    For matching aspect ratios, preserve full bleed. For non-matching ratios,
    retain the entire main artwork against a darker defocused duplicate.
    """
    if not isinstance(focal,(list,tuple)) or len(focal)!=2 or any(not .05<=float(v)<=.95 for v in focal):
        raise ValueError("Punto focal no válido.")
    image=cinematic_grade(source)
    ratio=image.width/image.height
    target=width/height
    if abs(ratio-target)<.16:
        return ImageOps.fit(image,(width,height),Image.Resampling.LANCZOS,
                            centering=(float(focal[0]),float(focal[1]))),True
    bg=image.resize((width,height),Image.Resampling.LANCZOS)
    bg=bg.filter(ImageFilter.GaussianBlur(max(12,width//24)))
    bg=ImageEnhance.Brightness(bg).enhance(.32)
    maxh=int(height*(.70 if height>width else .82))
    scale=min(width/image.width,maxh/image.height)
    fg=image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),Image.Resampling.LANCZOS)
    bg.paste(fg,((width-fg.width)//2,(height-fg.height)//2))
    return bg,False
