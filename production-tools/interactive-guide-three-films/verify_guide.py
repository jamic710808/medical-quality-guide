from pathlib import Path
from html.parser import HTMLParser
import base64,hashlib,json,subprocess
WORK=Path(__file__).resolve().parent
ROOT=WORK.parents[2]
OUT=Path('C:/Users/jamic/.codex/visualizations/2026/10/31/01a18fc0-0876-7220-b07f-83c457684060/medical-triple-guide')
class Parser(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.resources=[];self.anchors=[];self.scripts=[];self.kind=None;self.content=[];self.videos={};self.scriptid=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag in ['img','video','source','script','link']:
            self.resources.extend(a[k] for k in ['src','poster','href'] if k in a)
        if tag=='a' and a.get('href','').startswith('#'):self.anchors.append(a['href'][1:])
        if tag=='script':self.kind=a.get('type','text/javascript');self.scriptid=a.get('id');self.content=[]
    def handle_endtag(self,tag):
        if tag=='script':
            data=''.join(self.content)
            if self.kind=='application/octet-stream':self.videos[self.scriptid]=data
            elif self.kind not in ['application/json','text/plain']:self.scripts.append(data)
            self.kind=None;self.content=[]
    def handle_data(self,data):
        if self.kind:self.content.append(data)
page=OUT/'醫療病歷質控_三版影片互動導覽.html'
doc=page.read_text(encoding='utf-8');p=Parser();p.feed(doc);p.close()
assert len(p.ids)==len(set(p.ids)),'Duplicate IDs'
assert all(a in p.ids for a in p.anchors),'Unresolved anchor'
assert all(r.startswith('data:') for r in p.resources),'External runtime resource'
assert 'assets/img/' not in doc and '@@' not in doc,'Unresolved source placeholder'
assert set(p.videos)=={'ip-data-motion','ip-data-general','ip-data-animation'}
assert len(p.scripts)==2
for i,s in enumerate(p.scripts):
    path=OUT/f'validate-script-{i}.js';path.write_text(s,encoding='utf-8');subprocess.run(['node','--check',str(path)],check=True)
data=json.loads((WORK/'tour-data.json').read_text(encoding='utf-8'))
assert list(data['films'])==['motion','general','animation']
assert [len(v['chapters']) for v in data['films'].values()]==[8,12,12]
stepkeys={s['key'] for s in data['steps']}
embedded=[]
for key,f in data['films'].items():
    times=[c['start'] for c in f['chapters']]
    assert times==sorted(times) and all(0<=t<f['duration'] for t in times)
    cues=data['sync'][key]
    assert [c['start'] for c in cues]==sorted(c['start'] for c in cues)
    assert all(c['step'] in stepkeys or c['step'] is None for c in cues)
    raw=base64.b64decode(p.videos['ip-data-'+key],validate=True)
    digest=hashlib.sha256(raw).hexdigest()
    assert digest==hashlib.sha256((OUT/'assets'/f['file']).read_bytes()).hexdigest()
    embedded.append({'mode':key,'bytes':len(raw),'sha256':digest,'chapters':len(times)})
for st in data['steps']:assert st['motionTime'] is None or 0<=st['motionTime']<90
digest=hashlib.sha256(page.read_bytes()).hexdigest()
aliases=[ROOT/'架構圖解_20261031/醫療病歷質控_互動架構圖解.html',WORK/'醫療病歷質控_三版影片互動導覽.html',ROOT/'specs/research/2026-10-31-medical-dual-video/醫療病歷質控_雙版影片互動導覽.html',Path('C:/Users/jamic/.codex/visualizations/2026/10/31/01a18f5d-7c8e-79b1-8a4f-61dd0291ace2/medical-dual-guide/醫療病歷質控_雙版影片互動導覽.html')]
assert all(hashlib.sha256(a.read_bytes()).hexdigest()==digest for a in aliases),'Shared entry points differ'
result={'bytes':page.stat().st_size,'sha256':digest,'embedded_videos':embedded,'duplicate_ids':False,'anchors_valid':True,'all_runtime_resources_embedded':True,'executable_scripts':2,'javascript_syntax':'pass','chapter_total':32,'steps':10,'sync_maps_ordered':True,'shared_entry_points_identical':True}
(OUT/'static-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(WORK/'static-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='embedded_videos'},ensure_ascii=False))
