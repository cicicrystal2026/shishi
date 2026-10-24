from pathlib import Path
import sys,json,shutil,tempfile,unittest,contextlib,io
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import check_sync
class SyncGuard(unittest.TestCase):
 def setUp(self):
  (ROOT/'tmp').mkdir(exist_ok=True)
  self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'tmp');self.addCleanup(self.tmp.cleanup)
  self.fixture=Path(self.tmp.name)/'copy';self.fixture.mkdir()
  manifest=json.loads((ROOT/'release_manifest.json').read_text(encoding='utf-8'))
  for rel in list(manifest['files'])+['release_manifest.json']:
   dest=self.fixture/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dest)
  self.original=check_sync.ROOT;check_sync.ROOT=self.fixture
  self.addCleanup(setattr,check_sync,'ROOT',self.original)
 def result(self):
  with contextlib.redirect_stdout(io.StringIO()):return check_sync.check()
 def test_clean_copy_passes(self):self.assertEqual(self.result(),0)
 def test_stale_requirement_detected(self):
  p=self.fixture/'拾史桌面端V1_PRD.md';p.write_text(p.read_text(encoding='utf-8').replace('F01：','F01：变更',1),encoding='utf-8');self.assertEqual(self.result(),1)
 def test_stale_derived_detected(self):
  p=self.fixture/'原型/prototype.js';p.write_bytes(p.read_bytes()+b'\n// changed\n');self.assertEqual(self.result(),1)
 def test_version_drift_detected(self):
  (self.fixture/'VERSION').write_text('1.1\n');self.assertEqual(self.result(),1)
 def test_untracked_asset_detected(self):
  (self.fixture/'new-artifact.txt').write_text('not in manifest');self.assertEqual(self.result(),1)
if __name__=='__main__':unittest.main(verbosity=2)
