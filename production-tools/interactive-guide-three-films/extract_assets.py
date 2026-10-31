"""Extract already-embedded viewing media from the portable guide, fully offline."""
from pathlib import Path
import argparse,base64,json,re
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--html',type=Path,default=Path('index.html'))
parser.add_argument('--out',type=Path,default=Path('extracted-assets'))
args=parser.parse_args();doc=args.html.read_text(encoding='utf-8-sig')
out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
films={}
for key,encoded in re.findall(r'<script id="ip-data-(motion|general|animation)" type="application/octet-stream">([^<]+)</script>',doc):
    raw=base64.b64decode(encoded.strip(),validate=True)
    target=out/(key+'.mp4');target.write_bytes(raw);films[key]=len(raw)
if set(films)!={'motion','general','animation'}:raise ValueError('Expected exactly three embedded films')
marker='const IMGS='
if marker not in doc:raise ValueError('Embedded image dictionary not found')
images,_=json.JSONDecoder().raw_decode(doc[doc.index(marker)+len(marker):])
image_dir=out/'images';image_dir.mkdir(exist_ok=True)
for name,uri in images.items():
    if Path(name).name!=name or not name.endswith('.jpg'):raise ValueError('Unsafe image filename')
    if not uri.startswith('data:image/jpeg;base64,'):raise ValueError('Unexpected image type')
    (image_dir/name).write_bytes(base64.b64decode(uri.split(',',1)[1],validate=True))
print(json.dumps({'films':films,'images':len(images),'out':str(out)},ensure_ascii=False))
