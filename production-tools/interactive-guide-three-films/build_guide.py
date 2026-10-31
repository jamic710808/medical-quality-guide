from pathlib import Path
import json,base64,shutil,hashlib,re,subprocess
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
OUT=Path('C:\\Users\\jamic\\.codex\\visualizations\\2026\\10\\31\\01a18fc0-0876-7220-b07f-83c457684060\\medical-triple-guide')
WORK=Path(__file__).resolve().parent
ORIGINAL=ROOT/'架構圖解_20261031/醫療病歷質控_互動架構圖解.html'
BACKUP=ROOT/'specs/research/2026-10-31-medical-dual-video/原架構圖解_加入影片前.html'
GENERAL=Path(r'D:\CODEX\MedicalQualityCase-Windows\MedicalQuality\artifacts\film-v2-20261031')
SHOTS=GENERAL.parent/'showcase-20261031/screenshots'
ANIMATION=Path('C:\\Users\\jamic\\.codex\\visualizations\\2026\\10\\31\\01a18f5d-7c8e-79b1-8a4f-61dd0291ace2\\ff-medical-film')
MOTION=Path('C:\\Users\\jamic\\.codex\\visualizations\\2026\\10\\31\\01a18fc0-0876-7220-b07f-83c457684060\\evidence-film-90s')
motion_timeline=json.loads((MOTION/'timeline.json').read_text(encoding='utf-8'))
OUT.mkdir(exist_ok=True);(OUT/'assets/img').mkdir(parents=True,exist_ok=True)
for media_name in ['general-embed.mp4','animation-embed.mp4']:
    shutil.copy2(Path('C:/Users/jamic/.codex/visualizations/2026/10/31/01a18f5d-7c8e-79b1-8a4f-61dd0291ace2/medical-dual-guide')/'assets'/media_name,OUT/'assets'/media_name)
shutil.copy2(MOTION/'out/每個疑點都有來處_90秒完整版_Kore.mp4',OUT/'assets/motion-embed.mp4')
if not BACKUP.exists():shutil.copy2(ORIGINAL,BACKUP)

def save_img(src,name):
    im=Image.open(src).convert('RGB');im.thumbnail((1800,1800))
    im.save(OUT/'assets/img'/name,'JPEG',quality=86,optimize=True)
    return name

def shot(name):
    p=GENERAL/'screenshots'/name
    return p if p.exists() else SHOTS/name

for name in ['dashboard','sources','rules','case','casegraph','evaluation','release','assets','governance','operations']:
    save_img(shot(name+'.png'),name+'.jpg')
save_img(GENERAL/'poster.png','general-poster.jpg')
save_img(ANIMATION/'poster.png','animation-poster.jpg')
save_img(MOTION/'index-31.00s.png','motion-poster.jpg')
chapters=json.loads((GENERAL/'chapters.json').read_text(encoding='utf-8'))
timeline=json.loads((ANIMATION/'timeline.json').read_text(encoding='utf-8'))
at={s['id']:s['startFrame']/timeline['fps'] for s in timeline['scenes']}
gt={s['id']:s['start'] for s in chapters}

