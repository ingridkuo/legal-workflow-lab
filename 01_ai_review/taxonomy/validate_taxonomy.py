"""Validate the NDA crosswalk and DMS design. Standard-library only.
Offline: python3 validate_taxonomy.py
Verify pinned official source too: python3 validate_taxonomy.py --verify-upstream
The default command checks included evidence; it does not contact a DMS or SALI.
"""
from pathlib import Path
import argparse, hashlib, json, urllib.request, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
PIN='3f9ac0c9357b2a971582ae79ede243511d47811d'
SOURCE_SHA='51acefd5051aa8f52e60d6dd142b0925c7cec3a5d789bfbe4fcbe69021c9bba1'
SOURCE_URL=f'https://raw.githubusercontent.com/sali-legal/LMSS/{PIN}/LMSS.owl'
RDF='{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'
NS={'owl':'http://www.w3.org/2002/07/owl#','rdfs':'http://www.w3.org/2000/01/rdf-schema#','skos':'http://www.w3.org/2004/02/skos/core#'}
def load(p):return json.loads(p.read_text())
def validate(root=ROOT,upstream_bytes=None):
 lab=root.parent;cross=load(root/'sali_issue_crosswalk.json');excerpt=load(root/'sources/selected_sali_concepts.json');dms=load(root/'dms_metadata_example.json');policy=load(lab/'policy/nda_demo_policy.json');key=load(lab/'evaluation/reference_labels.json')
 checks=[]
 def check(ok,name):
  if not ok:raise ValueError(name)
  checks.append(name)
 check(hashlib.sha256((root/'sources/selected_sali_concepts.json').read_bytes()).hexdigest()==cross['selected_concepts_sha256'],'Source excerpt hash')
 check(cross['source']==excerpt['source'],'Common source pin')
 check(cross['source']['commit']==PIN and cross['source']['source_sha256']==SOURCE_SHA and cross['source']['source_url']==SOURCE_URL,'Pinned official source revision, hash and URL')
 concepts={c['iri']:c for c in excerpt['concepts']}
 check(len(concepts)==len(excerpt['concepts']),'Unique source IRIs')
 maps={m['local_rule_id']:m for m in cross['rule_type_mappings']}
 check(len(maps)==len(cross['rule_type_mappings']) and set(maps)==set(policy['rules']),'All local rule types covered once')
 for rule,m in maps.items():
  check(m['relationship'] in cross['relationship_definitions'],rule+': relationship vocabulary')
  check(bool(m['gap_note']) and bool(m['relationship_scope']),rule+': explicit gap and scope')
  check(m['local_policy_id']==policy['policy_id'],rule+': policy identity')
  check((m['relationship']=='unmapped')==(not m['sali_targets']),rule+': unmapped has no false target')
  for target in m['sali_targets']:
   check(target['iri'] in concepts and target['label']==concepts[target['iri']]['label'],rule+': IRI and label match source')
 expected={(c['document_id'],e['rule_id']):(c,e) for c in key['cases'] if c['split']=='heldout' for e in c['expected']}
 actual={(i['document_id'],i['rule_id']):i for i in cross['heldout_issue_instances']}
 check(len(actual)==len(cross['heldout_issue_instances']) and set(actual)==set(expected),'All held-out issue instances covered once')
 check(cross['scope']['local_rule_types']==len(maps) and cross['scope']['heldout_reference_issue_instances']==len(expected),'Instance and type counts separated')
 for pair,i in actual.items():
  c,e=expected[pair];m=maps[pair[1]]
  check(i['source_sha256']==c['sha256'] and i['source_locator']==e['source_locator'] and i['reference_severity']==e['severity'],i['issue_instance_id']+': reference linkage')
  source=(root/i['source_path']).resolve()
  check(source.is_relative_to(lab.resolve()) and source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest()==i['source_sha256'],i['issue_instance_id']+': actual source integrity')
  check(i['sali_targets']==m['sali_targets'] and i['relationship']==m['relationship'],i['issue_instance_id']+': crosswalk consistency')
 doc=dms['document'];p=(root/doc['content_path']).resolve()
 check(p.is_relative_to(lab.resolve()) and p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==doc['content_sha256'],'DMS document version binds exact content')
 check(doc['document_type']['sali_iri'] in concepts and doc['document_type']['label']==concepts[doc['document_type']['sali_iri']]['label'],'DMS document type is source-backed')
 check(dms['access']['acl_is_enforced'] is False and dms['record_kind']=='fictional_dms_metadata_design','DMS implementation scope is honest')
 check(dms['retention']['deletion_authorized'] is False and dms['retention']['trigger_date'] is None and dms['retention']['disposition_due_date'] is None,'No invented disposition authority or date')
 check(dms['legal_hold']['suspend_disposition_if_active'] is True and dms['legal_hold']['disclosure_authorized_by_hold'] is False,'Hold and disclosure are separate')
 check(dms['review']['human_review_required'] is True and dms['review']['approval_status']=='not_granted','Classification grants no approval')
 check(set(dms['review']['rule_ids_are_local_not_sali'])<=set(policy['rules']),'Local rules remain separate from SALI IRIs')
 mode='offline_included_source_excerpt'
 if upstream_bytes is not None:
  check(hashlib.sha256(upstream_bytes).hexdigest()==cross['source']['source_sha256'],'Full official pinned OWL hash')
  xml=ET.fromstring(upstream_bytes)
  nodes={c.get(RDF+'about'):c for c in xml.findall('owl:Class',NS)}
  for iri,c in concepts.items():
   check(iri in nodes,'Official source contains '+iri)
   node=nodes[iri]
   check(c['label']==node.findtext('rdfs:label',default='',namespaces=NS),'Official label '+iri)
   check(c['definition']==node.findtext('skos:definition',default='',namespaces=NS),'Official definition '+iri)
   parents=[x.get(RDF+'resource') for x in node.findall('rdfs:subClassOf',NS) if x.get(RDF+'resource')]
   check(c['parent_iris']==parents,'Official direct parents '+iri)
  mode='official_upstream_verified'
 return {'status':'PASS','mode':mode,'checks_passed':len(checks),'rule_types':len(maps),'heldout_issue_instances':len(actual),'selected_source_concepts':len(concepts),'source_commit':cross['source']['commit']}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify-upstream',action='store_true');parser.add_argument('--write-result',type=Path);args=parser.parse_args()
 raw=None
 if args.verify_upstream:
  source=load(ROOT/'sali_issue_crosswalk.json')['source']
  if source['source_url']!=SOURCE_URL:raise ValueError('Unexpected source URL')
  raw=urllib.request.urlopen(SOURCE_URL,timeout=60).read()
 result=validate(upstream_bytes=raw)
 if args.write_result:args.write_result.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
