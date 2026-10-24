const {chromium}=require('C:/Users/thoma/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');const assert=require('node:assert/strict');
(async()=>{
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
try{const page=await browser.newPage({viewport:{width:1440,height:1080}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():route.abort());
await page.goto('http://127.0.0.1:4317/#settings');await page.getByRole('heading',{name:'选择你的创作模型'}).waitFor();
assert.equal(await page.getByLabel('文字服务商').inputValue(),'deepseek');assert.equal(await page.getByLabel('DeepSeek 模型',{exact:true}).inputValue(),'deepseek-flash');
assert.equal(await page.getByLabel('DeepSeek API Key',{exact:true}).inputValue(),'');assert.equal(await page.getByLabel('OpenAI API Key',{exact:true}).inputValue(),'');
await page.getByLabel('文字服务商').selectOption('openai');await page.getByLabel('OpenAI 文字 / 识读模型').waitFor();await page.getByLabel('文字服务商').selectOption('deepseek');
await page.getByRole('button',{name:'保存连接'}).click();await page.getByRole('status').filter({hasText:'连接设置已保存'}).waitFor();
const config=await page.evaluate(async()=>{const b=await fetch('/api/v1/bootstrap').then(r=>r.json());return {version:b.version,connection:b.connection};});
assert.equal(config.version,'1.0.0-dev.2');assert.equal(config.connection.textProvider,'deepseek');assert.deepEqual(config.connection.reservations,{text:2,image:2,tts:2});assert.equal(config.connection.openaiConfigured,true);
assert.equal(config.connection.key,undefined);assert.equal(config.connection.deepseekKey,undefined);
fs.mkdirSync('qa/screens',{recursive:true});await page.screenshot({path:'qa/screens/deepseek-settings.png',fullPage:true});
for(const width of [1280,1440,1920]){await page.setViewportSize({width,height:1080});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
await page.goto('http://127.0.0.1:4317/#p/0dbe1187-6c04-45e9-bd8d-84f1250891c2/progress');await page.getByRole('heading',{name:'故事正在成为画面'}).waitFor();await page.getByText('30.00 元',{exact:true}).waitFor();
assert.deepEqual(errors,[]);fs.writeFileSync('qa/deepseek.json',JSON.stringify({version:config.version,widths:[1280,1440,1920],runtimeErrors:errors,checks:['provider selector','separate empty secret fields','blank save preserves OpenAI key','budget strategy preserved','current project budget 30 CNY','no secrets returned','no external requests']},null,2));console.log('PASS DeepSeek settings, blank-key preservation, project budget and desktop layout');
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
