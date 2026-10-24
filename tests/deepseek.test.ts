import {test,beforeEach} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'shishi-deepseek-test-'));
process.env.RUNTIME_DIR=temp;process.env.SHISHI_SECRET_FILE=path.join(temp,'fake-connection.json');
process.env.OPENAI_API_KEY='sk-fixture-openai-never-real';process.env.DEEPSEEK_API_KEY='sk-fixture-deepseek-never-real';
delete process.env.TEXT_MODEL;delete process.env.DEEPSEEK_MODEL;
const d=await import('../apps/api/db.ts');const p=await import('../apps/api/providers.ts');const {uid,now}=await import('../packages/domain.ts');
const config={textProvider:'deepseek',textModel:'fixture-openai-model',deepseekModel:'deepseek-flash',imageModel:'fixture-image-model',ttsModel:'fixture-tts-model',reservations:{text:0.01,image:0.01,tts:0.01},pricingConfirmed:true};
beforeEach(()=>{d.setSetting('connection',config)});
function project(){const id=uid();d.run('INSERT INTO projects(id,title,preference_id,overrides_json,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',id,'fixture only',d.defaults().id,'{"budgetMicros":1000000}','draft',now(),now());return {projectId:id,...d.enqueue(id,'story',{mode:'real'},uid())};}
function newJob(){const x=project();return {id:x.projectId,jid:x.jobId};}
function respond(text:string){return new Response(JSON.stringify({id:'fixture-response',output:[{content:[{type:'output_text',text}]}]}),{headers:{'x-request-id':'fixture-request'}});}

