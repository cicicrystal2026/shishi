from pathlib import Path
import unittest,json,sqlite3,uuid
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
class Contracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.core=json.loads((ROOT/'contracts/core.schema.json').read_text(encoding='utf-8'));cls.api=json.loads((ROOT/'contracts/openapi.json').read_text(encoding='utf-8'))
 def validator(self,n):return Draft202012Validator({'$defs':self.core['$defs'],'$ref':'#/$defs/'+n})
 def test_schema_itself(self):Draft202012Validator.check_schema(self.core)
 def test_empty_script_rejected(self):self.assertFalse(self.validator('Script').is_valid({'schemaVersion':1,'title':'x','coreMessage':'x','paragraphs':[]}))
 def test_valid_script(self):self.assertTrue(self.validator('Script').is_valid({'schemaVersion':1,'title':'x','coreMessage':'x','paragraphs':[{'id':str(uuid.uuid4()),'text':'x','claimIds':[],'sourceSpanIds':[]}]}))
 def test_job_state_rejected(self):self.assertFalse(self.validator('Job').is_valid({'id':'x','status':'pretend_done','attempt':1,'providerTaskId':None,'inputHash':'a'*64}))
 def test_negative_cost_rejected(self):self.assertFalse(self.validator('ChangePlan').is_valid({'schemaVersion':1,'operations':[{'op':'adjust_audio_gain','targetRefs':['x'],'parameters':{}}],'requiresClarification':False,'estimatedCostMicros':-1}))
 def test_openapi_refs_resolve(self):
  def walk(x):
   if isinstance(x,dict):
    if '$ref'in x:
     self.assertTrue(x['$ref'].startswith('#/'));v=self.api
     for key in x['$ref'][2:].split('/'):v=v[key]
    for v in x.values():walk(v)
   elif isinstance(x,list):
    for v in x:walk(v)
  walk(self.api)
 def test_posts_idempotent(self):
  for ops in self.api['paths'].values():
   if 'post'in ops:self.assertIn('Idempotency-Key',[x['name'] for x in ops['post']['parameters']])
 def test_unique_operation_ids(self):
  ids=[o['operationId']for ops in self.api['paths'].values()for o in ops.values()];self.assertEqual(len(ids),len(set(ids)))
 def db(self):
  c=sqlite3.connect(':memory:');c.executescript((ROOT/'contracts/schema.sql').read_text());self.addCleanup(c.close);return c
 def seed(self,c):c.execute("INSERT INTO preference_versions VALUES('pref','{}','t')");c.execute("INSERT INTO projects(id,title,preference_id,created_at,updated_at) VALUES('p','x','pref','t','t')")
 def test_orphan_rejected(self):
  c=self.db()
  with self.assertRaises(sqlite3.IntegrityError):c.execute("INSERT INTO projects(id,title,preference_id,created_at,updated_at) VALUES('p','x','missing','t','t')")
 def test_duplicate_approval_rejected(self):
  c=self.db();self.seed(c);c.execute("INSERT INTO approvals VALUES('a','p','script','s','h','t')")
  with self.assertRaises(sqlite3.IntegrityError):c.execute("INSERT INTO approvals VALUES('b','p','script','s','h','t')")
 def test_sql_job_state_rejected(self):
  c=self.db();self.seed(c);c.execute("INSERT INTO workflow_runs(id,project_id,snapshot_json,status,created_at) VALUES('r','p','{}','draft','t')")
  with self.assertRaises(sqlite3.IntegrityError):c.execute("INSERT INTO jobs(id,run_id,idempotency_key,status,input_hash,created_at) VALUES('j','r','key','pretend_done','h','t')")
if __name__=='__main__':unittest.main(verbosity=2)
