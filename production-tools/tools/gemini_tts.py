"""Generate only the approved fictional narration, keeping credentials out of files/logs."""
import os,json,base64,urllib.request,urllib.error,hashlib,time,sys,wave
from pathlib import Path

ROOT=Path(sys.argv[1]).resolve()
FILM=json.loads((ROOT/'film.json').read_text(encoding='utf-8'))
KEY=os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
if not KEY:raise SystemExit('No Gemini API key configured in the process.')
MODEL='gemini-3.8-flash-tts'
STYLE='Adult female narrator in warm, calm, conversational Taiwan Mandarin. Natural zh-TW pronunciation, clear professional storytelling, light smiling office humor, never childish, never an advertisement. Moderate pace. Read the exact Traditional Chinese transcript only, do not read directions. FF is pronounced as two English letter Fs.'
logs=[]
for s in FILM['scenes']:
    p=ROOT/s['voice'];record=p.with_suffix('.wav.json');text=s['narration']
    fingerprint=hashlib.sha256((MODEL+'Kore'+STYLE+text).encode()).hexdigest()
    if p.exists() and record.exists():
        r=json.loads(record.read_text(encoding='utf-8'))
        if r.get('key')==fingerprint and r.get('audioSha256')==hashlib.sha256(p.read_bytes()).hexdigest():
            print('Reuse '+s['id'],flush=True);continue
    payload={'model':MODEL,'input':[{'type':'user_input','content':[{'type':'text','text':text,'annotations':[{'type':'speech_metadata','style':STYLE}]}]}],'response_format':{'type':'audio'},'generation_config':{'speech_config':[{'voice':'Kore'}]}}
    data=json.dumps(payload).encode()
    response=None
    for attempt in range(3):
        try:
            req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/interactions',data=data,headers={'Content-Type':'application/json','x-goog-api-key':KEY})
            with urllib.request.urlopen(req,timeout=180) as r:response=json.load(r)
            break
        except urllib.error.HTTPError as e:
            raw=e.read().decode(errors='replace').replace(KEY,'[REDACTED]')
            error={'scene':s['id'],'model':MODEL,'http_status':e.code,'error':raw[:3000],'attempt':attempt+1}
            (ROOT/'audio/tts-failure.json').write_text(json.dumps(error,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps(error,ensure_ascii=False),flush=True)
            if e.code in (429,500,502,503) and attempt<2:time.sleep(8*(attempt+1));continue
            raise SystemExit('Gemini TTS request failed; no substitute engine used.')
    blocks=[c for step in response.get('steps',[]) for c in step.get('content',[]) if c.get('type')=='audio' and c.get('data')]
    if not blocks and response.get('output_audio'):blocks=[response['output_audio']]
    if not blocks:raise RuntimeError('Response has no audio block. Top-level keys: '+str(list(response)))
    audio=base64.b64decode(blocks[-1]['data'])
    if audio[:4]!=b'RIFF':
        with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(audio)
    else:p.write_bytes(audio)
    meta={'key':fingerprint,'engine':'gemini-api','model':MODEL,'voice':'Kore','style':STYLE,'text':text,'audioSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source':'Gemini API interactions','verification':'exact requested transcript; listening and transcription pending'}
    record.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    logs.append({'scene':s['id'],'bytes':p.stat().st_size,'model':MODEL,'voice':'Kore'})
    print('Generated '+s['id']+' '+str(p.stat().st_size)+' bytes',flush=True)
    if '--first' in sys.argv:break
(ROOT/'audio/tts-generation.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2),encoding='utf-8')
