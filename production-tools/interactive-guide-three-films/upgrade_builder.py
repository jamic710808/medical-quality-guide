"""Create a repeatable three-film builder from the previous two-film source."""
from pathlib import Path
import json,re,shutil

WORK=Path(__file__).resolve().parent
ROOT=WORK.parents[2]
OLD=ROOT/'specs/research/2026-10-31-medical-dual-video'
VIS=Path('C:/Users/jamic/.codex/visualizations/2026/10/31/01a18fc0-0876-7220-b07f-83c457684060')
OUT=VIS/'medical-triple-guide'
LEGACY=Path('C:/Users/jamic/.codex/visualizations/2026/10/31/01a18f5d-7c8e-79b1-8a4f-61dd0291ace2/medical-dual-guide')
MOTION=VIS/'evidence-film-90s'
WORK.mkdir(exist_ok=True);(OUT/'assets/img').mkdir(parents=True,exist_ok=True)
for source,name in [(ROOT/'架構圖解_20261031/醫療病歷質控_互動架構圖解.html','原雙版頁_加入90秒前.html'),(OLD/'build_guide.py','build_dual_legacy.py.bak'),(OLD/'verify_guide.py','verify_dual_legacy.py.bak'),(OLD/'verify_guide.cjs','verify_dual_legacy.cjs.bak')]:
    if not (WORK/name).exists():shutil.copy2(source,WORK/name)
for name in ['general-embed.mp4','animation-embed.mp4']:
    shutil.copy2(LEGACY/'assets'/name,OUT/'assets'/name)
shutil.copy2(MOTION/'out/每個疑點都有來處_90秒完整版_Kore.mp4',OUT/'assets/motion-embed.mp4')
s=(WORK/'build_dual_legacy.py.bak').read_text(encoding='utf-8')
def replace(a,b):
    global s
    if a not in s:raise RuntimeError('Missing upgrade marker: '+a[:90])
    s=s.replace(a,b)
