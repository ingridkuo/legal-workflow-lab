"""Mutation tests for crosswalk integrity and misleading DMS authority claims."""
from pathlib import Path
import json, shutil, tempfile, unittest
from validate_taxonomy import ROOT, validate
class TaxonomyIntegrityTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='.taxonomy-test-',dir=ROOT)
  lab=Path(self.temp.name)/'lab';self.root=lab/'taxonomy'
  shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('.taxonomy-test-*','__pycache__'))
  for folder in ['inputs','policy']:shutil.copytree(ROOT.parent/folder,lab/folder)
  (lab/'evaluation').mkdir();shutil.copy2(ROOT.parent/'evaluation/reference_labels.json',lab/'evaluation/reference_labels.json')
 def tearDown(self):self.temp.cleanup()
 def mutate(self,name,fn):
  p=self.root/name;v=json.loads(p.read_text());fn(v);p.write_text(json.dumps(v))
 def test_valid_offline_package(self):self.assertEqual(validate(self.root)['status'],'PASS')
 def test_fabricated_iri_is_rejected(self):
  self.mutate('sali_issue_crosswalk.json',lambda x:x['rule_type_mappings'][0]['sali_targets'][0].update(iri='http://lmss.sali.org/fabricated'))
  with self.assertRaisesRegex(ValueError,'IRI and label'):validate(self.root)
 def test_missing_rule_is_rejected(self):
  self.mutate('sali_issue_crosswalk.json',lambda x:x['rule_type_mappings'].pop())
  with self.assertRaisesRegex(ValueError,'All local rule types'):validate(self.root)
 def test_duplicate_issue_instance_is_rejected(self):
  self.mutate('sali_issue_crosswalk.json',lambda x:x['heldout_issue_instances'].append(x['heldout_issue_instances'][0]))
  with self.assertRaisesRegex(ValueError,'All held-out issue instances'):validate(self.root)
 def test_changed_source_is_rejected(self):
  p=self.root.parent/'inputs/heldout/NDA-19.txt';p.write_text(p.read_text()+'\nChanged after review.\n')
  with self.assertRaisesRegex(ValueError,'source integrity'):validate(self.root)
 def test_hold_cannot_authorize_disclosure(self):
  self.mutate('dms_metadata_example.json',lambda x:x['legal_hold'].update(disclosure_authorized_by_hold=True))
  with self.assertRaisesRegex(ValueError,'Hold and disclosure'):validate(self.root)
 def test_classification_cannot_grant_approval(self):
  self.mutate('dms_metadata_example.json',lambda x:x['review'].update(approval_status='approved'))
  with self.assertRaisesRegex(ValueError,'Classification grants no approval'):validate(self.root)
 def test_changed_upstream_url_is_rejected_offline(self):
  self.mutate('sali_issue_crosswalk.json',lambda x:x['source'].update(source_url='http://127.0.0.1/internal'))
  with self.assertRaises(ValueError):validate(self.root)
if __name__=='__main__':unittest.main()
