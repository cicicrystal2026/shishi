import {createHash,randomUUID} from 'node:crypto';
export const uid=()=>randomUUID();
export const now=()=>new Date().toISOString();
export const hash=(v:string|Buffer)=>createHash('sha256').update(v).digest('hex');
export class AppError extends Error {status:number;code:string;constructor(code:string,message:string,status=422){super(message);this.code=code;this.status=status;}}
export function assert(ok:unknown,code:string,message:string,status=422):asserts ok{if(!ok)throw new AppError(code,message,status);}
export const DEFAULT_PREFS={audience:'对历史文化感兴趣的普通观众',duration:60,visual:'器物纪录风',tone:'有悬念、说人话、克制不夸张',voice:'清晰自然、平稳讲述',reviewStory:true,budgetMicros:null as number|null,ratio:'9:16',music:false,subtitleSize:52};
export type Preferences=typeof DEFAULT_PREFS;
export type Script={title:string;coreMessage:string;paragraphs:{id:string;text:string;sourceSpanIds:string[]}[]};
export type JobStatus='queued'|'leased'|'submitting'|'submitted'|'running'|'unknown'|'cancel_requested'|'succeeded'|'failed'|'cancelled';
export function affected(intent:string){if(intent==='subtitle'||intent==='music')return ['timeline','render'];if(intent==='narration')return ['audio','timing','timeline','render'];if(intent==='image')return ['image','timeline','render'];return ['script','shots','audio','images','timeline','render'];}
export function validateScript(value:any,sourceIds:string[]):Script {assert(value&&typeof value.title==='string'&&value.title.trim(),'BAD_SCRIPT','剧本缺少标题');assert(Array.isArray(value.paragraphs)&&value.paragraphs.length>0&&value.paragraphs.length<=20,'BAD_SCRIPT','剧本需要 1–20 个段落');for(const p of value.paragraphs){assert(typeof p.text==='string'&&p.text.trim()&&p.text.length<1500,'BAD_SCRIPT','旁白段落为空或过长');assert(Array.isArray(p.sourceSpanIds)&&p.sourceSpanIds.every((id:string)=>sourceIds.includes(id)),'INVALID_SOURCE','剧本引用了不存在的来源');}return {title:value.title,coreMessage:String(value.coreMessage||''),paragraphs:value.paragraphs.map((p:any)=>({id:p.id||uid(),text:p.text,sourceSpanIds:p.sourceSpanIds}))};}
export function budgetAvailable(limit:number|null,spent:number,reserved:number,needed:number){return limit!==null&&Number.isSafeInteger(limit)&&limit>=0&&needed>0&&spent+reserved+needed<=limit;}
export function money(n:number|null){return n===null?'未授权':(n/1e6).toFixed(2)+' 元';}
export function srtTime(ms:number){const n=Math.round(ms);return `${String(Math.floor(n/3600000)).padStart(2,'0')}:${String(Math.floor(n/60000)%60).padStart(2,'0')}:${String(Math.floor(n/1000)%60).padStart(2,'0')},${String(n%1000).padStart(3,'0')}`;}
