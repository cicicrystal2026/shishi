from pathlib import Path
import json, hashlib
from check_sync import ROOT,reqs
v=(ROOT/'VERSION').read_text().strip();out=ROOT/'contracts';out.mkdir(exist_ok=True)
def save(name,d): (out/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def obj(props,required=None):return {'type':'object','properties':props,'required':required if required is not None else list(props),'additionalProperties':False}
S={'type':'string'};ID={'type':'string','format':'uuid'};N={'type':'integer','minimum':0}
def ref(name):return {'$ref':'#/$defs/'+name}
states=['queued','leased','submitting','submitted','running','unknown','cancel_requested','succeeded','failed','cancelled']
defs={
 'SourceRef':obj({'spanId':ID,'pageId':ID}),
 'Claim':obj({'id':ID,'kind':{'enum':['fact','author_view','creative','general']},'status':{'enum':['pending','verified','disputed','excluded']},'statement':S,'sources':{'type':'array','items':ref('SourceRef')}}),
 'Paragraph':obj({'id':ID,'text':{'type':'string','minLength':1},'claimIds':{'type':'array','items':ID},'sourceSpanIds':{'type':'array','items':ID}}),
 'Script':obj({'schemaVersion':{'const':1},'title':S,'coreMessage':S,'paragraphs':{'type':'array','minItems':1,'items':ref('Paragraph')}}),
 'Shot':obj({'id':ID,'shotKey':S,'paragraphIds':{'type':'array','minItems':1,'items':ID},'intent':S,'imagePrompt':S,'referenceAssetIds':{'type':'array','items':ID},'startFrame':N,'durationFrames':{'type':'integer','minimum':1}}),
 'Job':obj({'id':ID,'status':{'enum':states},'attempt':{'type':'integer','minimum':1},'providerTaskId':{'type':['string','null']},'inputHash':{'type':'string','pattern':'^[a-f0-9]{64}$'}}),
 'TimelineClip':obj({'shotId':ID,'assetId':ID,'startFrame':N,'durationFrames':{'type':'integer','minimum':1}}),
 'Subtitle':obj({'text':S,'startMs':N,'endMs':{'type':'integer','minimum':1}}),
 'Timeline':obj({'schemaVersion':{'const':1},'fps':{'const':30},'width':{'enum':[1080,1920]},'height':{'enum':[1080,1920]},'clips':{'type':'array','minItems':1,'items':ref('TimelineClip')},'subtitles':{'type':'array','items':ref('Subtitle')},'narrationAssetId':ID,'musicAssetId':{'type':['string','null']}}),
 'ChangePlan':obj({'schemaVersion':{'const':1},'operations':{'type':'array','minItems':1,'items':obj({'op':{'enum':['update_subtitle_style','adjust_audio_gain','change_pacing','replace_asset','rewrite_narration','revise_claim','regenerate_image','regenerate_clip']},'targetRefs':{'type':'array','minItems':1,'items':S},'parameters':{'type':'object'}})},'requiresClarification':{'type':'boolean'},'estimatedCostMicros':{'type':['integer','null'],'minimum':0}}),
 'Preference':obj({'audience':S,'durationMinSec':{'type':'integer','minimum':1},'durationMaxSec':{'type':'integer','minimum':1},'visualStyle':S,'tone':S,'voiceStyle':S,'reviewStory':{'type':'boolean'},'budgetMicros':{'type':['integer','null'],'minimum':0},'currency':{'enum':['CNY','USD']}})
}
save('core.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:shishi:core:1','title':'Shishi v'+v+' stage contracts','version':v,'$defs':defs})
schemas={k:json.loads(json.dumps(val).replace('#/$defs/','#/components/schemas/')) for k,val in defs.items()}
schemas.update({'Error':obj({'code':S,'message':S,'requestId':S,'details':{'type':'object'}}),'Accepted':obj({'id':ID,'status':S}),'List':obj({'items':{'type':'array','items':{'type':'object'}},'nextCursor':{'type':['string','null']}}),'ProjectCreate':obj({'title':{'type':'string','minLength':1},'preferenceId':ID,'overrides':{'type':'object'}},['title','preferenceId']),'ProjectPatch':obj({'expectedVersion':{'type':'integer','minimum':1},'title':S,'overrides':{'type':'object'}},['expectedVersion']),'ApprovalInput':obj({'targetType':{'enum':['script','timeline']},'targetId':ID,'versionHash':S,'expectedVersion':{'type':'integer','minimum':1}}),'ActionInput':obj({'runId':ID,'action':{'enum':['pause','resume','retry']},'expectedVersion':{'type':'integer','minimum':1}}),'ShotAction':obj({'shotId':ID,'action':{'enum':['select_asset','replace_asset','generate_candidate']},'assetId':ID,'expectedVersion':{'type':'integer','minimum':1}},['shotId','action','expectedVersion']),'FeedbackInput':obj({'targetId':ID,'text':{'type':'string','minLength':1},'expectedVersion':{'type':'integer','minimum':1}}),'ExportInput':obj({'timelineId':ID,'versionHash':S})})
schemas['Project']=obj({'id':ID,'title':S,'rowVersion':{'type':'integer','minimum':1},'preferenceId':ID,'overrides':{'type':'object'},'status':S,'createdAt':{'type':'string','format':'date-time'},'updatedAt':{'type':'string','format':'date-time'}})
schemas['Run']=obj({'id':ID,'status':{'enum':['draft','running','waiting_review','blocked','paused','completed','failed','cancelled']},'reasonCode':{'type':['string','null']},'jobs':{'type':'array','items':{'$ref':'#/components/schemas/Job'}}})
schemas['SourcePage']=obj({'id':ID,'pageOrder':N,'printedPage':{'type':['string','null']},'ocrStatus':S,'revision':{'type':'integer','minimum':1}})
schemas['Export']=obj({'id':ID,'timelineId':ID,'status':{'enum':['queued','running','succeeded','failed']},'files':{'type':'array','items':obj({'name':S,'assetId':ID,'sha256':S})}})
schemas['Event']=obj({'seq':N,'eventType':S,'payload':{'type':'object'}})
schemas['FeedbackRecord']=obj({'id':ID,'text':S,'status':S,'plan':{'anyOf':[{'$ref':'#/components/schemas/ChangePlan'},{'type':'null'}]}})
schemas['ScriptCreate']=obj({'expectedVersion':{'type':'integer','minimum':1},'parentId':{'type':['string','null']},'script':{'$ref':'#/components/schemas/Script'}})
schemas['StoryRunInput']=obj({'expectedVersion':{'type':'integer','minimum':1},'brief':S},['expectedVersion'])
schemas['ScriptRecord']=obj({'id':ID,'parentId':{'type':['string','null']},'versionHash':S,'status':{'enum':['draft','review_pending','approved','stale']},'content':{'$ref':'#/components/schemas/Script'}})
paths={}
def endpoint(path,method,summary,inputname=None,result='Accepted',async_=False):
 full='/api/v1'+path;params=[]
 for name in __import__('re').findall(r'\{(\w+)\}',path):params.append({'name':name,'in':'path','required':True,'schema':ID})
 if method in ['post','patch','delete']:
  params+=[{'name':'X-CSRF-Token','in':'header','required':True,'schema':S}]
 if method=='post':params+=[{'name':'Idempotency-Key','in':'header','required':True,'schema':{'type':'string','minLength':8}}]
 if method=='get' and result=='List':params+=[{'name':'limit','in':'query','schema':{'type':'integer','minimum':1,'maximum':100,'default':20}},{'name':'cursor','in':'query','schema':S}]
 code='202' if async_ else ('201' if method=='post' else '204' if method=='delete' else '200')
 responses={code:{'description':summary}}
 if code!='204':responses[code]['content']={'application/json':{'schema':{'$ref':'#/components/schemas/'+result}}}
 for c in ['401','404','409','422','500']:responses[c]={'description':c+' typed error','content':{'application/json':{'schema':{'$ref':'#/components/schemas/Error'}}}}
 op={'summary':summary,'operationId':method+'_'+path.replace('/','_').replace('{','').replace('}','').replace('-','_'),'parameters':params,'responses':responses,'security':[{'session':[]}]}
 if inputname:op['requestBody']={'required':True,'content':{'application/json':{'schema':{'$ref':'#/components/schemas/'+inputname}}}}
 paths.setdefault(full,{})[method]=op
