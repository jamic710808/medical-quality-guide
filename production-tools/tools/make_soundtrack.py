from pathlib import Path
import json,sys,wave,math
import numpy as np
root=Path(sys.argv[1]);t=json.loads((root/'timeline.json').read_text(encoding='utf-8'));film=json.loads((root/'film.json').read_text(encoding='utf-8'))
sr=48000;duration=t['durationSeconds'];n=int(duration*sr);sound=np.zeros((n,2),dtype=np.float32)
def add(start,freq,length=.85,amp=.025,pan=.5,kind='wood'):
    i=int(start*sr);m=min(int(length*sr),n-i)
    if m<=0:return
    tt=np.arange(m,dtype=np.float32)/sr
    if kind=='wood':v=(np.sin(2*np.pi*freq*tt)*np.exp(-tt*5)+.22*np.sin(2*np.pi*freq*2.01*tt)*np.exp(-tt*13))*(1-np.exp(-tt*350))
    elif kind=='bass':v=np.sin(2*np.pi*freq*tt)*np.exp(-tt*2)*(1-np.exp(-tt*60))
    else:v=np.sin(2*np.pi*freq*tt)*np.exp(-tt*18)*(1-np.exp(-tt*700))
    sound[i:i+m,0]+=v*amp*math.sqrt(1-pan);sound[i:i+m,1]+=v*amp*math.sqrt(pan)
freq=lambda midi:440*2**((midi-69)/12)
# Original sparse D-major plucked score; no third-party music samples.
beat=60/76;chords=[[55,62,67,71],[50,57,62,66],[52,59,64,67],[57,64,69,73]]
bar=beat*4
for k,start in enumerate(np.arange(0,duration,bar*2)):
    chord=chords[k%4]
    add(float(start),freq(chord[0]-12),2,.018,.5,'bass')
    for j,m in enumerate(chord[1:]+[chord[2]+12]):add(float(start+beat*(j*.9+.5)),freq(m),1.6,.019,.25+j*.17)
    if k%3!=2:add(float(start+beat*5.25),freq(chord[1]+12),1.0,.011,.65)
# Voice activity duck; serious scenes additionally soften the score.
duck=np.ones(n,dtype=np.float32)
for s in t['scenes']:
    a=int(s['voiceStartFrame']/t['fps']*sr);b=min(n,int((s['voiceStartFrame']+s['voiceFrames'])/t['fps']*sr));fade=int(.18*sr)
    duck[a:b]=.36
    if a>fade:duck[a-fade:a]=np.linspace(1,.36,fade)
    if b+fade<n:duck[b:b+fade]=np.linspace(.36,1,fade)
    if s['id'] in ['s03','s06','s07','s11']:
        sa=int(s['startFrame']/t['fps']*sr);sb=int(s['endFrame']/t['fps']*sr);duck[sa:sb]*=.7
sound*=duck[:,None]
# Subtle original action cues, not alarms: paper click, soft confirmation, handoff.
for s in t['scenes']:
    start=s['startFrame']/t['fps']
    for off in ([2,4,6] if s['id']=='s02' else [2,5,8,11] if s['id']=='s09' else [3.2]):
        add(start+off,880 if s['id']=='s09' else 620,.11,.009,.5,'cue')
sound[:sr]*=np.linspace(0,1,sr)[:,None];sound[-sr*2:]*=np.linspace(1,0,sr*2)[:,None]
pcm=np.clip(sound,-.98,.98);p=root/'audio/original-score.wav'
with wave.open(str(p),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((pcm*32767).astype('<i2').tobytes())
film['audioTracks']=[{'file':'audio/original-score.wav','startSeconds':0,'gain':1.0}]
(root/'film.json').write_text(json.dumps(film,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'audio/music-source.md').write_text('# 配樂與音效來源\n\n本片程式原創：D 大調稀疏木質撥音、柔和低音與提示音；無外部音樂或取樣。聲音依旁白段落降低，重要限制段另外降低。由 make_soundtrack.py 可重建。不是 Gemini 生成的配樂；Kore 僅負責旁白。\n',encoding='utf-8')
print('Original ducked soundtrack written; duration '+str(round(duration,3)))