# Source data for the skill's reusable stepper and percentage-based hotspot viewer.
steps=[
 dict(key='dashboard',label='質控工作臺',img='dashboard.jpg',title='先找到需要處理的病例',action='從病例隊列看風險、狀態與責任組，再選一份病例。',result='畫面是當時的合成工程資料快照；列表數字不是醫院成效。',chips=['病例隊列','風險與進度','責任範圍'],animation='s01',animLabel='動畫：交班前的工作',spots=[[7,21,'功能入口','左側選單依登入角色與權限顯示；各截圖可能使用不同工程身份。'],[46,53,'篩選病例','搜尋與狀態篩選協助縮小待處理範圍。'],[71,54,'病例處理進度','風險、當前進度與責任組是不同資訊，不應把完成一項檢查等同整份病歷合格。']]),
 dict(key='sources',label='資料接入',img='sources.jpg',title='確認資料從哪裡來',action='查看來源、用途與版本，再看解析狀態和覆蓋範圍。',result='部分解析或缺漏必須保留；來源已登記不代表全部內容已正確解析。',chips=['來源版本','用途與授權','解析覆蓋'],animation='s02',animLabel='動畫：授權後再開門',spots=[[7,27,'資料接入入口','先從資料接入頁認識來源，不直接把資料送給模型。'],[48,44,'來源與清單','來源、用途、版本與解析結果需一起查看；內容缺漏不應被視為通過。']]),
 dict(key='rules',label='規則與依據',img='rules.jpg',title='看清楚這次用哪一版規則',action='查看規則清單、依據與適用範圍，區分候選及批准資格。',result='八條是有限工程候選，不能據此宣稱已獲醫療專業批准。',chips=['八條有限規則','固定版本','候選資格'],animation='s05',animLabel='動畫：候選要帶出處',spots=[[7,33,'規則入口','規則與依據是檢查的基線，不是生成模型即時編造的標準。'],[50,45,'規則清單與範圍','規則版本、資格和適用用途共同限制可執行範圍。']]),
 dict(key='case',label='病例原文',img='case.jpg',title='把疑點帶回固定版本原文',action='從既有候選結果打開原文，比對來源、文書版本與被引用的段落。',result='本次實拍只展示原文定位，沒有執行整改、重核或簽字；完整責任閉環由動畫示意。',chips=['固定版本','原文定位','歷史候選'],animation='s03',animLabel='動畫：兩段不同怎麼辦',spots=[[38,21,'固定版本原文','這個視窗顯示被引用的文書版本；不是用最新內容替換歷史證據。'],[45,48,'定位到原文行','高亮顯示來源定位。引用能回查，不代表它必然支持醫療結論。'],[42,39,'合成資料標記','文書明列資料性質為合成工程病例，並非真實患者資料。']]),
 dict(key='graph',label='知識圖譜',img='casegraph.jpg',title='把關係與證據放在一起看',action='切換圖譜視圖，選一個節點或關係，再從檢查器查看來源。',result='連線是投影與語義關係；圖形連得上不等於臨床判斷已正確。',chips=['本體與術語','病例證據','規則影響'],animation='s04',animLabel='動畫：資料如何流轉',spots=[[7,38,'圖譜入口','本體、病例證據與規則影響是不同視角。'],[51,49,'節點與關係','選取節點或關係可聚焦目前投影，不能把視覺連線當作醫學推論證明。'],[86,47,'檢查器與來源','右側詳情可追查來源與版本；看不清時使用原尺寸放大。']]),
 dict(key='evaluation',label='專家評測',img='evaluation.jpg',title='先固定評測批次與獨立原判',action='查看建立批次的設定入口，理解原判專家與仲裁角色。',result='畫面只開啟設定表單，沒有提交、填造專家意見或產生臨床評測結論。',chips=['雙人獨立原判','分歧仲裁','表單未提交'],animation='s11',animLabel='動畫：工程與專家是兩道關',spots=[[43,7,'評測設定入口','表單展示建立固定版本批次的入口，不代表批次已經建立。'],[45,42,'兩位原判專家','獨立原判與後續仲裁分開保留；本地工程身份不能當作真實專家資格。'],[37,53,'仲裁與病例範圍','指定仲裁者與範圍會影響評測責任；本次實拍沒有提交。']]),
 dict(key='release',label='評測與准入',img='release.jpg',title='確認能用到哪個階段',action='查看准入申請與固定基線，逐項核對條件、缺項及責任接受。',result='本次沒有提交申請或生產放行；缺評測、授權或責任接受就不能直接使用。',chips=['版本基線','條件與缺項','未生產放行'],animation='s11',animLabel='動畫：缺條件就等待',spots=[[42,7,'建立准入申請','這是設定入口，不是已批准紀錄。'],[47,44,'條件與範圍','階段、用途、固定基線與責任意見一起決定准入，不能只看單一通過字樣。']]),
 dict(key='assets',label='交付資產',img='assets.jpg',title='把接手需要的依據整理好',action='認識交付資產入口，以及規則、權限與評測紀錄的版本和使用限制。',result='實拍時列表沒有交付包；這不影響本頁已產出的教學影片，兩者是不同交付物。',chips=['交接入口','使用限制','當時列表為空'],animation='s12',animLabel='動畫：讓下一個人接得住',spots=[[7,49,'資產功能入口','正式應用中的交付資產，與本頁影片或 HTML 的教材交付不同。'],[51,45,'交付清單狀態','空白只代表拍攝快照中沒有對應交付包，不能把空清單寫成已交接成功。']]),
 dict(key='governance',label='權限與審計',img='governance.jpg',title='看誰能做什麼、依據是什麼',action='查看角色、對象、用途與動作限制，再認識關鍵操作的審計紀錄。',result='不同角色可能看到不同功能；資訊科或管理角色不會因職稱就取得全部病歷權限。',chips=['身份與對象','用途與動作','關鍵操作留痕'],animation='s10',animLabel='動畫：繼續不等於同意',spots=[[7,56,'權限治理入口','實拍可能使用不同授權帳號，不暗示一個帳號擁有全部功能。'],[52,45,'授權與審計資訊','權限決定能做什麼；審計保留操作依據。恢復執行本身不能授權或代簽。']]),
 dict(key='operations',label='運行狀態',img='operations.jpg',title='分清資源存在與能力可用',action='查看服務、模型與資源資訊，再回頭核對目前階段是否允許使用。',result='拍攝當時模型停用；歷史權重中繼資料或檔案存在不代表模型正在運行。本輪沒有重新啟動服務。',chips=['服務與資源','拍攝時模型停用','非即時監控'],animation='s10',animLabel='動畫：中斷後如何恢復',spots=[[50,34,'服務與資源狀態','這是歷史截圖，不是本頁對正式系統的即時監控。'],[53,61,'能力限制','模型端點、資源準備與階段授權是不同條件；檔案存在不能代替運行驗證。']]),
]
for s in steps:
    s['generalTime']=gt[s['key']];s['animationTime']=at[s['animation']]
# Percentage coordinates were checked against the actual captured screenshots.
coords={'dashboard':[[7,21],[46,40],[70,53]],'sources':[[23,15],[48,45]],'rules':[[23,15],[64,43]],'graph':[[23,15],[53,49],[88,44]],'release':[[43,32],[47,44]],'assets':[[23,15],[55,63]],'governance':[[23,15],[53,60]]}
for s in steps:
    for i,xy in enumerate(coords.get(s['key'],[])):s['spots'][i][:2]=xy


motion_mapping={'dashboard': (0, '記載差異與待複核疑點'), 'sources': (6, '來源、時間與版本'), 'rules': (18, '規則與模型的限定範圍'), 'case': (33, '回查原文與人工複核'), 'graph': (None, ''), 'evaluation': (None, ''), 'release': (86, '正式使用前的准入邊界'), 'assets': (None, ''), 'governance': (76, '人工責任與依權限簽署'), 'operations': (None, '')}
for st in steps:
    st['motionTime'],st['motionLabel']=motion_mapping[st['key']]
