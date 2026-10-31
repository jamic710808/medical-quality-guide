"""Independent automated listening check using audio only; no expected text in prompt."""
from pathlib import Path
import os,json,base64,urllib.request,urllib.error,sys,re,difflib,time
root=Path(sys.argv[1]);film=json.loads((root/'film.json').read_text(encoding='utf-8'))
key=os.environ['GEMINI_API_KEY'];results=[]
for s in film['scenes']:
    p=root/s['voice'];dest=root/'audio'/f"{s['id']}-asr.json"
    if dest.exists():r=json.loads(dest.read_text(encoding='utf-8'))
    else:
        payload={'contents':[{'role':'user','parts':[{'text':'Transcribe this Mandarin audio verbatim into Traditional Chinese. Return JSON with keys transcript, language, delivery (brief description), audible_issues (list). Do not infer missing words. Do not add commentary outside JSON.'},{'inlineData':{'mimeType':'audio/wav','data':base64.b64encode(p.read_bytes()).decode()}}]}],'generationConfig':{'responseMimeType':'application/json','temperature':0}}
        req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent',data=json.dumps(payload).encode(),headers={'x-goog-api-key':key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=150) as f:reply=json.load(f)
            raw=''.join(x.get('text','') for x in reply['candidates'][0]['content']['parts']);r=json.loads(raw)
            dest.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
        except Exception as e:
            print('ASR failed '+s['id']+' '+type(e).__name__,flush=True);continue
    norm=lambda v:re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]','',v).lower()
    score=difflib.SequenceMatcher(None,norm(s['narration']),norm(r.get('transcript',''))).ratio()
    results.append({'scene':s['id'],'similarity':round(score,4),'expected':s['narration'],'transcript':r.get('transcript'),'delivery':r.get('delivery'),'audible_issues':r.get('audible_issues',[])})
    print(s['id']+' transcript similarity '+str(round(score,3)),flush=True)
(root/'audio/transcription-review.json').write_text(json.dumps({'method':'independent Gemini 3.8 Flash audio transcription; automated, not human listening','results':results},ensure_ascii=False,indent=2),encoding='utf-8')
