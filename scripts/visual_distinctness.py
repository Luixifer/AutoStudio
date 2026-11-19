"""Cross-scene visual composition QC from actual image model observations.

The image inspector must first PASS the individual frame. This second,
conservative gate compares *observed visual descriptions* from that model
against already selected scenes. It does not compare narration or prompts.
It never turns a FAIL/UNSURE into PASS or treat semantic diversity as
scientific verification.
"""
from __future__ import annotations
import re

# Remove narration boilerplate, camera-independent aesthetics and color/lighting
# descriptors. Do NOT remove structural nouns like vortex, tunnel, mountain,
# foreground, closeup, disk or horizon: those identify repeated shot composition.
BOILERPLATE = frozenset("""
a an the in on at and or of to for from by with without against over under above
below into through this that is are was were it its image picture scene shot frame
shows show showing depicts depicting visible appears appearance there background
dark black space outer cosmic deep photo photorealistic bright luminous
light lights lighting illuminated illumination colors color coloured colored
orange yellow blue red white green purple golden brown grey gray
cinematic high quality detailed highly realistic clear distinct featuring
has have as near nearby which along around next between asterisks
""".split())

def visual_terms(evidence):
    if not isinstance(evidence,str):
        return frozenset()
    # Normalize plurals conservatively; retain spatial and subject terms.
    tokens=re.findall(r"[a-z]{3,}",evidence.lower())
    result=[]
    for t in tokens:
        if t in BOILERPLATE:
            continue
        if t.endswith("ies") and len(t)>5:
            t=t[:-3]+"y"
        elif t.endswith("s") and len(t)>5 and not t.endswith("ss"):
            t=t[:-1]
        if t not in BOILERPLATE:
            result.append(t)
    return frozenset(result)

def compare_visual_evidence(evidence, prior, threshold=0.68):
    """Return matching prior scene or None, with a transparent similarity score.

    Restrict automatic rejection to scenes sharing >=3 nontrivial observed
    visual terms and with at least 4 terms in each description. This is
    deliberately conservative and can miss perceptual duplicates.
    """
    current=visual_terms(evidence)
    matches=[]
    if len(current)<4:
        return None
    for prior_scene,prior_evidence in prior:
        old=visual_terms(prior_evidence)
        if len(old)<4:
            continue
        shared=current & old
        score=len(shared)/min(len(current),len(old))
        if len(shared)>=3 and score>=threshold:
            matches.append({"prior_scene":prior_scene,"score":round(score,3),
                            "common_terms":sorted(shared)[:12]})
    return max(matches,key=lambda x:x["score"]) if matches else None