endpoint('/projects','get','List projects',result='List');endpoint('/projects','post','Create draft','ProjectCreate')
endpoint('/projects/{projectId}','get','Get project snapshot');endpoint('/projects/{projectId}','patch','Update project','ProjectPatch');endpoint('/projects/{projectId}','delete','Soft delete project')
endpoint('/preferences','get','Get default preference',result='Preference');endpoint('/preferences','post','Create preference version','Preference')
p='/projects/{projectId}'
for tail in ['sources','scripts','runs','shots','events','exports']:endpoint(p+'/'+tail,'get','List '+tail,result='List')
endpoint(p+'/sources','post','Import source',async_=True)
paths['/api/v1'+p+'/sources']['post']['requestBody']={'required':True,'content':{'multipart/form-data':{'schema':obj({'file':{'type':'string','format':'binary'},'pageOrder':N},['file'])},'application/json':{'schema':obj({'text':{'type':'string','minLength':1},'bibliography':{'type':'object'}},['text'])}}}
endpoint(p+'/story-runs','post','Start story workflow',async_=True)
endpoint(p+'/scripts','post','Create script version','Script',result='Script')
endpoint(p+'/approvals','post','Approve exact version','ApprovalInput',async_=True)
endpoint(p+'/run-actions','post','Pause resume retry workflow','ActionInput',async_=True)
endpoint(p+'/shot-actions','post','Apply shot action','ShotAction',async_=True)
endpoint(p+'/feedback','post','Create change plan','FeedbackInput',result='ChangePlan',async_=True)
endpoint(p+'/feedback','get','List feedback and change plans',result='List')
endpoint(p+'/exports','post','Create export','ExportInput',async_=True)
endpoint('/assets/{assetId}/content','get','Read protected asset')
op=paths['/api/v1/assets/{assetId}/content']['get'];op['parameters'].append({'name':'Range','in':'header','schema':S});op['responses']['200']={'description':'Protected binary content','content':{'application/octet-stream':{'schema':{'type':'string','format':'binary'}}}};op['responses']['206']={'description':'Partial content'};op['responses']['416']={'description':'Range not satisfiable'}
def response_type(path,method,code,name):paths['/api/v1'+path][method]['responses'][code]['content']={'application/json':{'schema':{'$ref':'#/components/schemas/'+name}}}
response_type('/projects/{projectId}','get','200','Project');response_type('/projects','post','201','Project');response_type('/projects/{projectId}','patch','200','Project')
for tail,name in [('sources','SourcePage'),('scripts','ScriptRecord'),('runs','Run'),('shots','Shot'),('events','Event'),('exports','Export'),('feedback','FeedbackRecord')]:
 key=name+'List';schemas[key]=obj({'items':{'type':'array','items':{'$ref':'#/components/schemas/'+name}},'nextCursor':{'type':['string','null']}});response_type(p+'/'+tail,'get','200',key)
