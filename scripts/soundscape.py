"""Original quiet synthetic ambience; not a field recording or licensed soundtrack."""
import wave
import numpy as np

def write_ambience(target,duration,cuts,rate=48000,theme="ocean"):
    size=round(duration*rate);rng=np.random.default_rng(202602);noise=rng.normal(0,1,size)
    spectrum=np.fft.rfft(noise);freq=np.fft.rfftfreq(size,1/rate);spectrum*=1/(1+(freq/270)**4);bed=np.fft.irfft(spectrum,n=size)
    bed=bed/max(float(np.std(bed)),1e-9)*.012;t=np.arange(size)/rate;bed*=np.minimum(1,t/1.3)*np.minimum(1,np.maximum(0,duration-t)/.7)
    if theme!='ocean':
        if theme not in {'auroras','dna','volcanoes'}:raise ValueError('Unknown original soundscape.')
        base={'auroras':110,'dna':220,'volcanoes':45}[theme]
        bed=bed*.65+(np.sin(t*2*np.pi*base)+.35*np.sin(t*2*np.pi*base*1.5))*.0025*np.minimum(1,t)*np.minimum(1,np.maximum(0,duration-t))
    for cut in cuts:
        n=int(.18*rate);start=int(cut*rate)
        if start+n>size:continue
        whoosh=rng.normal(0,1,n)*np.sin(np.linspace(0,np.pi,n))**2*.0018;bed[start:start+n]+=whoosh
    stereo=np.stack([bed,bed*.98],axis=1);pcm=(np.clip(stereo,-.95,.95)*32767).astype('<i2')
    with wave.open(str(target),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(rate);f.writeframes(pcm.tobytes())
    return {'origin':('Original deterministic synthetic water-like ambience' if theme=='ocean' else 'Original low-level synthetic soundscape: '+theme),'real_field_recording':False,'music_asset_downloaded':False,'mix_volume':.42,'seed':202602}
