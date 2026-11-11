"""Build the author-created NDA/SALI crosswalk from a pinned official OWL source.
Run: python3 build_crosswalk.py --source /path/to/LMSS.owl
No model calls. Never changes the Lab policy or reference labels.
"""
from pathlib import Path
import argparse, collections, hashlib, json, urllib.request, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
LAB=ROOT.parent
PIN='3f9ac0c9357b2a971582ae79ede243511d47811d'
SOURCE_SHA='51acefd5051aa8f52e60d6dd142b0925c7cec3a5d789bfbe4fcbe69021c9bba1'
RAW=f'https://raw.githubusercontent.com/sali-legal/LMSS/{PIN}/LMSS.owl'
NS={'owl':'http://www.w3.org/2002/07/owl#','rdfs':'http://www.w3.org/2000/01/rdf-schema#','skos':'http://www.w3.org/2004/02/skos/core#'}
RDF='{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'
def write(name,data):
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path);args=parser.parse_args()
 raw=args.source.read_bytes() if args.source else urllib.request.urlopen(RAW,timeout=60).read()
 assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA,'Pinned source hash mismatch'
 xml=ET.fromstring(raw);by_label={}
 for c in xml.findall('owl:Class',NS):
  label=c.findtext('rdfs:label',default='',namespaces=NS)
  if label in by_label:continue
  by_label[label]={'iri':c.get(RDF+'about'),'label':label,'definition':c.findtext('skos:definition',default='',namespaces=NS),'parent_iris':[p.get(RDF+'resource') for p in c.findall('rdfs:subClassOf',NS) if p.get(RDF+'resource')]}
 specs=[
 ('DURATION','broader',['Survival Clause'],'Five-year survival, the three-year fallback and the disclosure-window distinction are local policy tests; the SALI tag identifies the broader clause topic.'),
 ('TRADE_SECRET','related',['Trade Secret Law','Confidentiality Clause'],'Area-of-law and clause-topic tags do not encode duration while information remains a qualifying trade secret or decide whether a fixed cap is acceptable.'),
 ('RESIDUALS','broader',['Confidentiality Clause'],'No exact residual-memory NDA exception concept was identified in the pinned source. Use the broader confidentiality topic and preserve RESIDUALS as a local rule.'),
 ('PURPOSE','broader',['Confidentiality Clause'],'The confidentiality topic is broader than an evaluation-only use restriction. The privacy-specific Purpose Specification Principle was not substituted for a commercial NDA use rule.'),
 ('MODEL_TRAINING','related',['Machine Learning','Confidentiality Clause'],'Machine Learning supplies technical context, not permission to train on confidential data. Separate express approval and shared-model scope remain local policy fields.'),
 ('REPRESENTATIVES','related',['Permitted Disclosure Clause','"Representatives" Definition'],'The definition and disclosure topic do not encode need-to-know access, equivalent duties, professional-duty carveouts or recipient responsibility.'),
 ('COMPELLED_NOTICE','broader',['Legally Compelled Disclosure Clause'],'The common disclosure topic does not distinguish lawful notice and cooperation from a prohibited notice obligation. Keep this rule separate from compelled scope.'),
 ('COMPELLED_SCOPE','broader',['Legally Compelled Disclosure Clause'],'The common disclosure topic does not encode the minimum-legally-required production limit. Two distinct local rules intentionally share one SALI concept.'),
 ('RETENTION','related',['Retention and Litigation Hold Management'],'This is an operational preservation topic, not an NDA return/destruction clause equivalent. Thirty-day timing, inactive backup and legal-retention exceptions remain local policy. A hold suspends deletion; it does not authorize disclosure.'),
 ('COMMERCIAL_RESTRICTION','related',['Exclusive Agreement Clause','Non-Competition Covenant'],'These tags cover examples of the rule, not its full scope: no-hire, IP transfer and other commercial commitments need their own analysis. The instance mapping retains the actual noncompete context.'),
 ('SOURCE_COMPLETENESS','unmapped',[],'No exact source-completeness or missing-incorporated-contract-source concept was identified. Do not use the SALI Attachment concept: its definition concerns prejudgment seizure, not a missing contract attachment. Keep NEED_SOURCE as local workflow state.'),
 ('EMBEDDED_INSTRUCTION','related',['Adversarial Machine Learning'],'The SALI concept describes a broader attack domain. It is not an exact indirect prompt-injection or contract-review rule; instruction isolation and the human gate remain local controls.'),
 ('UNLIMITED_LIABILITY','broader',['Liability Clause'],'The broad topic is liability allocation. A Limitation of Liability Clause is not an exact match for an express unlimited obligation; lack of a cap alone is not a defect under this policy.'),
 ('PERSONAL_DATA','related',['Data Privacy Clause','Data Protection Agreement'],'These tags support privacy routing and retrieval. They do not determine whether a DPA is required, whether processing is authorized or whether a privacy review has occurred.'),
 ('CONTROLLED_TECH','related',['Export Controls Practice'],'Practice-area context is not an export classification, license decision or finding of an actual violation. No Export Control Claims tag is applied solely because technical data may be controlled.')]
 used=set();mappings=[]
 policy=json.loads((LAB/'policy/nda_demo_policy.json').read_text())
 key=json.loads((LAB/'evaluation/reference_labels.json').read_text())
 for rule,relation,labels,gap in specs:
  targets=[{'iri':by_label[l]['iri'],'label':l} for l in labels];used.update(labels)
  mappings.append({'local_rule_id':rule,'local_policy_id':policy['policy_id'],'relationship':relation,'relationship_scope':'subject-matter mapping; not equivalence to policy test, severity or approval','sali_targets':targets,'gap_note':gap})
 by_rule={m['local_rule_id']:m for m in mappings}
 instances=[]
 for c in key['cases']:
  if c['split']!='heldout':continue
  for e in c['expected']:
   m=by_rule[e['rule_id']]
   instances.append({'issue_instance_id':c['document_id']+'::'+e['rule_id'],'document_id':c['document_id'],'source_path':'../'+c['input_path'],'source_sha256':c['sha256'],'rule_id':e['rule_id'],'reference_severity':e['severity'],'source_locator':e['source_locator'],'relationship':m['relationship'],'sali_targets':m['sali_targets'],'gap_note':m['gap_note']})
 dmslabels=['Nondisclosure Agreement','Document Management','Document Version','Draft Document Version','Legal Hold Management'];used.update(dmslabels)
 selected=[by_label[l] for l in sorted(used)]
 provenance={'publisher':'SALI Alliance','repository':'https://github.com/sali-legal/LMSS','commit':PIN,'commit_date_utc':'2026-03-10T23:01:15Z','retrieved_on':'2026-11-11','source_url':RAW,'source_sha256':SOURCE_SHA,'source_bytes':len(raw),'version_scope':'Pinned main commit; not represented as a formal release','license_in_repository':'MIT; original notice retained in sources/SALI_LICENSE.txt','standard_website_license_note':'The SALI website separately describes CC BY-ND. This package provides an author-created crosswalk and compact verbatim source records; it does not alter or republish the ontology as a competing standard.'}
 write('sources/selected_sali_concepts.json',{'source':provenance,'selection':'Verbatim labels, definitions and direct parent IRIs selected from the pinned official OWL source. This is a compact source excerpt, not a complete ontology.','concepts':selected})
 excerpt_sha=hashlib.sha256((ROOT/'sources/selected_sali_concepts.json').read_bytes()).hexdigest()
 write('sali_issue_crosswalk.json',{'schema_version':'1.0','author':'Ingrid Kao','mapping_status':'Author-created portfolio crosswalk; not a SALI-endorsed mapping','scope':{'local_rule_types':len(mappings),'heldout_documents':15,'heldout_reference_issue_instances':len(instances),'instance_key':'document_id plus rule_id'},'source':provenance,'selected_concepts_sha256':excerpt_sha,'relationship_definitions':{'exact':'Same subject concept; would still not establish equivalence to a local risk rule. None claimed here.','broader':'SALI topic is broader than the local issue concept.','related':'Useful context or retrieval relationship; neither equivalence nor asserted subsumption.','unmapped':'No adequate concept identified in this pinned source; local rule is retained.'},'rule_type_mappings':mappings,'heldout_issue_instances':instances})
 nda=LAB/'inputs/heldout/NDA-19.txt'
 doc_tag=by_label['Nondisclosure Agreement'];version_tag=by_label['Draft Document Version']
 write('dms_metadata_example.json',{'schema_version':'1.0','record_kind':'fictional_dms_metadata_design','implementation_status':'Architecture example; no vendor DMS connection or live access-control enforcement','matter':{'matter_id':'DEMO-MAT-001','name':'Aster Vale evaluation NDA','client_entity':'Aster Vale Systems Inc. (fictional)','responsible_role':'Legal'},'document':{'document_id':'DEMO-DOC-019','source_document_id':'NDA-19','version_id':'DEMO-DOC-019-v1','version_number':1,'supersedes_version_id':None,'status':'draft','content_path':'../inputs/heldout/NDA-19.txt','content_sha256':hashlib.sha256(nda.read_bytes()).hexdigest(),'mime_type':'text/plain','document_type':{'label':doc_tag['label'],'sali_iri':doc_tag['iri']},'version_classification':{'label':version_tag['label'],'sali_iri':version_tag['iri']},'incorporated_sources':[]},'access':{'classification':'synthetic-public-demonstration','business_acl_group_ids':['DEMO-LEGAL','DEMO-FINANCE'],'read_roles':['Legal','Finance'],'edit_roles':['Legal'],'export_roles':['Legal'],'acl_is_enforced':False,'note':'Illustrative role assignments only. SALI topic tags and the model route grant no permissions.'},'retention':{'schedule_id':'DEMO-RET-001','basis':'Fictional schedule: owner review after matter closure','trigger_event':'matter_closed','trigger_date':None,'disposition_due_date':None,'deletion_authorized':False,'note':'Do not invent a retention date before the triggering event or conflate the NDA return/destruction rule with an organizational records schedule.'},'legal_hold':{'status':'none_reported_in_demo','hold_id':None,'hold_owner_role':'Legal','suspend_disposition_if_active':True,'release_requires_role':'Legal','disclosure_authorized_by_hold':False},'provenance':{'source':'Synthetic NDA fixture','ingest_actor':'portfolio-import-demo','ingest_date':'2026-11-11','sali_commit':PIN,'review_policy_id':policy['policy_id'],'review_output_is_separate_record':True},'review':{'review_record_id':'DEMO-REV-019','policy_id':policy['policy_id'],'human_review_required':True,'risk_route':'RED','approval_status':'not_granted','issue_instances':['NDA-19::UNLIMITED_LIABILITY','NDA-19::EMBEDDED_INSTRUCTION'],'rule_ids_are_local_not_sali':['UNLIMITED_LIABILITY','EMBEDDED_INSTRUCTION']}})
 print(json.dumps({'rule_types':len(mappings),'heldout_issue_instances':len(instances),'selected_sali_concepts':len(selected),'relationships':dict(collections.Counter(m['relationship'] for m in mappings))},indent=2))
if __name__=='__main__':main()
