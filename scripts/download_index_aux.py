"""Fetch only the official auxiliary weights needed by IndexTTS2.5."""
import argparse, concurrent.futures, hashlib, json, urllib.request
from pathlib import Path
from download_index_models import download

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',default=r'D:\AI-Runtime\shishi-indextts')
    root=Path(p.parse_args().root).resolve();cache=root/'models/IndexTTS-2.5/hf_cache';cache.mkdir(parents=True,exist_ok=True)
    entries=[('facebook/w2v-bert-2.0',cache/'w2v-bert-2.0',['config.json','preprocessor_config.json','model.safetensors','README.md']),('funasr/campplus',cache,['campplus_cn_common.bin']),('nvidia/bigvgan_v2_22khz_80band_256x',cache/'bigvgan',['config.json','bigvgan_generator.pt','LICENSE'])]
    manifest=[]
    def group(entry):
        repo,target,names=entry;target.mkdir(parents=True,exist_ok=True)
        with urllib.request.urlopen('https://huggingface.co/api/models/'+repo+'/tree/main',timeout=30) as r:meta=json.load(r)
        selected={f['path']:f for f in meta if f.get('type')=='file'}
        for name in names:
            f=selected[name];manifest.append({'repo':repo,**f})
            if f.get('lfs'):
                download(target,{'Path':name,'Size':f['size'],'Sha256':f['lfs']['oid']},'', 'huggingface',repo_id=repo)
            else:
                with urllib.request.urlopen('https://huggingface.co/'+repo+'/resolve/main/'+name,timeout=30) as r:data=r.read()
                actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
                if actual!=f['oid']:raise RuntimeError('Git blob integrity mismatch '+repo+'/'+name)
                (target/name).write_bytes(data)
                print('Verified auxiliary config',repo,name,flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(group,entries))
    (root/'auxiliary-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Auxiliary models ready',flush=True)

if __name__=='__main__':main()
