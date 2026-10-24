from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];v=(ROOT/'VERSION').read_text().strip();(ROOT/'build').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def evidence(name,sources,outputs):
 (ROOT/'build'/name).write_text(json.dumps({'version':v,'sources':{p:sha(p) for p in sources},'outputs':{p:sha(p) for p in outputs}},ensure_ascii=False,indent=2),encoding='utf-8')
html=(ROOT/'原型/index.html').read_text(encoding='utf-8').replace('<link rel="stylesheet" href="style.css">','<style>'+(ROOT/'原型/style.css').read_text(encoding='utf-8')+'</style>').replace('<script src="prototype.js"></script>','<script>'+(ROOT/'原型/prototype.js').read_text(encoding='utf-8')+'</script>')
(ROOT/'拾史桌面端V1_交互原型.html').write_text(html,encoding='utf-8')
evidence('offline.json',['原型/index.html','原型/style.css','原型/prototype.js','tools/build_delivery_assets.py'],['拾史桌面端V1_交互原型.html'])
shots=sorted((ROOT/'原型图').glob('[0-9]*.png'))
canvas=Image.new('RGB',(1550,3380),'#f5f4ef');draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21)
draw.text((28,20),'拾史  桌面端 v'+v+'  页面总览',font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',32),fill='#234935')
for i,p in enumerate(shots):
 x=28+(i%2)*770;y=86+(i//2)*650;draw.text((x,y),p.stem.replace('-','  ',1),font=font,fill='#34533e');im=Image.open(p).convert('RGB');im.thumbnail((735,610));canvas.paste(im,(x,y+35))
canvas.save(ROOT/'页面总览.png')
evidence('overview.json',[p.relative_to(ROOT).as_posix() for p in shots]+['tools/build_delivery_assets.py'],['页面总览.png'])
evidence('contracts.json',['tools/build_contracts.py','拾史桌面端V1_PRD.md','VERSION'],['contracts/core.schema.json','contracts/openapi.json','需求追踪.json'])
print('offline, overview and contract provenance generated')