sync={'general': [], 'animation': [], 'motion': [{'start': 0, 'step': 'dashboard'}, {'start': 6, 'step': 'sources'}, {'start': 18, 'step': 'rules'}, {'start': 33, 'step': 'case'}, {'start': 47, 'step': 'case'}, {'start': 61, 'step': 'case'}, {'start': 76, 'step': 'governance'}, {'start': 86, 'step': 'release'}]}
sync['general']=[dict(start=c['start'],step=c['id'] if c['id'] in {s['key'] for s in steps} else None) for c in chapters]
animation_steps=['dashboard','sources','case','graph','rules','case','case','case','governance','operations','evaluation','assets']
sync['animation']=[dict(start=s['startFrame']/timeline['fps'],step=animation_steps[i]) for i,s in enumerate(timeline['scenes'])]

films={
 'general':dict(label='一般版｜全功能介面路演',short='一般版',duration=137.15,poster='general-poster.jpg',file='general-embed.mp4',description='2 分 17 秒・九個功能區＋病例原文・介面快照',boundary='工程合成資料的既有介面實拍；設定表單未提交，沒有執行整改、重核或簽字。拍攝時模型停用。',voice='Gemini 3.8 Flash-Lite TTS／Kore（依原製作紀錄）',chapters=[dict(start=c['start'],title=c['title'],id=c['id']) for c in chapters]),
 'animation':dict(label='動畫版｜這一筆，先別急著蓋章',short='動畫版',duration=timeline['durationSeconds'],poster='animation-poster.jpg',file='animation-embed.mp4',description='3 分 37.9 秒・手繪墨線＋淡彩・證據與人工責任故事',boundary='人物、文書差異、修訂及簽字均為合成教學示意，不是正式系統操作錄影或臨床驗收。',voice='Gemini 3.8 Flash TTS／Kore',chapters=[dict(start=s['startFrame']/timeline['fps'],title=s['title'],id=s['id']) for s in timeline['scenes']])
}

films={'motion':dict(label='90 秒精華版｜每個疑點，都有來處',short='90 秒精華版',duration=90,poster='motion-poster.jpg',file='motion-embed.mp4',description='1 分 30 秒・Kore 女聲・證據、複核與責任主線',boundary='合成教學流程視覺化，包含修訂與依權限簽署示意；不是正式應用操作錄影。正式使用仍需專家評測與醫院准入。',voice='Gemini 3.8 Flash-Lite TTS／Kore',chapters=[dict(start=s['start'],title=s['title'],id=s['id']) for s in motion_timeline['scenes']]),**films}

(WORK/'tour-data.json').write_text(json.dumps({'films':films,'steps':steps,'sync':sync},ensure_ascii=False,indent=2),encoding='utf-8')

