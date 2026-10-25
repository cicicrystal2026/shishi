"""Download official IndexTTS2.5 resources with verified resumable chunks."""
import argparse, concurrent.futures, hashlib, json, math, time, urllib.parse, urllib.request
from pathlib import Path

def fetch(url, headers=None):
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=60)

def download(target, item, base, source, repo_id="IndexTeam/IndexTTS-2.5"):
    path=(target/item['Path']).resolve()
    if not path.is_relative_to(target.resolve()):raise ValueError('Invalid resource path')
    path.parent.mkdir(parents=True,exist_ok=True)
    size=item['Size']; expected=item['Sha256']
    def checksum(p):
        h=hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
        return h.hexdigest()
    if path.exists() and path.stat().st_size==size and checksum(path)==expected:return
    if not size:path.write_bytes(b'');return
    url=('https://huggingface.co/'+repo_id+'/resolve/main/'+urllib.parse.quote(item['Path']) if source=='huggingface' else base+'?Revision=master&FilePath='+urllib.parse.quote(item['Path'],safe=''))
    chunk=32*1024*1024
    def part(i):
        start=i*chunk;end=min(size,start+chunk)-1
        dest=path.with_name(path.name+f'.part-{i}')
        if dest.exists() and dest.stat().st_size==end-start+1:return dest
        for attempt in range(3):
            try:
                received=dest.stat().st_size if dest.exists() else 0
                current=start+received
                with fetch(url,{'Range':f'bytes={current}-{end}'}) as response:
                    if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {current}-{end}/{size}':raise RuntimeError('Unexpected range response')
                    with dest.open('ab' if received else 'wb') as out:
                        while True:
                            data=response.read(65536)
                            if not data:break
                            out.write(data)
                if dest.stat().st_size!=end-start+1:raise RuntimeError('Incomplete download')
                return dest
            except Exception:
                if attempt==2:raise
                time.sleep(2)
    if size>chunk:
        count=math.ceil(size/chunk)
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
            for done,_ in enumerate(pool.map(part,range(count)),1):
                if done%8==0 or done==count:print(item['Path'],done,'/',count,'chunks',flush=True)
        temp=path.with_name(path.name+'.complete')
        with temp.open('wb') as out:
            for i in range(count):
                with path.with_name(path.name+f'.part-{i}').open('rb') as source:
                    for block in iter(lambda:source.read(4*1024*1024),b''):out.write(block)
        if checksum(temp)!=expected:raise RuntimeError('SHA256 mismatch: '+item['Path'])
        temp.replace(path)
        for i in range(count):path.with_name(path.name+f'.part-{i}').unlink()
    else:
        temp=path.with_name(path.name+'.partial')
        with fetch(url) as r,temp.open('wb') as out:
            for block in iter(lambda:r.read(1024*1024),b''):out.write(block)
        if temp.stat().st_size!=size or checksum(temp)!=expected:raise RuntimeError('SHA256 mismatch: '+item['Path'])
        temp.replace(path)
    print('Verified',item['Path'],flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',choices=['modelscope','huggingface'],default='huggingface')
    parser.add_argument('--root',default=r'D:\AI-Runtime\shishi-indextts')
    args=parser.parse_args();root=Path(args.root).resolve();target=root/'models'/'IndexTTS-2.5';target.mkdir(parents=True,exist_ok=True)
    base='https://modelscope.cn/api/v1/models/IndexTeam/IndexTTS-2.5/repo'
    with fetch(base+'/files?Revision=master&Recursive=true') as r:manifest=json.load(r)
    files=[f for f in manifest['Data']['Files'] if f['Type']=='blob' and not f['Path'].startswith('qwen0.6bemo4-merge/')]
    (root/'model-files.json').write_text(json.dumps(manifest),encoding='utf-8')
    print('Core model bytes',sum(f['Size'] for f in files),'optional Qwen emotion model excluded',flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda item:download(target,item,base,args.source),sorted(files,key=lambda f:f['Size'])))
    voices=root/'voices';voices.mkdir(exist_ok=True);voice=voices/'voice_01.wav'
    if not voice.exists():
        urls=['https://huggingface.co/spaces/IndexTeam/IndexTTS-2-Demo/resolve/main/examples/voice_01.wav','https://hf-mirror.com/spaces/IndexTeam/IndexTTS-2-Demo/resolve/main/examples/voice_01.wav']
        for url in urls:
            try:
                with fetch(url) as r:data=r.read()
                if data[:4]!=b'RIFF' or data[8:12]!=b'WAVE':raise RuntimeError('Invalid example WAV')
                voice.write_bytes(data);break
            except Exception:
                if url==urls[-1]:raise
    print('Core model and official demo voice ready',flush=True)

if __name__=='__main__':main()