replace("OUT=Path(r'C:\\Users\\jamic\\.codex\\visualizations\\2026\\10\\31\\01a18f5d-7c8e-79b1-8a4f-61dd0291ace2\\medical-dual-guide')",f'OUT=Path({str(OUT)!r})')
replace("BACKUP=WORK/'原架構圖解_加入影片前.html'","BACKUP=ROOT/'specs/research/2026-10-31-medical-dual-video/原架構圖解_加入影片前.html'")
replace("ANIMATION=OUT.parent/'ff-medical-film'",f"ANIMATION=Path({str(LEGACY.parent/'ff-medical-film')!r})\nMOTION=Path({str(MOTION)!r})\nmotion_timeline=json.loads((MOTION/'timeline.json').read_text(encoding='utf-8'))")
replace("OUT.mkdir(exist_ok=True);(OUT/'assets/img').mkdir(exist_ok=True)","OUT.mkdir(exist_ok=True);(OUT/'assets/img').mkdir(parents=True,exist_ok=True)\nfor media_name in ['general-embed.mp4','animation-embed.mp4']:\n    shutil.copy2(Path("+repr(str(LEGACY))+")/'assets'/media_name,OUT/'assets'/media_name)\nshutil.copy2(MOTION/'out/每個疑點都有來處_90秒完整版_Kore.mp4',OUT/'assets/motion-embed.mp4')")
replace("save_img(ANIMATION/'poster.png','animation-poster.jpg')","save_img(ANIMATION/'poster.png','animation-poster.jpg')\nsave_img(MOTION/'index-31.00s.png','motion-poster.jpg')")
mapping={'dashboard':(0,'記載差異與待複核疑點'),'sources':(6,'來源、時間與版本'),'rules':(18,'規則與模型的限定範圍'),'case':(33,'回查原文與人工複核'),'graph':(None,''),'evaluation':(None,''),'release':(86,'正式使用前的准入邊界'),'assets':(None,''),'governance':(76,'人工責任與依權限簽署'),'operations':(None,'')}
sync={'general':[], 'animation':[], 'motion':[{'start':0,'step':'dashboard'},{'start':6,'step':'sources'},{'start':18,'step':'rules'},{'start':33,'step':'case'},{'start':47,'step':'case'},{'start':61,'step':'case'},{'start':76,'step':'governance'},{'start':86,'step':'release'}]}
extra=f"""
motion_mapping={mapping!r}
for st in steps:
    st['motionTime'],st['motionLabel']=motion_mapping[st['key']]
sync={sync!r}
sync['general']=[dict(start=c['start'],step=c['id'] if c['id'] in {{s['key'] for s in steps}} else None) for c in chapters]
animation_steps=['dashboard','sources','case','graph','rules','case','case','case','governance','operations','evaluation','assets']
sync['animation']=[dict(start=s['startFrame']/timeline['fps'],step=animation_steps[i]) for i,s in enumerate(timeline['scenes'])]
"""
replace('films={',extra+'\nfilms={')
extra2="""
films={'motion':dict(label='90 秒精華版｜每個疑點，都有來處',short='90 秒精華版',duration=90,poster='motion-poster.jpg',file='motion-embed.mp4',description='1 分 30 秒・Kore 女聲・證據、複核與責任主線',boundary='合成教學流程視覺化，包含修訂與依權限簽署示意；不是正式應用操作錄影。正式使用仍需專家評測與醫院准入。',voice='Gemini 3.8 Flash-Lite TTS／Kore',chapters=[dict(start=s['start'],title=s['title'],id=s['id']) for s in motion_timeline['scenes']]),**films}
"""
replace("(WORK/'tour-data.json').write_text",extra2+"\n(WORK/'tour-data.json').write_text")
replace("{'films':films,'steps':steps}","{'films':films,'steps':steps,'sync':sync}")
replace('grid-template-columns:1fr 1fr;gap:12px;margin-bottom:18px','grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:18px')
replace('.ip .video-tabs{gap:8px}', '.ip .video-tabs{gap:8px;grid-template-columns:1fr}.ip .video-tabs button{min-width:0}.ip .video-tabs [data-film="motion"]{border-width:2px}')
replace('WATCH / 兩種視角，同一條主線','WATCH / 三種視角，同一條主線')
replace('先看實際介面，<br>再看懂背後的責任。','先用 90 秒看懂，<br>再逐步深入。')
replace('一般版：看功能在哪裡、先看什麼。<br>動畫版：看證據、版本與人如何接手。','90 秒精華版：掌握證據與責任主線。<br>一般版看實際介面，動畫版看完整職場故事。')
replace('<div class="video-tabs" role="tablist" aria-label="影片版本">','<div class="video-tabs" role="tablist" aria-label="影片版本"><button id="ip-tab-motion" role="tab" aria-selected="true" aria-controls="ip-film-panel" tabindex="0" data-film="motion"><b>90 秒精華版</b><span>每個疑點，都有來處 · 1:30</span></button>')
replace('id="ip-tab-general" role="tab" aria-selected="true" aria-controls="ip-film-panel" tabindex="0"','id="ip-tab-general" role="tab" aria-selected="false" aria-controls="ip-film-panel" tabindex="-1"')
replace('aria-labelledby="ip-tab-general"','aria-labelledby="ip-tab-motion"')
replace('<strong id="ip-film-title">一般版｜全功能介面路演</strong>','<strong id="ip-film-title">90 秒精華版｜每個疑點，都有來處</strong>')
replace('poster="assets/img/general-poster.jpg"','poster="assets/img/motion-poster.jpg"')
replace('一般版播放時，同步切換演示步驟','目前影片播放時，同步切換相關演示步驟')
replace('<p class="caption">這裡是既有介面截圖的教材導覽','<p class="caption" id="ip-sync-note" aria-live="polite">可選擇讓演示步驟跟隨目前影片；教學短片僅提供相關概念對照。</p><p class="caption">這裡是既有介面截圖的教材導覽')
replace('一般版為 137.15 秒；動畫版為 217.867 秒。章節取自各自的時間軸。','90 秒精華版為 90 秒／8 章；一般版為 137.15 秒／12 章；動畫版為 217.867 秒／12 章。章節取自各自的實際時間軸。')
replace('一般版 chapters.json；動畫版 timeline.json；本輪 ffprobe','三版各自的 chapters.json／timeline.json；本輪媒體規格核對')
replace('一般版使用工程合成資料的介面截圖；動畫版為合成教學故事。','一般版使用工程合成資料的介面截圖；動畫版與 90 秒精華版為合成教學故事或流程示意。')
replace('兩版皆不構成臨床效果或醫院准入證據；本輪未新增全片人工聽音、獨立影片評審或臨床驗收。','三版皆不構成臨床效果或醫院准入證據；本輪僅整合既有影片，未新增完整人工聽音或臨床驗收。')
replace("let mode='general',jsel=0,serial=0,ready=null,readyResolve=null,opener=null;","let mode='motion',jsel=0,serial=0,ready=null,readyResolve=null,opener=null,metaHandler=null,seekSerial=0;")
replace("const saved={general:0,animation:0},urls={};","const saved=Object.fromEntries(Object.keys(FILMS).map(k=>[k,0])),urls={},SYNC=@@SYNC@@;")
mark=r'''function markChapter(){let k=0;FILMS[mode].chapters.forEach((c,i)=>{if(vid.currentTime>=c.start-.035)k=i});$$('.chip',chb).forEach((b,i)=>{b.classList.toggle('on',i===k);b.setAttribute('aria-current',i===k?'true':'false');});$('#ip-film-status').textContent=`${FILMS[mode].short} · ${fmt(vid.currentTime)} / ${fmt(FILMS[mode].duration)} · ${FILMS[mode].chapters[k].title}`;
if($('#ip-follow').checked){let cue=null;for(const c of SYNC[mode]){if(vid.currentTime>=c.start-.035)cue=c;else break;}const j=cue?JR.findIndex(s=>s.key===cue.step):-1;if(j>=0&&j!==jsel){jsel=j;drawJ(false);}$('#ip-sync-note').textContent=j>=0?`${FILMS[mode].short}：同步至「${JR[j].label}」${mode==='general'?'；介面快照導覽。':'；相關概念對照，非該功能的實際操作錄影。'}`:`${FILMS[mode].short}：目前段落沒有直接對應的功能步驟，保留你的選擇。`;}}
'''
s,n=re.subn(r'function markChapter\(\)\{.*?(?=async function setMode)',lambda m:mark,s,flags=re.S);assert n==1
setmode=r'''async function setMode(key){if(!FILMS[key])throw Error('Unknown film');if(mode===key&&vid.src){return await ready;}if(vid.readyState>=1)saved[mode]=vid.currentTime;vid.pause();if(metaHandler)vid.removeEventListener('loadedmetadata',metaHandler);if(readyResolve)readyResolve(false);mode=key;const ticket=++serial,f=FILMS[key];$$('[data-film]').forEach(b=>{const on=b.dataset.film===key;b.setAttribute('aria-selected',on);b.tabIndex=on?0:-1});$('#ip-film-panel').setAttribute('aria-labelledby','ip-tab-'+key);$('#ip-film-title').textContent=f.label;$('#ip-film-meta').textContent=f.description;$('#ip-film-boundary').textContent=f.boundary;$('#ip-voice').textContent='原片聲音：'+f.voice+'。沿用現有配音。';vid.poster=A+f.poster;$('#ip-film-status').textContent='影片載入中…';drawChapters();let resolve;const pending=ready=new Promise(r=>resolve=r);readyResolve=resolve;metaHandler=()=>{vid.removeEventListener('loadedmetadata',metaHandler);if(ticket!==serial){resolve(false);return;}vid.currentTime=Math.min(saved[key],Math.max(0,vid.duration-.1));markChapter();resolve(true);};vid.addEventListener('loadedmetadata',metaHandler);vid.src=blobUrl(key);vid.load();return await pending;}
'''
s,n=re.subn(r'async function setMode\(key\)\{.*?(?=async function seekTo)',lambda m:setmode,s,flags=re.S);assert n==1
seek=r'''async function seekTo(key,seconds,play=true){const operation=++seekSerial;if(!await setMode(key)||operation!==seekSerial||mode!==key)return;vid.currentTime=Math.max(0,Math.min(seconds,vid.duration-.05));markChapter();if(play){try{await vid.play()}catch(e){$('#ip-film-status').textContent='已定位章節；請按影片播放鍵。';}}vid.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});}
'''
s,n=re.subn(r'async function seekTo\(key,seconds,play=true\)\{.*?(?=vid.addEventListener)',lambda m:seek,s,flags=re.S);assert n==1
replace("const key=e.key==='Home'?'general':e.key==='End'?'animation':mode==='general'?'animation':'general';","const keys=Object.keys(FILMS),index=keys.indexOf(mode),key=e.key==='Home'?keys[0]:e.key==='End'?keys.at(-1):keys[(index+(e.key==='ArrowRight'?1:-1)+keys.length)%keys.length];")
replace('<button type="button" id="ip-watch-animation">▶ ${j.animLabel} · ${fmt(j.animationTime)}</button></div>','<button type="button" id="ip-watch-animation">▶ ${j.animLabel} · ${fmt(j.animationTime)}</button><button type="button" id="ip-watch-motion" ${j.motionTime===null?\'disabled\':\'\'}>${j.motionTime===null?\'90 秒精華版未涵蓋此功能\':\'▶ 精華版：\'+j.motionLabel+\' · \'+fmt(j.motionTime)+\'（概念對照）\'}</button></div>')
replace("$('#ip-watch-animation').onclick=()=>seekTo('animation',j.animationTime);","$('#ip-watch-animation').onclick=()=>seekTo('animation',j.animationTime);$('#ip-watch-motion').onclick=()=>{if(j.motionTime!==null)seekTo('motion',j.motionTime);};")
replace("window.__introPack={get mode()", "$('#ip-follow').addEventListener('change',()=>{if($('#ip-follow').checked)markChapter();else $('#ip-sync-note').textContent='播放跟隨已關閉；手動選擇演示步驟不會被影片改變。';});\nconst motionBridge=document.createElement('button');motionBridge.type='button';motionBridge.id='ip-arch-motion';motionBridge.textContent='▶ 90 秒精華版：原文回查 · 0:33';if(dock){dock.appendChild(motionBridge);motionBridge.onclick=()=>seekTo('motion',33);$$('[data-node]').forEach(b=>b.addEventListener('click',()=>{const t={ui:33,model:18}[b.dataset.node];motionBridge.disabled=t===undefined;motionBridge.textContent=t===undefined?'90 秒精華版未解說此架構零件':'▶ 90 秒精華版：'+(b.dataset.node==='ui'?'原文回查':'有限候選與證據')+' · '+fmt(t);motionBridge.onclick=()=>{if(t!==undefined)seekTo('motion',t);};}));}\nwindow.__introPack={sync:SYNC,get mode()")
replace("drawJ();setMode('general');","drawJ();setMode('motion');")
replace("'MODELTIME':str(at['s05'])","'MODELTIME':str(at['s05']),'SYNC':json.dumps(sync,ensure_ascii=False)")
replace("raw=GENERAL/'醫療病歷質控_全功能路演_Kore.mp4' if key=='general' else ANIMATION/'final.mp4'","raw=GENERAL/'醫療病歷質控_全功能路演_Kore.mp4' if key=='general' else ANIMATION/'final.mp4' if key=='animation' else MOTION/'out/每個疑點都有來處_90秒完整版_Kore.mp4'")
replace("assert 'ip-data-general' in standalone and 'ip-data-animation' in standalone","assert all('ip-data-'+key in standalone for key in films)")
s=s.replace('雙版影片','三版影片')
# Keep historical shared entry points synchronized; the canonical output has a three-film name.
s+='''
legacy_work=ROOT/'specs/research/2026-10-31-medical-dual-video'
legacy_out=Path('''+repr(str(LEGACY))+''')
for target in [legacy_work/'醫療病歷質控_雙版影片互動導覽.html',legacy_out/'醫療病歷質控_雙版影片互動導覽.html']:
    shutil.copy2(OUT/'醫療病歷質控_三版影片互動導覽.html',target)
shutil.copy2(OUT/'assets/motion-embed.mp4',legacy_out/'assets/motion-embed.mp4')
shutil.copy2(OUT/'assets/img/motion-poster.jpg',legacy_out/'assets/img/motion-poster.jpg')
shutil.copy2(OUT/'guide.src.html',legacy_out/'guide.src.html')
for name in ['tour-data.json','media-manifest.json']:
    shutil.copy2(WORK/name,legacy_work/name)
'''
(WORK/'build_guide.py').write_text(s,encoding='utf-8')
print('Prepared three-film builder and media; existing pages unchanged until build_guide.py runs.')
