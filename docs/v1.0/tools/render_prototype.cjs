const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/thoma/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {pathToFileURL}=require('url');
const root=path.resolve(__dirname,'..');
const crypto=require('crypto');
const version=fs.readFileSync(path.join(root,'VERSION'),'utf8').trim();
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--disable-gpu','--no-first-run']});
 const page=await browser.newPage({viewport:{width:1440,height:1050},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const base=pathToFileURL(path.join(root,'原型/index.html')).href;
 fs.mkdirSync(path.join(root,'原型图'),{recursive:true});
 const routes=['home','preferences','input','story','production','storyboard','review','export'];
 const names=['01-我的作品','02-创作偏好','03-输入材料','04-确认故事','05-自动制作','06-分镜与素材','07-审阅成片','08-导出作品'];
 const checks=[];
 for(let i=0;i<routes.length;i++){
  await page.goto(base+'#'+routes[i]);await page.evaluate(()=>document.fonts.ready);
  const layout=await page.evaluate(()=>({width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,viewport:innerWidth,heading:document.querySelector('h1')?.textContent}));
  await page.screenshot({path:path.join(root,'原型图',names[i]+'.png'),fullPage:true});checks.push({route:routes[i],...layout});
 }
 await page.goto(base+'#production');await page.locator('[data-action=budget]').click();await page.getByRole('dialog').waitFor();await page.screenshot({path:path.join(root,'原型图/09-预算暂停状态.png'),fullPage:true});await page.getByRole('button',{name:'保留并稍后处理'}).click();
 await page.goto(base+'#story');await page.locator('button[data-action=source]').click();await page.getByRole('dialog').waitFor();await page.screenshot({path:path.join(root,'原型图/10-来源与疑点状态.png'),fullPage:true});await page.keyboard.press('Escape');
 await page.goto(base+'#home');await page.getByRole('button',{name:'＋ 新建作品',exact:true}).click();if(!page.url().endsWith('#input'))throw Error('new story nav failed');
 await page.getByRole('button',{name:'生成故事方案　→',exact:true}).click();if(!page.url().endsWith('#story'))throw Error('story nav failed');
 await page.getByRole('button',{name:'认可故事，开始制作　→',exact:true}).click();if(!page.url().endsWith('#production'))throw Error('production nav failed');
 await page.getByRole('button',{name:'查看分镜与素材',exact:true}).click();await page.locator('[data-asset-tab=prompts]').click();if(!await page.locator('.asset-description').first().innerText().then(t=>t.includes('提示词')))throw Error('asset tab failed');
 await page.locator('[data-action=shot]').first().click();await page.getByRole('dialog').waitFor();await page.keyboard.press('Escape');
 await page.goto(base+'#review');await page.locator('[data-suggestion]').first().click();await page.locator('[data-action=film-feedback]').click();if(!await page.locator('#feedback-list').innerText().then(t=>t.includes('开头节奏快一点')))throw Error('feedback failed');
 await page.goto(base+'#preferences');await page.locator('[name=duration]').selectOption('30–60 秒');await page.locator('[data-action=save-prefs]').click();await page.reload();if(await page.locator('[name=duration]').inputValue()!=='30–60 秒')throw Error('prefs persistence failed');await page.locator('[name=duration]').selectOption('60–90 秒');await page.locator('[data-action=save-prefs]').click();
 for(const w of [1280,1920]){await page.setViewportSize({width:w,height:1080});await page.goto(base+'#review');const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);if(overflow)throw Error('desktop horizontal overflow '+w)}
 if(errors.length)throw Error('Runtime errors '+JSON.stringify(errors));
 fs.writeFileSync(path.join(root,'原型/verification.json'),JSON.stringify({viewport:'1440 × 1050',routes:checks,interactionChecks:['new project flow','story approval','asset tabs','shot detail','feedback mapping','preferences persistence','1280 and 1920 width'],runtimeErrors:errors},null,2));
 const digest=p=>crypto.createHash('sha256').update(fs.readFileSync(path.join(root,p))).digest('hex');
 const sources=Object.fromEntries(['原型/index.html','原型/style.css','原型/prototype.js','tools/render_prototype.cjs'].map(p=>[p,digest(p)]));
 const outputs=Object.fromEntries(fs.readdirSync(path.join(root,'原型图')).filter(p=>/^\d/.test(p)&&p.endsWith('.png')).map(n=>{const p='原型图/'+n;return[p,digest(p)]}));
 fs.mkdirSync(path.join(root,'build'),{recursive:true});fs.writeFileSync(path.join(root,'build/prototype.json'),JSON.stringify({version,sources,outputs},null,2));
 console.log(JSON.stringify({version,screens:10,checks,runtimeErrors:errors},null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
