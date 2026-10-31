from pathlib import Path
import base64,difflib,json,os,re,urllib.request,winreg
root=Path(__file__).resolve().parents[1]
key=os.getenv('GEMINI_API_KEY')
if not key:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Environment') as r:key=winreg.QueryValueEx(r,'GEMINI_API_KEY')[0]
payload={'contents':[{'role':'user','parts':[{'text':'Transcribe this Mandarin audio verbatim in Traditional Chinese. Return JSON keys transcript, delivery, audible_issues (array). Do not infer missing words. No other text.'},{'inlineData':{'mimeType':'audio/wav','data':base64.b64encode((root/'assets/full-voice.wav').read_bytes()).decode()}}]}],'generationConfig':{'responseMimeType':'application/json','temperature':0}}
request=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent',data=json.dumps(payload).encode(),headers={'x-goog-api-key':key,'Content-Type':'application/json'})
with urllib.request.urlopen(request,timeout=120) as response:reply=json.load(response)
result=json.loads(''.join(p.get('text','') for p in reply['candidates'][0]['content']['parts']))
normalize=lambda s:re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]','',s)
expected=(root/'narration.txt').read_text(encoding='utf-8')
result['similarity']=round(difflib.SequenceMatcher(None,normalize(expected),normalize(result.get('transcript',''))).ratio(),4)
result['method']='Audio-only Gemini 3.8 Flash transcription, expected text withheld; automated review, not human listening.'
(root/'assets/narration/transcription-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Audio transcription similarity:',result['similarity'])
print('Reported audible issues:',len(result.get('audible_issues',[])))

