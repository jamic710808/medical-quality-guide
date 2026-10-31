from pathlib import Path
import json,os,base64,urllib.request,subprocess,sys
root=Path(sys.argv[1]);t=json.loads((root/'timeline.json').read_text(encoding='utf-8'));key=os.environ['GEMINI_API_KEY'];results=[]
for sid in ['s01','s07','s12']:
 s=next(x for x in t['scenes'] if x['id']==sid);p=root/'audio'/f'{sid}-mix-review.wav';start=s['startFrame']/30
 subprocess.run(['ffmpeg','-y','-v','error','-ss',str(start),'-i',str(root/'audio/mix-master.wav'),'-t',str(s['durationFrames']/30),'-ar','24000','-ac','1',str(p)],check=True)
 payload={'contents':[{'parts':[{'text':'Evaluate this narrated animation audio excerpt. Return JSON with voice_description, speech_intelligibility, background_music_balance, clipping_or_glitches (list), caveats. Report what is actually audible, do not infer a brand or model. This is an automated audio review, not human acceptance.'},{'inlineData':{'mimeType':'audio/wav','data':base64.b64encode(p.read_bytes()).decode()}}]}],'generationConfig':{'responseMimeType':'application/json','temperature':0}}
 req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent',data=json.dumps(payload).encode(),headers={'x-goog-api-key':key,'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=120) as f:d=json.load(f)
  r=json.loads(''.join(p.get('text','') for p in d['candidates'][0]['content']['parts']));results.append({'scene':sid,'assessment':r});print(sid+' mix assessed',flush=True)
 except Exception as e:results.append({'scene':sid,'error':type(e).__name__});print(sid+' review error '+type(e).__name__,flush=True)
(root/'audio/mix-review.json').write_text(json.dumps({'method':'Gemini 3.8 Flash automated listening review of opening, human-review, and closing mixed excerpts; no human listening claimed','results':results},ensure_ascii=False,indent=2),encoding='utf-8')