CSS=r'''
/* Added dual-video guide. tabs/hotspots/lightbox adapted and scoped from project-intro-pack. */
header{overflow:hidden}header nav{overflow-x:auto;scrollbar-width:thin}header nav>a{flex-shrink:0}#ip-arch-watch{grid-column:1/-1;justify-self:start;font-size:13px}
.ip{--surface:#fffef9;--soft:#e8f0e8;--accent:#225b4c;--mute:#536b63}
.ip .video-tabs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:18px}.ip .video-tabs button{text-align:left;padding:18px 22px;border-radius:17px}.ip .video-tabs b{display:block;font-size:19px}.ip .video-tabs span{display:block;font-size:12px;opacity:.85;margin-top:3px}.ip .video-tabs [aria-selected=true]{background:var(--green);color:white;border-color:var(--green)}
.ip .film-card{border:1px solid var(--line);background:var(--surface);border-radius:24px;overflow:hidden}.ip .film-bar{padding:16px 22px;display:flex;gap:14px;justify-content:space-between;align-items:center}.ip .film-bar strong{font-size:16px}.ip .film-bar span{font-size:12px;color:var(--mute)}.ip video{display:block;width:100%;aspect-ratio:16/9;background:#183e38}.ip .film-status{padding:12px 20px;font-size:13px;background:#edf1e9}.ip .chapters{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:17px}.ip .chip{text-align:left;padding:10px 12px;font-size:13px;display:flex;gap:10px;align-items:start}.ip .chip i{font:600 12px/1.8 Consolas,monospace;color:#987029;font-style:normal;white-space:nowrap}.ip .chip.on{background:#e1eee2;border-color:#65876d}.ip .chip.on i{color:#2f6e51}.ip .film-footnote{font-size:13px;color:var(--mute);margin:15px 0 0}.ip .film-footnote b{color:#80582b}.ip .steps{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:22px}.ip .step{text-align:left;padding:12px;min-height:82px}.ip .step b{display:block;font:600 12px/1.8 Consolas,monospace;color:var(--mute)}.ip .step span{font-size:14px;font-weight:650}.ip .step[aria-selected=true]{background:var(--green);color:white;border-color:var(--green)}.ip .step[aria-selected=true] b{color:#d6e7d9}
.ip .walk-layout{display:grid;grid-template-columns:minmax(0,1fr) 270px;gap:20px;align-items:start}.ip .fig{position:relative;border:1px solid var(--line);border-radius:16px;background:white;overflow:hidden}.ip .fig img{width:100%;height:auto;display:block}.ip .zoom{position:absolute;right:10px;bottom:10px;padding:6px 12px;border-radius:20px;font-size:12px;background:#ffffffed;box-shadow:0 2px 9px #0002}.ip .hs{position:absolute;display:flex;align-items:center;justify-content:center;width:32px;height:32px;margin:-16px 0 0 -16px;padding:0;border:3px solid white;border-radius:50%;background:#b87932;color:white;box-shadow:0 2px 7px #0004;font-size:13px;font-weight:700}.ip .hs[aria-pressed=true]{background:#225b4c;outline:3px solid #d6e5ca}.ip .note{padding:16px 18px;border-radius:14px;border:1px solid var(--line);background:var(--soft);margin-top:12px;min-height:93px}.ip .note b{display:block;font-size:16px}.ip .note span{font-size:13px;color:var(--mute)}.ip .walk-copy h3{margin:2px 0 14px;font-size:23px}.ip .walk-copy p{font-size:14px;color:var(--mute);margin:7px 0 16px}.ip .copy-label{font:650 11px/1.6 'Segoe UI',sans-serif;letter-spacing:.09em;color:#37664d}.ip .tags{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:20px}.ip .tag{font-size:11px;background:#e8eee3;padding:4px 9px;border-radius:20px}.ip .watch-buttons{display:grid;gap:8px}.ip .watch-buttons button{text-align:left;font-size:12px;padding:10px 12px}.ip .walk-controls{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:20px}.ip .follow{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--mute)}.ip .follow input{accent-color:#225b4c;width:17px;height:17px}.ip .facts-pair{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:24px}.ip .fact-pane{border:1px solid var(--line);border-radius:20px;padding:22px;background:#fffef9}.ip .fact-pane.warn{background:#f4ecdf}.ip .fact-pane h3{font-size:20px}.ip .fact-pane li{font-size:13px;margin:11px 0;color:var(--mute)}.ip .fact-pane ul{padding-left:19px;margin-bottom:0}.ip .fact-pane code{font-size:11px;overflow-wrap:anywhere;display:block;color:#637b69;margin-top:4px}.source-title{font-weight:600}.sources code{display:block;font-size:10px;overflow-wrap:anywhere;color:#6d8275}.ip .dict{display:grid;grid-template-columns:1fr 1fr;gap:8px}.ip .dict details{margin:0;border:1px solid var(--line);border-radius:12px;padding:12px 16px}.ip .dict summary{font-size:14px}.ip .dict p{font-size:13px;color:var(--mute)}
#ip-lightbox{border:0;padding:0;border-radius:15px;max-width:96vw;width:1500px;max-height:94vh;color:#183e38;background:#f7f6f0}#ip-lightbox::backdrop{background:#0d221fe8}#ip-lightbox .lb-tools{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:12px 16px;border-bottom:1px solid var(--line)}#ip-lightbox .lb-tools span{margin-right:auto;font-size:13px}#ip-lightbox button{font-size:12px;padding:7px 12px}#ip-lightbox .zoom-viewport{overflow:auto;max-height:78vh;padding:12px}#ip-lbimg{display:block;width:100%;max-width:none;height:auto}#ip-lightbox.actual #ip-lbimg{width:auto;max-width:none}#ip-lightbox .lb-hint{font-size:12px;padding:8px 16px;color:#536b63;margin:0}
@media(max-width:900px){.ip .walk-layout{grid-template-columns:1fr}.ip .walk-copy{display:grid;grid-template-columns:1fr 1fr;gap:0 20px}.ip .walk-copy h3,.ip .tags,.ip .watch-buttons{grid-column:1/-1}.ip .watch-buttons{grid-template-columns:1fr 1fr}.ip .walk-copy h3{font-size:22px}.ip .chapters{grid-template-columns:1fr 1fr}.ip .steps{grid-template-columns:repeat(5,1fr)}.ip .step{padding:10px 7px}.ip .step span{font-size:12px}}
@media(max-width:600px){.ip .video-tabs{gap:8px;grid-template-columns:1fr}.ip .video-tabs button{min-width:0}.ip .video-tabs [data-film="motion"]{border-width:2px}.ip .video-tabs button{padding:13px 12px}.ip .video-tabs b{font-size:16px}.ip .video-tabs span{font-size:10px}.ip .film-bar{display:block;padding:12px 15px}.ip .film-bar span{display:block;margin-top:3px}.ip .chapters{gap:7px}.ip .chip{font-size:11px;padding:9px;gap:6px}.ip .chip i{font-size:10px}.ip .steps{grid-template-columns:1fr 1fr;gap:7px}.ip .step{min-height:60px;padding:9px 12px}.ip .step span{font-size:13px}.ip .step b{font-size:10px}.ip .walk-layout{gap:16px}.ip .walk-copy{display:block}.ip .watch-buttons{grid-template-columns:1fr}.ip .hs{width:29px;height:29px;margin:-14.5px 0 0 -14.5px;font-size:11px}.ip .facts-pair,.ip .dict{grid-template-columns:1fr}.ip .walk-controls button{font-size:12px}.ip .follow{width:100%;order:3}.ip .fig{border-radius:12px}.ip .note{padding:13px 15px}#ip-lightbox{width:96vw}#ip-lightbox .lb-tools{gap:7px}#ip-lightbox .lb-tools span{width:100%}.ip .facts-pair{gap:12px}.ip .fact-pane{padding:18px}}
@media(max-width:760px){header nav{gap:12px}header nav .brand{min-width:145px}}
'''

