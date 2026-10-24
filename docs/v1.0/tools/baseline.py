from pathlib import Path
import json, hashlib, sys, zipfile
from check_sync import ROOT,sha,controlled_files,check
def manifest():
 version=(ROOT/'VERSION').read_text().strip()
 if not __import__('re').fullmatch(r'\d+\.\d+(?:\.\d+)?',version):raise SystemExit('invalid version')
 if (ROOT/'releases'/('v'+version)).exists():raise SystemExit('version already frozen; choose a new version, never rewrite its manifest')
 files=controlled_files()
 data={'version':version,'baseline':'shishi-desktop-v'+version,'stage':'design_baseline','implementation_status':'not_implemented','files':{p:sha(ROOT/p) for p in files},'derived':{'拾史桌面端V1_PRD.docx':['拾史桌面端V1_PRD.md','tools/build_prd.py'],'技术架构/技术架构图_v'+version+'.png':['技术架构/architecture.json','tools/render_architecture.py'],'技术架构/技术架构图_v'+version+'.svg':['技术架构/architecture.json','tools/render_architecture.py'],'拾史桌面端V1_交互原型.html':['原型/index.html','原型/style.css','原型/prototype.js'],'原型图':['原型/index.html','原型/style.css','原型/prototype.js']}}
 (ROOT/'release_manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Manifest updated. This does not record semantic approval.')
def snapshot():
 if check():raise SystemExit('sync check must pass')
 version=(ROOT/'VERSION').read_text().strip();folder=ROOT/'releases'/('v'+version)
 if folder.exists():raise SystemExit('release directory exists; overwrite refused')
 folder.mkdir(parents=True)
 name='shishi-desktop-v'+version+'-design.zip';dest=folder/name
 m=json.loads((ROOT/'release_manifest.json').read_text(encoding='utf-8'))
 with zipfile.ZipFile(dest,'x',zipfile.ZIP_DEFLATED) as z:
  for rel in list(m['files'])+['release_manifest.json']:z.write(ROOT/rel,rel)
 (folder/'SHA256SUMS').write_text(sha(dest)+'  '+name+'\n',encoding='ascii')
 (folder/'release_manifest.json').write_bytes((ROOT/'release_manifest.json').read_bytes())
 print('Immutable snapshot created: releases/v'+version+'/'+name)
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['manifest','snapshot']:raise SystemExit('usage: baseline.py manifest|snapshot')
 {'manifest':manifest,'snapshot':snapshot}[sys.argv[1]]()
