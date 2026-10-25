import fs from 'node:fs';import path from 'node:path';import type http from 'node:http';import formidable from 'formidable';
import {RUNTIME,setting,setSetting,storeAsset,filePath,asset,one,run} from './db.ts';import {assert,AppError,uid,hash} from '../../packages/domain.ts';import {command,duration,ffmpeg} from './render.ts';

export function indexTtsUrl(value:any){
 assert(typeof value==='string','BAD_TTS_URL','请填写本机 IndexTTS 服务地址');let u:URL;try{u=new URL(value.trim())}catch{throw new AppError('BAD_TTS_URL','IndexTTS 地址格式不正确')}
 assert(u.protocol==='http:'&&['127.0.0.1','localhost'].includes(u.hostname)&&!u.username&&!u.password&&!u.search&&!u.hash&&['','/'].includes(u.pathname),'BAD_TTS_URL','当前版本仅连接本机 http://127.0.0.1:端口 服务');
 u.hostname='127.0.0.1';return u.origin;
}
export async function indexTtsHealth(url:string){try{const r=await fetch(indexTtsUrl(url)+'/health',{signal:AbortSignal.timeout(5000),redirect:'error'});const b=await r.json() as any;return {available:r.ok&&b.service==='shishi-index-tts'&&b.ready===true,model:b.model||null,referenceReady:!!setting('indexTtsVoice')||!!b.referenceReady};}catch{return {available:false,model:null,referenceReady:!!setting('indexTtsVoice')};}}
export function voiceStatus(){const v=setting('indexTtsVoice');return v?{id:v.id,name:v.name,seconds:v.seconds}:null;}
export async function uploadVoice(req:http.IncomingMessage){
 const form=formidable({uploadDir:path.join(RUNTIME,'temp'),maxFileSize:10*1024*1024,maxTotalFileSize:10*1024*1024,maxFiles:1,allowEmptyFiles:false});let files:any={};let converted='';
 try{const [,f]=await form.parse(req);files=f;const list=Object.values(f).flat() as any[];assert(list.length===1,'VOICE_REQUIRED','请选择一段2–30秒清晰参考人声');const file=list[0];const seconds=await duration(file.filepath);assert(seconds>=2&&seconds<=30,'VOICE_DURATION','参考音频需要为2–30秒');
 const id=uid(),folder=path.join(RUNTIME,'voices');fs.mkdirSync(folder,{recursive:true});converted=path.join(folder,id+'.wav');await command(ffmpeg,['-v','error','-y','-i',file.filepath,'-vn','-ac','1','-ar','24000','-c:a','pcm_s16le',converted]);
 setSetting('indexTtsVoice',{id,file:id+'.wav',name:String(file.originalFilename||'参考声音').slice(0,150),seconds:await duration(converted)});return voiceStatus();
 }catch(e){if(converted&&fs.existsSync(converted))fs.unlinkSync(converted);throw e;}finally{for(const file of Object.values(files).flat() as any[])if(fs.existsSync(file.filepath))fs.unlinkSync(file.filepath);}
}
export async function indexSpeech(id:string,jid:string,text:string,stage:string,url:string){
 const base=indexTtsUrl(url),v=setting('indexTtsVoice');const reference=v?fs.readFileSync(path.join(RUNTIME,'voices',v.file)):null;
 const key=hash(JSON.stringify({provider:'index_tts',jid,stage,text,voice:reference?hash(reference):'service-default',base}));
 const previous=one('SELECT * FROM provider_calls WHERE request_key=? OR request_key LIKE ? ORDER BY rowid DESC LIMIT 1',key,key+':%');if(previous?.status==='succeeded'){const metadata=JSON.parse(previous.response_metadata_json||'{}');if(metadata.assetId)return asset(metadata.assetId);}
 assert(!previous||previous.status==='failed','PROVIDER_UNKNOWN','本机配音请求结果待核实，未自动重复生成');
 const health=await indexTtsHealth(base);assert(health.available,'PROVIDER_UNCONFIGURED','本机 IndexTTS 服务未就绪，请先启动并检测服务');assert(reference||health.referenceReady,'REFERENCE_REQUIRED','请先上传参考声音或配置服务示例音色');
 const callId=uid(),requestKey=previous?key+':'+uid():key;
 run('INSERT INTO provider_calls(id,job_id,stage,request_key,status,provider,model,created_at) VALUES(?,?,?,?,?,?,?,?)',callId,jid,'index-tts-'+stage,requestKey,'submitting','index_tts','IndexTTS-local',new Date().toISOString());
 let r:Response;try{r=await fetch(base+'/v1/audio/speech',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({input:text,reference_audio:reference?.toString('base64'),duration_factor:1}),signal:AbortSignal.timeout(900000),redirect:'error'});}catch{run("UPDATE provider_calls SET status='unknown' WHERE id=?",callId);throw new AppError('PROVIDER_UNKNOWN','本机 IndexTTS 请求中断；请检查服务状态及输出，未自动重试');}
 if(!r.ok){run("UPDATE provider_calls SET status='failed' WHERE id=?",callId);let code='';try{code=(await r.json() as any).error||''}catch{}throw new AppError('INDEX_TTS_FAILED',code==='REFERENCE_REQUIRED'?'请先上传参考音频或给本机服务配置示例音色':'本机 IndexTTS 合成失败，请检查服务日志');}
 const bytes=Buffer.from(await r.arrayBuffer());assert(bytes.length>44&&bytes.subarray(0,4).toString()==='RIFF'&&bytes.subarray(8,12).toString()==='WAVE','INVALID_AUDIO','本机配音未返回有效 WAV');
 const temp=path.join(RUNTIME,'temp',uid()+'.wav');let seconds:number;try{fs.writeFileSync(temp,bytes);seconds=await duration(temp);}finally{if(fs.existsSync(temp))fs.unlinkSync(temp);}
 const a=storeAsset(id,'audio','index_tts',bytes,'wav',{mime:'audio/wav',stage,model:'IndexTTS-local',voiceId:v?.id||'service-default',seconds,apiFeeCNY:0});
 run("UPDATE provider_calls SET status='succeeded',provider_request_id=?,provider_response_id=?,response_metadata_json=? WHERE id=?",r.headers.get('x-request-id'),a.id,JSON.stringify({assetId:a.id,seconds,local:true,apiFeeCNY:0,voiceId:v?.id||'service-default'}),callId);return a;
}
