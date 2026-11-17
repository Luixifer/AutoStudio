"""Short dynamic captions, grounded in the measured synthesis timeline."""
def group_words(words,max_words=3):
    if not words:raise ValueError('Missing timed words.')
    if not isinstance(max_words,int) or not 1<=max_words<=3:raise ValueError('Use one to three words.')
    if any(w['start']<0 or w['end']<=w['start'] for w in words):raise ValueError('Invalid acoustic word duration.')
    if any(b['start']<a['end']-.002 for a,b in zip(words,words[1:])):raise ValueError('Acoustic words overlap.')
    groups=[];part=[]
    def commit():
        if not part:return
        groups.append({'start':part[0]['start'],'end':part[-1]['end'],'text':' '.join(w['word'] for w in part),'words':part.copy()})
        part.clear()
    for word in words:
        part.append(word)
        if len(part)==max_words or word['word'].rstrip('»”"').endswith(('.', '!', '?', ';', ':')):commit()
    commit()
    return groups

def caption_at(groups,t):
    for i,group in enumerate(groups):
        hold=min(group['end']+.10,groups[i+1]['start']) if i+1<len(groups) else group['end']+.08
        if group['start']<=t<=hold:
            active=next((j for j,w in enumerate(group['words']) if w['start']<=t<w['end']),-1)
            return {**group,'active':active}
    return None