SECTION=r'''
<section class="ip" id="video-demo"><div class="section-head"><div><span class="eyebrow">WATCH / 三種視角，同一條主線</span><h2>先用 90 秒看懂，<br>再逐步深入。</h2></div><p>90 秒精華版：掌握證據與責任主線。<br>一般版看實際介面，動畫版看完整職場故事。</p></div>
<div class="video-tabs" role="tablist" aria-label="影片版本"><button id="ip-tab-motion" role="tab" aria-selected="true" aria-controls="ip-film-panel" tabindex="0" data-film="motion"><b>90 秒精華版</b><span>每個疑點，都有來處 · 1:30</span></button><button id="ip-tab-general" role="tab" aria-selected="false" aria-controls="ip-film-panel" tabindex="-1" data-film="general"><b>一般版</b><span>介面全功能路演 · 2:17</span></button><button id="ip-tab-animation" role="tab" aria-selected="false" aria-controls="ip-film-panel" tabindex="-1" data-film="animation"><b>動畫版</b><span>溫暖職場故事 · 3:37.9</span></button></div>
<div class="film-card" id="ip-film-panel" role="tabpanel" aria-labelledby="ip-tab-motion"><div class="film-bar"><strong id="ip-film-title">90 秒精華版｜每個疑點，都有來處</strong><span id="ip-film-meta">九個功能區＋病例原文・介面快照</span></div><video id="ip-video" controls playsinline preload="metadata" poster="assets/img/motion-poster.jpg" aria-label="專案演示影片"></video><div class="film-status" id="ip-film-status" role="status">影片載入中…</div></div>
<div id="ip-chapters" class="chapters" aria-label="影片章節"></div><p class="film-footnote"><b>先知道：</b><span id="ip-film-boundary"></span></p><p class="film-footnote" id="ip-voice"></p>
</section>
<section class="ip" id="walkthrough"><div class="section-head"><div><span class="eyebrow">TRY / 九個功能區＋病例原文</span><h2>照著畫面，<br>一步一步走過每一站。</h2></div><p>選步驟 → 點圖上圓點 → 放大核對。<br>也可以直接跳回影片的對應段落。</p></div>
<div id="ip-steps" class="steps" role="tablist" aria-label="詳細演示步驟"></div><div class="walk-layout"><div id="ip-shot"></div><div class="walk-copy" id="ip-walk-copy"></div></div>
<div class="walk-controls"><button type="button" id="ip-prev">← 上一步</button><label class="follow"><input type="checkbox" id="ip-follow">目前影片播放時，同步切換相關演示步驟</label><button type="button" id="ip-next">下一步 →</button></div><p class="caption" id="ip-sync-note" aria-live="polite">可選擇讓演示步驟跟隨目前影片；教學短片僅提供相關概念對照。</p><p class="caption">這裡是既有介面截圖的教材導覽；點選不會對正式系統提交資料、執行模型或產生簽字。</p>
</section>
<section class="ip" id="evidence-status"><span class="eyebrow">BOUNDARIES / 畫面看到了什麼</span><h2>看見介面，<br>也看見它的邊界。</h2><div class="facts-pair"><article class="fact-pane"><h3>已確認的事實</h3><ul><li>90 秒精華版為 90 秒／8 章；一般版為 137.15 秒／12 章；動畫版為 217.867 秒／12 章。章節取自各自的實際時間軸。<code>三版各自的 chapters.json／timeline.json；本輪媒體規格核對</code></li><li>應用左側定義九個功能入口；病例詳情隸屬工作臺旅程。<code>MedicalQualityCase-Windows/MedicalQuality/frontend/src/App.tsx：nav</code></li><li>一般版使用工程合成資料的介面截圖；動畫版與 90 秒精華版為合成教學故事或流程示意。<code>一般版 DELIVERY.md；動畫版 script.md、review.md</code></li><li>三版影片、海報與截圖均內嵌於本頁，核心導覽可離線使用。<code>本輪資產清單與獨立單檔驗證</code></li></ul></article><article class="fact-pane warn"><h3>觀察／待確認</h3><ul><li>一般版拍攝當時模型停用；本頁不是即時運行監控，本輪沒有重新啟動應用。</li><li>評測與准入只展示設定入口，未提交；病例只展示既有候選與原文定位，沒有實拍整改、重核或簽字。</li><li>「交付資產當時為空」指應用中的資產清單，與本頁已完成的教學影片不同。</li><li>三版皆不構成臨床效果或醫院准入證據；本輪僅整合既有影片，未新增完整人工聽音或臨床驗收。</li></ul></article></div><details><summary>看畫面時會遇到的六個名詞</summary><div class="dict"><details><summary>候選疑點（Candidate）</summary><p>值得核對的文書差異；還不是專業定論。</p></details><details><summary>證據（Evidence）</summary><p>保留來源、版本與位置的內容，讓人回到原文。</p></details><details><summary>覆蓋（Coverage）</summary><p>這次讀到了哪些範圍；沒有讀到不能當作沒有問題。</p></details><details><summary>原判與仲裁</summary><p>先保存獨立意見，再處理分歧，不用仲裁覆蓋原判。</p></details><details><summary>准入（Release Gate）</summary><p>固定範圍與責任條件齊備，才討論可進入哪個階段。</p></details><details><summary>執行存檔（Checkpoint）</summary><p>記住工作做到哪一步；不替任何人批准或簽字。</p></details></div></details><p class="caption">以下保留原本的架構、證據情境與責任流程互動圖解，可接著探索。</p></section>
<dialog id="ip-lightbox" aria-labelledby="ip-lbtitle"><div class="lb-tools"><span id="ip-lbtitle">介面原圖</span><button type="button" id="ip-lbsize" aria-pressed="false">原尺寸放大</button><button type="button" id="ip-lbclose">關閉 ✕</button></div><div class="zoom-viewport" tabindex="0" aria-label="可捲動的放大介面"><img id="ip-lbimg" alt="放大介面截圖"></div><p class="lb-hint">原尺寸模式可上下、左右捲動；按 Esc 關閉，返回原步驟。</p></dialog>
'''

