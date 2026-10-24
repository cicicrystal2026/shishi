from pathlib import Path
import json, html, hashlib
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'技术架构/architecture.json'
d=json.loads(source.read_text(encoding='utf-8'))
assert d['version']==(ROOT/'VERSION').read_text().strip()
W,H=2200,1610
im=Image.new('RGB',(W,H),'#F5F6F1');draw=ImageDraw.Draw(im)
fontpath='C:/Windows/Fonts/msyh.ttc'
fonts={s:ImageFont.truetype(fontpath,s) for s in [19,21,23,24,26,31,48]}
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',f'<title>{d["title"]} v{d["version"]}</title>','<desc>与 PRD F01 至 F42 同步的桌面端设计架构，模块化单体加 Worker。尚未实现正式应用。</desc>','<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#6B8871"/></marker></defs>','<rect width="2200" height="1610" fill="#F5F6F1"/>']
def rect(x,y,w,h,fill,stroke='#D9E2D4',r=15):
 draw.rounded_rectangle((x,y,x+w,y+h),radius=r,fill=fill,outline=stroke,width=2)
 svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
def text(x,y,t,size=24,fill='#334E3C'):
 draw.text((x,y),t,font=fonts[size],fill=fill)
 svg.append(f'<text x="{x}" y="{y+size}" font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{size}" fill="{fill}">{html.escape(t)}</text>')
text(80,42,d['title'],48,'#1B3F2E');text(1640,55,'DESKTOP / v'+d['version'],26,'#43684D')
text(80,110,'设计基线  ·  PRD F01–F42  ·  默认偏好驱动  ·  故事与成片两次内容审阅',24,'#6D8069')
rect(80,170,2040,140,'#EAF0E3')
text(105,183,'用户看到的页面',21,'#6B8060')
for i,p in enumerate(d['pages']):
 x=105+i*250;active=p['id'] in ['P04','P07']
 rect(x,226,230,58,'#2D5B40' if active else '#FFFFFF',stroke='#D5E0CE',r=9)
 text(x+14,239,p['id']+' '+p['label'],23,'#FFFFFF' if active else '#496B48')
for e in d['edges']:
 pts=[tuple(p) for p in e['points']];draw.line(pts,fill='#6B8871',width=3)
 (x1,y1),(x2,y2)=pts[-2:]
 if y2>y1:tri=[(x2,y2),(x2-7,y2-14),(x2+7,y2-14)]
 else:tri=[(x2,y2),(x2-14,y2-7),(x2-14,y2+7)]
 draw.polygon(tri,fill='#6B8871')
 svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+'" fill="none" stroke="#6B8871" stroke-width="3" marker-end="url(#arrow)"><title>'+html.escape(e['label'])+'</title></polyline>')
 if len(pts)==2 and x1==x2:text(x1+15,(y1+y2)//2-15,e['label'],19,'#78906C')
for m in d['modules']:
 x,y,w,h=[m[k] for k in ['x','y','w','h']]
 color={'entry':'#FFFFFF','core':'#EAF0E3','data':'#FFFFFF','output':'#EEF0E6'}[m['type']]
 rect(x,y,w,h,color)
 text(x+24,y+15,m['id']+'  '+m['name'],31,'#294E35')
 for j,line in enumerate(m['detail']):text(x+25,y+64+j*34,line,23,'#6A7F60')
text(1330,1250,'工具调用统一经过 T07 的费用与幂等检查',19,'#8C865B')
rect(80,1295,2040,185,'#203E2D',stroke='#203E2D')
text(105,1310,'部署与外部能力边界',26,'#E2EBD6')
items=[('单机持久化','SQLite + Job 表 + 受控文件目录'),('OpenAI 默认能力','GPT 编排 / 结构化输出 / 图片工具'),('声音与视频','TTS 需验证 · 视频接口条件启用'),('本地合成','时间线 JSON → FFmpeg → 交付包')]
for i,(a,b) in enumerate(items):
 x=110+i*500;text(x,1362,a,24,'#E4EBD8');text(x,1409,b,19,'#B3C7A7')
text(80,1510,'模块表示职责，不等于十个独立服务。浏览器离页可继续；主机服务停止需重启后恢复。',23,'#647B59')
text(80,1553,'图源 architecture.json  /  模型 ID 与依赖版本在接入时锁定  /  当前为设计，未执行付费任务',21,'#819071')
svg.append('</svg>')
out=ROOT/'技术架构';stem='技术架构图_v'+d['version']
(out/(stem+'.svg')).write_text('\n'.join(svg),encoding='utf-8');im.save(out/(stem+'.png'))
lines=['flowchart TD','  subgraph UI[桌面端页面]']
for p in d['pages']:lines.append(f'    {p["id"]}["{p["id"]} {p["label"]}"]')
lines+=['  end']
for m in d['modules']:lines.append(f'  {m["id"]}["{m["id"]} {m["name"]}"]')
lines+=['  UI --> T01']
for e in d['edges']:lines.append(f'  {e["from"]} -->|{e["label"]}| {e["to"]}')
lines+=['  T07 -.费用与幂等门槛.-> T05','  T05 --> EXT["OpenAI / OCR / TTS / 可选视频服务"]','  T09 --> FFM["FFmpeg"]']
(out/(stem+'.mmd')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
(out/'diagram_build.json').write_text(json.dumps({'version':d['version'],'source':'技术架构/architecture.json','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'generator':'tools/render_architecture.py'},ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'build').mkdir(exist_ok=True)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT/'build/architecture.json').write_text(json.dumps({'version':d['version'],'sources':{'技术架构/architecture.json':digest(source),'tools/render_architecture.py':digest(Path(__file__))},'outputs':{'技术架构/'+stem+ext:digest(out/(stem+ext)) for ext in ['.svg','.png','.mmd']}},ensure_ascii=False,indent=2),encoding='utf-8')
print('architecture SVG PNG Mermaid generated for v'+d['version'])
