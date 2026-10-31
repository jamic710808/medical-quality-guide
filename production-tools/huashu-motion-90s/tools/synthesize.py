from pathlib import Path
import base64,concurrent.futures,hashlib,json,os,subprocess,urllib.request,urllib.error,winreg
ROOT=Path(__file__).resolve().parents[1]
FILM=json.loads((ROOT/'film.json').read_text(encoding='utf-8'))
DEST=ROOT/'assets'/'narration-full';DEST.mkdir(exist_ok=True)
key=os.getenv('GEMINI_API_KEY')
if not key:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Environment') as r:key=winreg.QueryValueEx(r,'GEMINI_API_KEY')[0]
def make(row):
    path=DEST/(row['id']+'.wav');receipt=DEST/(row['id']+'-receipt.json')
    cache=path.exists() and receipt.exists() and json.loads(receipt.read_text(encoding='utf-8')).get('text')==row['narration']
    if not cache:
        body={'model':FILM['voice']['model'],'input':[{'type':'user_input','content':[{'type':'text','text':row['narration'],'annotations':[{'type':'speech_metadata','style':'Adult female narrator, Taiwan Mandarin, same warm and clear Kore voice throughout. Professional conversational explanation. Brisk natural delivery around 4.8 Chinese syllables per second, concise pauses. Read FF as the English letters F F. Read only the supplied script, no extra words, no music. Avoid theatrical acting.'}]}]}],'response_format':{'type':'audio'},'generation_config':{'speech_config':[{'voice':FILM['voice']['name']}]}}
        req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/interactions',data=json.dumps(body).encode(),headers={'x-goog-api-key':key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=120) as r:result=json.load(r)
        except urllib.error.HTTPError as e:raise RuntimeError('TTS '+row['id']+' HTTP '+str(e.code)) from None
        blocks=[c for s in result.get('steps',[]) if s.get('type')=='model_output' for c in s.get('content',[]) if c.get('type')=='audio']
        if not blocks:raise RuntimeError('No audio '+row['id'])
        raw=base64.b64decode(blocks[-1]['data']);path.write_bytes(raw)
        receipt.write_text(json.dumps({'id':result.get('id'),'model':body['model'],'voice':FILM['voice']['name'],'text':row['narration'],'sha256':hashlib.sha256(raw).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
    duration=float(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(path)],text=True))['format']['duration'])
    print(row['id'],round(duration,3),'budget',row['end']-row['start'],flush=True)
    return {**row,'voice':str(path.relative_to(ROOT)).replace('\\','/'),'audioDuration':duration}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(make,[s for s in FILM['scenes'] if s['narration']]))
(ROOT/'voice-measurements.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print('Total measured speech:',round(sum(r['audioDuration'] for r in results),3),'seconds')