JS=r'''
/* Reused stepper / hotspot / chapter concepts from project-intro-pack, scoped to preserve existing ELI5 page. */
(()=>{'use strict';
const FILMS=@@FILMS@@,JR=@@STEPS@@;
const A='assets/img/';const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const vid=$('#ip-video'),chb=$('#ip-chapters'),fmt=s=>Math.floor(s/60)+':'+String(Math.floor(s%60)).padStart(2,'0');
let mode='motion',jsel=0,serial=0,ready=null,readyResolve=null,opener=null,metaHandler=null,seekSerial=0;
const saved=Object.fromEntries(Object.keys(FILMS).map(k=>[k,0])),urls={},SYNC=@@SYNC@@;
function blobUrl(key){if(urls[key])return urls[key];const el=document.getElementById('ip-data-'+key);if(!el)return FILMS[key].url;const bin=atob(el.textContent.trim()),bytes=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);return urls[key]=URL.createObjectURL(new Blob([bytes],{type:'video/mp4'}));}
function drawChapters(){chb.innerHTML='';FILMS[mode].chapters.forEach((c,i)=>{const b=document.createElement('button');b.type='button';b.className='chip';b.dataset.chapter=i;b.innerHTML=`<i>${fmt(c.start)}</i><span>${c.title}</span>`;b.onclick=()=>seekTo(mode,c.start,true);chb.appendChild(b);});}
function markChapter(){let k=0;FILMS[mode].chapters.forEach((c,i)=>{if(vid.currentTime>=c.start-.035)k=i});$$('.chip',chb).forEach((b,i)=>{b.classList.toggle('on',i===k);b.setAttribute('aria-current',i===k?'true':'false');});$('#ip-film-status').textContent=`${FILMS[mode].short} · ${fmt(vid.currentTime)} / ${fmt(FILMS[mode].duration)} · ${FILMS[mode].chapters[k].title}`;
if($('#ip-follow').checked){let cue=null;for(const c of SYNC[mode]){if(vid.currentTime>=c.start-.035)cue=c;else break;}const j=cue?JR.findIndex(s=>s.key===cue.step):-1;if(j>=0&&j!==jsel){jsel=j;drawJ(false);}$('#ip-sync-note').textContent=j>=0?`${FILMS[mode].short}：同步至「${JR[j].label}」${mode==='general'?'；介面快照導覽。':'；相關概念對照，非該功能的實際操作錄影。'}`:`${FILMS[mode].short}：目前段落沒有直接對應的功能步驟，保留你的選擇。`;}}
async function setMode(key){if(!FILMS[key])throw Error('Unknown film');if(mode===key&&vid.src){return await ready;}if(vid.readyState>=1)saved[mode]=vid.currentTime;vid.pause();if(metaHandler)vid.removeEventListener('loadedmetadata',metaHandler);if(readyResolve)readyResolve(false);mode=key;const ticket=++serial,f=FILMS[key];$$('[data-film]').forEach(b=>{const on=b.dataset.film===key;b.setAttribute('aria-selected',on);b.tabIndex=on?0:-1});$('#ip-film-panel').setAttribute('aria-labelledby','ip-tab-'+key);$('#ip-film-title').textContent=f.label;$('#ip-film-meta').textContent=f.description;$('#ip-film-boundary').textContent=f.boundary;$('#ip-voice').textContent='原片聲音：'+f.voice+'。沿用現有配音。';vid.poster=A+f.poster;$('#ip-film-status').textContent='影片載入中…';drawChapters();let resolve;const pending=ready=new Promise(r=>resolve=r);readyResolve=resolve;metaHandler=()=>{vid.removeEventListener('loadedmetadata',metaHandler);if(ticket!==serial){resolve(false);return;}vid.currentTime=Math.min(saved[key],Math.max(0,vid.duration-.1));markChapter();resolve(true);};vid.addEventListener('loadedmetadata',metaHandler);vid.src=blobUrl(key);vid.load();return await pending;}
async function seekTo(key,seconds,play=true){const operation=++seekSerial;if(!await setMode(key)||operation!==seekSerial||mode!==key)return;vid.currentTime=Math.max(0,Math.min(seconds,vid.duration-.05));markChapter();if(play){try{await vid.play()}catch(e){$('#ip-film-status').textContent='已定位章節；請按影片播放鍵。';}}vid.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});}
vid.addEventListener('timeupdate',markChapter);vid.addEventListener('seeked',markChapter);vid.addEventListener('error',()=>{$('#ip-film-status').textContent='影片未能載入，請使用 Chrome／Edge 開啟此單檔頁。';if(readyResolve)readyResolve();});
$$('[data-film]').forEach(b=>{b.onclick=()=>setMode(b.dataset.film);b.onkeydown=e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();const keys=Object.keys(FILMS),index=keys.indexOf(mode),key=e.key==='Home'?keys[0]:e.key==='End'?keys.at(-1):keys[(index+(e.key==='ArrowRight'?1:-1)+keys.length)%keys.length];setMode(key);$('[data-film="'+key+'"]').focus();}};});
function hotspotBlock(el,img,alt,spots,intro){el.innerHTML=`<div class="fig shot"><img src="${A+img}" alt="${alt}">${spots.map((s,i)=>`<button type="button" class="hs" style="left:${s[0]}%;top:${s[1]}%" data-i="${i}" aria-pressed="false" aria-label="${s[2]}">${i+1}</button>`).join('')}<button type="button" class="zoom" data-zoom>放大介面 ↗</button></div><div class="note" aria-live="polite"><b>${intro[0]}</b><span>${intro[1]}</span></div>`;
 $$('.hs',el).forEach(h=>h.onclick=()=>{const s=spots[+h.dataset.i];$$('.hs',el).forEach(x=>x.setAttribute('aria-pressed',String(x===h)));$('.note',el).innerHTML=`<b>${+h.dataset.i+1}. ${s[2]}</b><span>${s[3]}</span>`;});}
function drawJ(focus=false){const st=$('#ip-steps');st.innerHTML='';JR.forEach((j,i)=>{const b=document.createElement('button');b.type='button';b.className='step';b.setAttribute('role','tab');b.setAttribute('aria-selected',i===jsel);b.setAttribute('aria-controls','ip-shot');b.tabIndex=i===jsel?0:-1;b.dataset.step=i;b.innerHTML=`<b>${String(i+1).padStart(2,'0')}</b><span>${j.label}</span>`;b.onclick=()=>{jsel=i;drawJ(true);};b.onkeydown=e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();jsel=e.key==='Home'?0:e.key==='End'?JR.length-1:(i+(e.key==='ArrowRight'?1:-1)+JR.length)%JR.length;drawJ(true);}};st.appendChild(b);});const j=JR[jsel];hotspotBlock($('#ip-shot'),j.img,'2026-10-31 工程合成資料介面截圖：'+j.title,j.spots,['點圖上編號看重點','這是靜態介面導覽，不會送出真實操作。']);$('#ip-walk-copy').innerHTML=`<div class="tags">${j.chips.map(c=>`<span class="tag">${c}</span>`).join('')}</div><h3>${j.title}</h3><div><span class="copy-label">這一步做什麼</span><p>${j.action}</p></div><div><span class="copy-label">結果與界線</span><p>${j.result}</p></div><div class="watch-buttons"><button type="button" id="ip-watch-general">▶ 一般版看這段 · ${fmt(j.generalTime)}</button><button type="button" id="ip-watch-animation">▶ ${j.animLabel} · ${fmt(j.animationTime)}</button><button type="button" id="ip-watch-motion" ${j.motionTime===null?'disabled':''}>${j.motionTime===null?'90 秒精華版未涵蓋此功能':'▶ 精華版：'+j.motionLabel+' · '+fmt(j.motionTime)+'（概念對照）'}</button></div>`;$('#ip-watch-general').onclick=()=>seekTo('general',j.generalTime);$('#ip-watch-animation').onclick=()=>seekTo('animation',j.animationTime);$('#ip-watch-motion').onclick=()=>{if(j.motionTime!==null)seekTo('motion',j.motionTime);};$('#ip-prev').disabled=jsel===0;$('#ip-next').disabled=jsel===JR.length-1;if(focus)$('[data-step="'+jsel+'"]').focus();}
$('#ip-prev').onclick=()=>{jsel=Math.max(0,jsel-1);drawJ();};$('#ip-next').onclick=()=>{jsel=Math.min(JR.length-1,jsel+1);drawJ();};
const lb=$('#ip-lightbox');document.addEventListener('click',e=>{const z=e.target.closest('#ip-shot [data-zoom]');if(z){opener=z;const im=z.parentElement.querySelector('img');$('#ip-lbimg').src=im.src;$('#ip-lbimg').alt=im.alt;$('#ip-lbtitle').textContent=JR[jsel].label+'｜介面截圖';lb.classList.remove('actual');$('#ip-lbsize').setAttribute('aria-pressed','false');$('#ip-lbsize').textContent='原尺寸放大';vid.pause();lb.showModal();}});$('#ip-lbclose').onclick=()=>lb.close();lb.addEventListener('click',e=>{if(e.target===lb)lb.close();});lb.addEventListener('close',()=>{if(opener?.isConnected)opener.focus();});$('#ip-lbsize').onclick=()=>{const actual=lb.classList.toggle('actual');$('#ip-lbsize').setAttribute('aria-pressed',actual);$('#ip-lbsize').textContent=actual?'適合視窗':'原尺寸放大';};
// Bridge original architecture buttons to a relevant filmed or animated explanation.
const archMap={ui:['general',gtSafe('dashboard')],api:['animation',@@ARCHTIME@@],db:['animation',@@ARCHTIME@@],worker:['animation',@@ARCHTIME@@],flow:['animation',@@ARCHTIME@@],model:['animation',@@MODELTIME@@]};function gtSafe(id){return FILMS.general.chapters.find(c=>c.id===id).start;}
const bridge=document.createElement('button');bridge.type='button';bridge.id='ip-arch-watch';bridge.textContent='▶ 一般版看工作臺';const dock=$('#architecture .detail');if(dock){dock.appendChild(bridge);bridge.onclick=()=>seekTo(...archMap.ui);$$('[data-node]').forEach(b=>b.addEventListener('click',()=>{const [m,time]=archMap[b.dataset.node];bridge.textContent='▶ '+FILMS[m].short+'看這個環節 · '+fmt(time);bridge.onclick=()=>seekTo(m,time);}));}
$('#ip-follow').addEventListener('change',()=>{if($('#ip-follow').checked)markChapter();else $('#ip-sync-note').textContent='播放跟隨已關閉；手動選擇演示步驟不會被影片改變。';});
const motionBridge=document.createElement('button');motionBridge.type='button';motionBridge.id='ip-arch-motion';motionBridge.textContent='▶ 90 秒精華版：原文回查 · 0:33';if(dock){dock.appendChild(motionBridge);motionBridge.onclick=()=>seekTo('motion',33);$$('[data-node]').forEach(b=>b.addEventListener('click',()=>{const t={ui:33,model:18}[b.dataset.node];motionBridge.disabled=t===undefined;motionBridge.textContent=t===undefined?'90 秒精華版未解說此架構零件':'▶ 90 秒精華版：'+(b.dataset.node==='ui'?'原文回查':'有限候選與證據')+' · '+fmt(t);motionBridge.onclick=()=>{if(t!==undefined)seekTo('motion',t);};}));}
window.__introPack={sync:SYNC,get mode(){return mode},get step(){return jsel},films:FILMS,steps:JR,setMode,seekTo};drawJ();setMode('motion');
})();
'''

