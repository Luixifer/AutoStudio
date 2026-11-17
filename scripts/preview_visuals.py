"""Distinct, original, conceptual visuals for a black-hole REVIEW-ONLY preview.

These diagrams are not photographs, metric simulations or NASA imagery.
Drawn locally with Pillow; role-specific illustrations must not be swapped.
"""
import math
import random

ROLES=("Apertura","Frontera","Luz","Alrededores","Límites")

def draw_scene_art(draw, role, width=720, top=130, bottom=700):
    if role not in ROLES:
        raise ValueError("Escena sin diagrama validado: "+str(role))
    # Deterministic star field with a different palette and layout per role.
    palette={
        "Apertura":((7,19,42),(252,167,86)),
        "Frontera":((9,22,49),(71,217,229)),
        "Luz":((10,18,45),(252,220,130)),
        "Alrededores":((25,14,37),(246,141,79)),
        "Límites":((21,15,45),(166,122,228)),
    }
    bg,accent=palette[role]
    draw.rectangle((0,top,width,bottom),fill=bg)
    rng=random.Random(1904+ROLES.index(role)*37)
    for _ in range(85):
        x=rng.randrange(28,width-28)
        y=rng.randrange(top+15,bottom-20)
        size=rng.choice([1,1,1,2,3])
        draw.ellipse((x-size,y-size,x+size,y+size),fill=(97,127,160))
    cx,cy=width//2,top+273
    if role=="Apertura":
        for radius,color in [(220,(25,48,78)),(188,(53,73,103)),(161,accent),(130,(244,212,164)),(110,(10,13,27)),(89,(3,8,17))]:
            draw.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=color)
        draw.arc((cx-214,cy-103,cx+214,cy+103),200,345,fill=(255,225,184),width=13)
    elif role=="Frontera":
        for radius,color in [(222,(21,64,94)),(180,(16,42,70)),(139,accent),(133,(7,17,29)),(90,(4,8,19))]:
            draw.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=color)
        draw.arc((cx-205,cy-205,cx+205,cy+205),-58,127,fill=(223,249,255),width=7)
        draw.line((74,cy+192,226,cy+192),fill=accent,width=6)
        draw.polygon([(226,cy+192),(207,cy+181),(207,cy+203)],fill=accent)
    elif role=="Luz":
        for radius,color in [(206,(38,49,83)),(161,accent),(145,(11,19,43)),(108,(4,9,20))]:
            draw.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=color)
        for offset in [-95,-55,10,65]:
            y=cy+offset
            draw.arc((56,y-155,width-56,y+155),10,170,fill=(239,221,143),width=6)
            draw.line((32,y+65,160,y+65),fill=(232,222,174),width=4)
    elif role=="Alrededores":
        for width_stroke in [40,27,16]:
            draw.arc((72,cy-168,648,cy+168),10,190,fill=accent,width=width_stroke)
            draw.arc((72,cy-168,648,cy+168),197,355,fill=(252,206,130),width=width_stroke)
        draw.ellipse((cx-120,cy-120,cx+120,cy+120),fill=(7,8,18))
        draw.arc((cx-148,cy-148,cx+148,cy+148),191,352,fill=(255,224,159),width=9)
    elif role=="Límites":
        for radius in [220,176,132]:
            draw.arc((cx-radius,cy-radius,cx+radius,cy+radius),30,310,fill=accent,width=5)
        for index in range(12):
            theta=index*math.pi/6
            a=(cx+int(82*math.cos(theta)),cy+int(82*math.sin(theta)))
            b=(cx+int(215*math.cos(theta+.32)),cy+int(215*math.sin(theta+.32)))
            draw.line((a,b),fill=(174,161,228),width=3)
        draw.ellipse((cx-49,cy-49,cx+49,cy+49),fill=(4,7,16))
        draw.arc((cx-85,cy-85,cx+85,cy+85),5,295,fill=(243,223,255),width=7)

def scene_visual_signature(role):
    if role not in ROLES:raise ValueError("Unknown role")
    return "original-schematic-"+role.lower()