test('DeepSeek story uses its own official endpoint, key and structured output',async t=>{
 const old=globalThis.fetch;t.after(()=>globalThis.fetch=old);const {id,jid}=newJob();let calls=0;
 globalThis.fetch=async(url:any,options:any)=>{calls++;assert.equal(url,'https://api.deepseek.com/responses');assert.equal(options.headers.Authorization,'Bearer '+process.env.DEEPSEEK_API_KEY);const b=JSON.parse(options.body);assert.equal(b.model,'deepseek-flash');assert.equal(b.input[0].role,'system');assert.equal(b.store,undefined);assert.deepEqual(b.reasoning,{effort:'none'});assert.equal(b.text.format.type,'json_schema');return respond(JSON.stringify({title:'测试',coreMessage:'事实',paragraphs:[{text:'来源正文',sourceSpanIds:['span1']}]}));};
 const result=await p.writeStory(id,jid,[{id:'span1',text:'来源正文'}],'','real');assert.equal(result.title,'测试');assert.equal(calls,1);
 const call=d.one('SELECT * FROM provider_calls WHERE job_id=?',jid);assert.equal(call.provider,'deepseek');assert.equal(call.model,'deepseek-flash');assert.equal(call.provider_response_id,'fixture-response');
});
test('storyboard preserves approved paragraph IDs and rejects bad references',async t=>{
 const old=globalThis.fetch;t.after(()=>globalThis.fetch=old);const {id,jid}=newJob();globalThis.fetch=async()=>respond(JSON.stringify({shots:[{paragraphId:'p1',prompt:'器物特写',motionPrompt:'推进'}]}));
 const result=await p.planShots(id,jid,{paragraphs:[{id:'p1',text:'正文'}]},'real');assert.equal(result[0].paragraphId,'p1');
 const other=newJob();globalThis.fetch=async()=>respond(JSON.stringify({shots:[{paragraphId:'invented',prompt:'特写'}]}));await assert.rejects(()=>p.planShots(other.id,other.jid,{paragraphs:[{id:'p1',text:'正文'}]},'real'),/未完整覆盖/);
});
test('image and TTS routes never receive the DeepSeek secret',async t=>{
 const old=globalThis.fetch;t.after(()=>globalThis.fetch=old);const {id,jid}=newJob();let calls=0;
 globalThis.fetch=async(url:any,options:any)=>{calls++;assert.ok(String(url).startsWith('https://api.openai.com/v1/'));assert.equal(options.headers.Authorization,'Bearer '+process.env.OPENAI_API_KEY);return url.endsWith('audio/speech')?new Response(Buffer.from('fixture WAV')):new Response(JSON.stringify({data:[]}));};
 await p.paid(id,jid,'fixture-image','image','images/generations',{model:'fixture-image'});await p.paid(id,jid,'fixture-tts','tts','audio/speech',{model:'fixture-tts'});assert.equal(calls,2);
});
test('DeepSeek photo OCR carries real image input and system transcription instruction',async t=>{
 const old=globalThis.fetch;t.after(()=>globalThis.fetch=old);const {id,jid}=newJob();const asset=d.storeAsset(id,'source','fixture',Buffer.from('fixture only'),'png',{mime:'image/png'});
 globalThis.fetch=async(url:any,options:any)=>{assert.equal(url,'https://api.deepseek.com/responses');const b=JSON.parse(options.body);assert.equal(b.input[0].role,'system');assert.ok(b.input[1].content[0].image_url.startsWith('data:image/png;base64,'));return respond('转写正文');};
 assert.equal(await p.readSource(id,jid,{id:uid(),asset_id:asset.id}),'转写正文');
});
test('unsupported PDF and nonvision models fail before any reservation or request',async t=>{
 const old=globalThis.fetch;t.after(()=>globalThis.fetch=old);let calls=0;globalThis.fetch=async()=>{calls++;throw Error('network forbidden');};const {id,jid}=newJob();const a=d.storeAsset(id,'source','fixture',Buffer.from('%PDF-fixture'),'pdf',{mime:'application/pdf'});
 await assert.rejects(()=>p.readPdfPages(id,jid,a.id,2),/转成 JPG\/PNG/);
 d.setSetting('connection',{...config,deepseekModel:'deepseek-v4-pro'});const image=d.storeAsset(id,'source','fixture',Buffer.from('fixture'),'png',{mime:'image/png'});await assert.rejects(()=>p.readSource(id,jid,{id:uid(),asset_id:image.id}),/deepseek-flash/);
 assert.equal(calls,0);assert.equal(d.totals(id).reservedMicros,0);assert.equal(d.all('SELECT id FROM provider_calls WHERE job_id=?',jid).length,0);
});
test('missing selected key does not fall back to OpenAI or occupy budget',async t=>{
 const saved=process.env.DEEPSEEK_API_KEY;delete process.env.DEEPSEEK_API_KEY;t.after(()=>process.env.DEEPSEEK_API_KEY=saved);const {id,jid}=newJob();
 await assert.rejects(()=>p.paid(id,jid,'missing','text','responses',{}),/DeepSeek API Key/);assert.equal(d.totals(id).reservedMicros,0);assert.equal(p.connectionStatus().configured,false);
});
test('timeout preserves reservation and prevents a second DeepSeek submission',async t=>{
 const old=globalThis.fetch;t.after(()=>globalThis.fetch=old);const {id,jid}=newJob();let calls=0;globalThis.fetch=async()=>{calls++;throw Error('fixture timeout')};
 await assert.rejects(()=>p.paid(id,jid,'timeout','text','responses',{}),/结果未知/);await assert.rejects(()=>p.paid(id,jid,'timeout','text','responses',{}),/尚未核实/);assert.equal(calls,1);assert.equal(d.totals(id).reservedMicros,10000);
});
test('secret updates preserve both providers, never expose keys, and validate before writing',()=>{
 const first='sk-fixture-stored-openai-only',second='sk-fixture-stored-deepseek-only';p.saveConnection({...config,key:first,deepseekKey:second});p.saveConnection({...config,key:'',deepseekKey:''});
 assert.deepEqual(JSON.parse(fs.readFileSync(process.env.SHISHI_SECRET_FILE!,'utf8')),{key:first,deepseekKey:second});
 const status=JSON.stringify(p.connectionStatus());assert.ok(!status.includes(first)&&!status.includes(second)&&!status.includes(process.env.DEEPSEEK_API_KEY!));
 assert.throws(()=>p.saveConnection({...config,key:'sk-fixture-invalid-change',reservations:{text:-1}}),/预留金额/);assert.equal(JSON.parse(fs.readFileSync(process.env.SHISHI_SECRET_FILE!,'utf8')).key,first);
 fs.unlinkSync(process.env.SHISHI_SECRET_FILE!);
});
test('legacy settings still select OpenAI with no migration of existing keys',()=>{d.setSetting('connection',{textModel:'legacy'});assert.equal(p.connection().textProvider,'openai');assert.equal(p.connection().textModel,'legacy');});

test('model IDs normalize surrounding whitespace on save and on legacy reads',()=>{
 p.saveConnection({...config,deepseekModel:' deepseek-flash  ',textModel:' model ',imageModel:' image ',ttsModel:' voice '});
 assert.equal(p.connection().textModel,'deepseek-flash');assert.equal(d.setting('connection').deepseekModel,'deepseek-flash');assert.equal(p.connection().imageModel,'image');
 d.setSetting('connection',{...config,deepseekModel:'deepseek-flash '});assert.equal(p.connection().textModel,'deepseek-flash');
 assert.throws(()=>p.saveConnection({...config,deepseekModel:'   '}),/不能为空/);
 assert.throws(()=>p.saveConnection({...config,textModel:'   '}),/不能为空/);
});

test('truncated text is rejected and response usage remains available for reconciliation',async t=>{
 const old=globalThis.fetch;t.after(()=>globalThis.fetch=old);const {id,jid}=newJob();globalThis.fetch=async()=>new Response(JSON.stringify({id:'partial-fixture',status:'incomplete',usage:{input_tokens:10,output_tokens:20},incomplete_details:{reason:'max_output_tokens'},output:[]}));
 await assert.rejects(()=>p.paid(id,jid,'partial','text','responses',{model:'deepseek-flash'}),/输出被截断/);
 assert.equal(d.totals(id).reservedMicros,0);const record=d.one('SELECT response_metadata_json FROM provider_calls WHERE job_id=?',jid);assert.equal(JSON.parse(record.response_metadata_json).status,'incomplete');
});