for k,val in {'FILMS':json.dumps(films,ensure_ascii=False),'STEPS':json.dumps(steps,ensure_ascii=False),'ARCHTIME':str(at['s04']),'MODELTIME':str(at['s05']),'SYNC':json.dumps(sync,ensure_ascii=False)}.items():JS=JS.replace('@@'+k+'@@',val)

page=BACKUP.read_text(encoding='utf-8')
page=page.replace('<title>一份病歷的通關之旅｜醫療病歷質控架構圖解</title>','<title>FF - 醫療病歷質控｜三版影片與詳細互動演示</title>')
page=page.replace('</style>',CSS+'\n</style>',1)
page=page.replace('<section id="architecture">',SECTION+'\n<section id="architecture">',1)
page=page.replace('<a href="#architecture">看架構</a>','<a href="#video-demo">看影片</a><a href="#walkthrough">逐步演示</a><a href="#architecture">看架構</a>',1)
page=page.replace('href="#architecture">跟著一份病歷出發 ↓','href="#video-demo">看影片，開始逐步演示 ↓',1)
page=page.replace('從零開始 · 離線互動圖解','從零開始 · 三版影片＋互動圖解',1)
page=page.replace('本頁不提供診斷、治療或法規判斷。','本頁不提供診斷、治療或法規判斷。新增一般版取自 Windows 工程副本的既有拍攝成果；本輪沒有重新啟動正式應用。')
# Preserve readable provenance while avoiding file dependencies in the portable document.
def source_ref(m):
    ref,title=m.group(1),m.group(2)
    return '<span class="source-title">'+title+'</span><code>'+ref.removeprefix('../')+'</code>'
