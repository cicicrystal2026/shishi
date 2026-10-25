import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
import wave

spec=importlib.util.spec_from_file_location('bridge',Path(__file__).resolve().parents[1]/'scripts'/'index_tts_bridge.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
class Engine:
    def __init__(self):self.calls=0
    def infer(self,**kwargs):
        self.calls+=1
        with wave.open(kwargs['output_path'],'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(16000);f.writeframes(b'\0\0'*1600)

class BridgeTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.reference=Path(self.temp.name)/'reference.wav'
        with wave.open(str(self.reference),'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(16000);f.writeframes(b'\0\0'*1600)
        self.engine=Engine();self.server=bridge.make_server(self.engine,self.reference,Path(self.temp.name)/'cache',port=0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)
        self.url='http://127.0.0.1:'+str(self.server.server_port)
    def test_health(self):
        with urllib.request.urlopen(self.url+'/health') as r:self.assertTrue(json.load(r)['referenceReady'])
    def test_cached_audio(self):
        req=urllib.request.Request(self.url+'/v1/audio/speech',data=json.dumps({'input':'测试旁白'}).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req) as r:first=r.read()
        with urllib.request.urlopen(req) as r:second=r.read()
        self.assertEqual(first,second);self.assertEqual(first[:4],b'RIFF');self.assertEqual(self.engine.calls,1)
    def test_bad_input_and_browser_origin_rejected(self):
        for body,headers,status in [({'input':''},{},400),({'input':'测试'},{'Origin':'https://example.com'},403),({'input':'测试','reference_audio':'invalid-base64'},{},400)]:
            req=urllib.request.Request(self.url+'/v1/audio/speech',data=json.dumps(body).encode(),headers={'Content-Type':'application/json',**headers})
            with self.assertRaises(urllib.error.HTTPError) as ctx:urllib.request.urlopen(req)
            self.assertEqual(ctx.exception.code,status)
        self.assertEqual(self.engine.calls,0)
if __name__=='__main__':unittest.main()
