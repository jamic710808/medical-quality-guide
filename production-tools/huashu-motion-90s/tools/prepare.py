from pathlib import Path
import json,re,subprocess,wave,math,array
ROOT=Path(__file__).resolve().parents[1]
film=json.loads((ROOT/'film.json').read_text(encoding='utf-8'))
rows=json.loads((ROOT/'voice-measurements.json').read_text(encoding='utf-8'))
starts=[.1,6.35,18.3,33.3,47.3,61.3,76.25]
args=['ffmpeg','-hide_banner','-loglevel','error','-y']
filters=[];captions=[]
for i,(row,start) in enumerate(zip(rows,starts)):
    scene=next(s for s in film['scenes'] if s['id']==row['id'])
    row['start']=scene['start'];row['end']=scene['end']
    args+=['-i',str(ROOT/row['voice'])]
    filters.append(f'[{i}:a]aresample=48000,aformat=channel_layouts=mono,adelay={round(start*1000)}:all=1[v{i}]')
    row['voiceStart']=start;row['voiceEnd']=round(start+row['audioDuration'],3)
    # Sentence/phrase captions are interpolated within the measured speech clip,
    # not word-level forced alignment. Split at punctuation to keep lines short.
    parts=[p for p in re.findall(r'[^，。、；！？]+[，。、；！？]?',row['narration']) if p.strip()]
    chunks=[];carry=''
    for part in parts:
        if len(carry+part)>23 and carry:chunks.append(carry);carry=''
        carry+=part
        if part[-1] in '。；！？':chunks.append(carry);carry=''
    if carry:chunks.append(carry)
    weights=[len(re.sub(r'[^\w\u4e00-\u9fff]','',s))+.8 for s in chunks]
    available=row['audioDuration']-.28;at=start+.1
    for text,w in zip(chunks,weights):
        end=at+available*w/sum(weights)
        captions.append({'start':round(at,3),'end':round(end,3),'text':text})
        at=end
filters.append(''.join(f'[v{i}]' for i in range(len(rows)))+f'amix=inputs={len(rows)}:normalize=0,apad,atrim=duration=90[out]')
args+=['-filter_complex',';'.join(filters),'-map','[out]','-c:a','pcm_s16le',str(ROOT/'assets/full-voice.wav')]
subprocess.run(args,check=True)
film['measuredVoice']=rows;film['captions']=captions
(ROOT/'timeline.json').write_text(json.dumps(film,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'narration.txt').write_text('\n'.join(s['narration'] for s in film['scenes'] if s['narration']),encoding='utf-8')
def stamp(t):
    n=round(t*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'
(ROOT/'subtitles.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for i,c in enumerate(captions))+'\n',encoding='utf-8')
source=Path('D:/CODEX/MedicalQualityCase-Windows/MedicalQuality/backend/fixtures/prototype-synthetic.json')
rules=json.loads(source.read_text(encoding='utf-8'))['rules']
(ROOT/'materials/rules.json').write_text(json.dumps([{'id':r['id'],'name':r['name']} for r in rules],ensure_ascii=False,indent=2),encoding='utf-8')
print('Measured narration 72.04s; placed in 90-second composition; captions:',len(captions))