page=re.sub(r'<a href="(\.\./[^"]+)">([^<]+)</a>',source_ref,page)
page=page.replace('來源連結需保留本頁與原資料包的相對位置。','來源路徑保留供回查；核心影片、圖片與互動不依賴原資料包。')
page=page.replace('</body>','<script>'+JS+'</script>\n</body>')
(OUT/'guide.src.html').write_text(page,encoding='utf-8')
imgs={p.name:'data:image/jpeg;base64,'+base64.b64encode(p.read_bytes()).decode() for p in (OUT/'assets/img').glob('*.jpg')}
standalone=page
for name,uri in imgs.items():standalone=standalone.replace('assets/img/'+name,uri)
standalone=standalone.replace("const A='assets/img/';",'const IMGS='+json.dumps(imgs)+';')
standalone=standalone.replace('${A+img}','${IMGS[img]}').replace('vid.poster=A+f.poster;','vid.poster=IMGS[f.poster];')
# In authoring source only, use adjacent media. Portable output uses lazy Blob URLs.
source=page.replace("return FILMS[key].url;","return 'assets/'+FILMS[key].file;")
(OUT/'guide.src.html').write_text(source,encoding='utf-8')
payload=''
for key,f in films.items():
    p=OUT/'assets'/f['file'];payload+=f'<script id="ip-data-{key}" type="application/octet-stream">'+base64.b64encode(p.read_bytes()).decode()+'</script>\n'
standalone=standalone.replace('<script>\n/* Reused stepper',payload+'<script>\n/* Reused stepper')
assert all('ip-data-'+key in standalone for key in films)
assert 'assets/img/' not in standalone and '${A+' not in standalone
(OUT/'醫療病歷質控_三版影片互動導覽.html').write_text(standalone,encoding='utf-8')
shutil.copy2(OUT/'醫療病歷質控_三版影片互動導覽.html',ORIGINAL)
shutil.copy2(OUT/'醫療病歷質控_三版影片互動導覽.html',WORK/'醫療病歷質控_三版影片互動導覽.html')
manifest=[]
for key,f in films.items():
    raw=GENERAL/'醫療病歷質控_全功能路演_Kore.mp4' if key=='general' else ANIMATION/'final.mp4' if key=='animation' else MOTION/'out/每個疑點都有來處_90秒完整版_Kore.mp4'
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,size:stream=codec_name,width,height,avg_frame_rate','-of','json',str(raw)]))
    manifest.append({'kind':key,'source':str(raw),'sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'probe':info,'embedded_file':f['file']})
(WORK/'media-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'portable_html':str(OUT/'醫療病歷質控_三版影片互動導覽.html'),'bytes':len(standalone.encode()),'films':len(films),'chapters':[len(f['chapters']) for f in films.values()],'tour_steps':len(steps),'embedded_images':len(imgs),'original_page_updated':True},ensure_ascii=False))

legacy_work=ROOT/'specs/research/2026-10-31-medical-dual-video'
legacy_out=Path('C:\\Users\\jamic\\.codex\\visualizations\\2026\\10\\31\\01a18f5d-7c8e-79b1-8a4f-61dd0291ace2\\medical-dual-guide')
for target in [legacy_work/'醫療病歷質控_雙版影片互動導覽.html',legacy_out/'醫療病歷質控_雙版影片互動導覽.html']:
    shutil.copy2(OUT/'醫療病歷質控_三版影片互動導覽.html',target)
shutil.copy2(OUT/'assets/motion-embed.mp4',legacy_out/'assets/motion-embed.mp4')
shutil.copy2(OUT/'assets/img/motion-poster.jpg',legacy_out/'assets/img/motion-poster.jpg')
shutil.copy2(OUT/'guide.src.html',legacy_out/'guide.src.html')
for name in ['tour-data.json','media-manifest.json']:
    shutil.copy2(WORK/name,legacy_work/name)
