"""检查产品设计基线；不将文件一致性误称为语义或实现验收。"""
from pathlib import Path
import json, hashlib, re, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reqs():
 text=(ROOT/'拾史桌面端V1_PRD.md').read_text(encoding='utf-8')
 matches=re.findall(r'(F\d{2})：(.*?)(?=F\d{2}：|$)',text,re.M)
 if len(matches)!=len({m[0] for m in matches}):raise ValueError('duplicate requirement declarations')
 return {rid:t.strip() for rid,t in matches}
def controlled_files():
 files=[]
 for p in ROOT.rglob('*'):
  rel=p.relative_to(ROOT)
  if any(x in {'.git','releases','__pycache__','runtime','uploads','private','qa','tmp','node_modules'} for x in rel.parts):continue
  if not p.is_file() or p.name=='release_manifest.json':continue
  if p.name.startswith('.env') and p.name!='.env.example':raise ValueError('private env in controlled tree')
  files.append(rel.as_posix())
 return sorted(files)
def check():
 errors=[]
 try:
  v=(ROOT/'VERSION').read_text().strip();r=reqs()
  if not r or (v=='1.0' and set(r)!={'F'+str(i).zfill(2) for i in range(1,43)}):errors.append('baseline requirement coverage incomplete')
  trace=json.loads((ROOT/'需求追踪.json').read_text(encoding='utf-8'))
  arch=json.loads((ROOT/'技术架构/architecture.json').read_text(encoding='utf-8'))
  build=json.loads((ROOT/'技术架构/diagram_build.json').read_text(encoding='utf-8'))
  manifest=json.loads((ROOT/'release_manifest.json').read_text(encoding='utf-8'))
  for name,doc in [('trace',trace),('architecture',arch),('diagram',build),('manifest',manifest)]:
   if doc['version']!=v:errors.append('version mismatch: '+name)
  prd=(ROOT/'拾史桌面端V1_PRD.md').read_text(encoding='utf-8')
  if '版本 V'+v not in prd:errors.append('PRD header version mismatch')
  technical=(ROOT/'技术架构/技术架构说明.md').read_text(encoding='utf-8')
  if '版本 v'+v not in technical:errors.append('technical header version mismatch')
  spec=(ROOT/'拾史桌面端v1.0技术规格说明书.md').read_text(encoding='utf-8')
  if '版本 v'+v not in spec:errors.append('technical specification version mismatch')
  for rel in ['contracts/openapi.json','contracts/core.schema.json']:
   contract=json.loads((ROOT/rel).read_text(encoding='utf-8'))
   if contract.get('version',contract.get('info',{}).get('version'))!=v:errors.append('contract version mismatch: '+rel)
  proto=(ROOT/'原型/prototype.js').read_text(encoding='utf-8')
  if 'DESKTOP v'+v not in proto:errors.append('prototype version mismatch')
  mods={m['id'] for m in arch['modules']};pages={p['id'] for p in arch['pages']}|{'S01','S02'}
  items=trace['requirements'];ids=[x['id'] for x in items]
  if len(ids)!=len(set(ids)) or set(ids)!=set(r):errors.append('requirement set mismatch')
  for item in items:
   rid=item['id']
   if rid in r and item['text_sha256']!=hashlib.sha256(r[rid].encode()).hexdigest():errors.append('stale requirement: '+rid)
   if not item['pages'] or not set(item['pages'])<=pages:errors.append('invalid page map: '+rid)
   if not item['modules'] or not set(item['modules'])<=mods:errors.append('invalid module map: '+rid)
   if not item['acceptance'] or not item['implementation_status']:errors.append('missing acceptance/status: '+rid)
   if not (ROOT/item.get('technical_spec','missing')).is_file():errors.append('missing technical spec: '+rid)
  for p in arch['pages']:
   if p['route']+':' not in proto:errors.append('missing prototype route: '+p['route'])
  if build['source_sha256']!=sha(ROOT/build['source']):errors.append('architecture diagram source stale')
  evidence=list((ROOT/'build').glob('*.json'))
  required_evidence={'prd.json','technical-spec.json','architecture.json','prototype.json','offline.json','overview.json','contracts.json'}
  if not required_evidence <= {p.name for p in evidence}:errors.append('missing build provenance')
  for p in evidence:
   record=json.loads(p.read_text(encoding='utf-8'))
   if record['version']!=v:errors.append('build version mismatch: '+p.name)
   for section in ['sources','outputs']:
    for rel,digest in record[section].items():
     target=ROOT/rel
     if not target.is_file() or sha(target)!=digest:errors.append('stale derived asset: '+p.name+' / '+rel)
  files=controlled_files()
  if set(files)!=set(manifest['files']):errors.append('controlled file set changed')
  for rel,digest in manifest['files'].items():
   p=ROOT/rel
   if not p.is_file() or sha(p)!=digest:errors.append('file hash mismatch: '+rel)
 except Exception as e:errors.append(type(e).__name__+': '+str(e))
 if errors:
  print('FAIL: baseline is not synchronized')
  for e in errors:print(' - '+e.encode('ascii','backslashreplace').decode())
  return 1
 print('PASS: v'+v+' / '+str(len(r))+' requirements / '+str(len(files))+' controlled files')
 print('Design consistency only; implementation and semantic acceptance are separate.')
 return 0
if __name__=='__main__':sys.exit(check())