schemas['ProjectList']=obj({'items':{'type':'array','items':{'$ref':'#/components/schemas/Project'}},'nextCursor':{'type':['string','null']}});response_type('/projects','get','200','ProjectList')
response_type(p+'/feedback','post','202','Accepted')
response_type(p+'/scripts','post','201','ScriptRecord')
paths['/api/v1'+p+'/scripts']['post']['requestBody']['content']['application/json']['schema']={'$ref':'#/components/schemas/ScriptCreate'}
paths['/api/v1'+p+'/story-runs']['post']['requestBody']={'required':True,'content':{'application/json':{'schema':{'$ref':'#/components/schemas/StoryRunInput'}}}}
save('openapi.json',{'openapi':'3.1.0','info':{'title':'Shishi desktop API design contract','version':v,'description':'Design only. No running service or provider calls.'},'paths':paths,'components':{'schemas':schemas,'securitySchemes':{'session':{'type':'apiKey','in':'cookie','name':'shishi_session'}}}})
# Explicit requirement-to-module map; no implementation claims.
groups=[(1,4,['P01'],['T01','T02','T07','T08'],'7.1'),(5,9,['P02','S01'],['T01','T02','T06','T07'],'7.2'),(10,15,['P03','S02'],['T01','T02','T05','T06','T08'],'7.3'),(16,20,['P04','S02'],['T02','T03','T04','T06','T07'],'7.4'),(21,26,['P05','S01'],['T01','T03','T05','T07','T09'],'7.5'),(27,31,['P06'],['T01','T03','T04','T06','T07','T08','T09'],'7.6'),(32,37,['P07'],['T01','T03','T06','T07','T09','T10'],'7.7'),(38,42,['P08'],['T01','T02','T08','T09','T10'],'7.8')]
items=[]
for rid,text in reqs().items():
 num=int(rid[1:]);group=next(g for g in groups if g[0]<=num<=g[1])
 items.append({'id':rid,'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'pages':group[2],'modules':group[3],'prd_section':group[4],'technical_spec':'拾史桌面端v1.0技术规格说明书.md','acceptance':['AC-'+rid],'implementation_status':'design_only'})
(ROOT/'需求追踪.json').write_text(json.dumps({'version':v,'requirements':items,'review_scope':'Design mapping only; runtime acceptance not performed'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('contracts generated:',len(paths),'paths,',len(items),'requirements')
