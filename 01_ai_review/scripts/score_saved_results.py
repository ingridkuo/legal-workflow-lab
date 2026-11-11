"""Rescore the saved synthetic NDA reviews with Python's standard library.
Run from any directory: python3 scripts/score_saved_results.py
This script validates saved outputs; it does not call a model.
"""
from pathlib import Path
import csv, hashlib, json, re
ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads(path.read_text())
def ratio(n,d): return None if d==0 else n/d

def main():
    key=load(ROOT/'evaluation/reference_labels.json')
    policy=load(ROOT/'policy/nda_demo_policy.json')
    all_rows=[]; evidence=[]; summaries=[]
    for name,split in [('v1_development','development'),('v2_development','development'),('v2_heldout','heldout')]:
        cases={c['document_id']:c for c in key['cases'] if c['split']==split}
        reviews=load(ROOT/f'evaluation/saved_reviews/{name}.json')
        assert len(reviews)==len(cases) and {r['document_id'] for r in reviews}==set(cases)
        assert len({r['document_id'] for r in reviews})==len(reviews)
        rows=[]
        for r in reviews:
            case=cases[r['document_id']]; source=(ROOT/case['input_path']).read_text()
            assert hashlib.sha256(source.encode()).hexdigest()==case['sha256'], 'Source differs from reference record'
            sections={f'Section {m.group(1)}':m.group(2) for m in re.finditer(r'^Section (\d+)\. (.*?)(?=^Section \d+\.|\Z)',source,re.M|re.S)}
            expected={x['rule_id']:x for x in case['expected']}
            flags={x['rule_id']:x for x in r['issues']}
            assert len(flags)==len(r['issues']), 'Duplicate document-rule finding'
            assert set(flags)<=set(policy['rules'])
            supported=set(); quote_errors=locator_errors=severity_errors=0
            for rule,f in flags.items():
                quote_ok=bool(f['source_quote']) and f['source_quote'] in source
                locator_ok=f['source_locator'] in sections and f['source_quote'] in sections.get(f['source_locator'],'')
                if quote_ok and locator_ok: supported.add(rule)
                quote_errors+=not quote_ok; locator_errors+=not locator_ok
                severity_errors+=rule in expected and f['severity']!=expected[rule]['severity']
                evidence.append({'review':name,'document_id':r['document_id'],'rule_id':rule,'matches_reference_family':rule in expected,'quote_in_source':quote_ok,'quote_in_stated_section':locator_ok,'source_locator':f['source_locator']})
            matched=set(expected)&supported
            route='RED' if any(x['severity']=='RED' for x in expected.values()) else 'YELLOW' if expected else 'GREEN'
            status='NEED_SOURCE' if 'SOURCE_COMPLETENESS' in expected else 'REVIEW_READY'
            row={'review':name,'document_id':r['document_id'],'reference_issues':len(expected),'red_reference_issues':sum(x['severity']=='RED' for x in expected.values()),'returned_findings':len(flags),'supported_matches':len(matched),'extra_under_key':len(flags)-len(matched),'missed_reference_issues':len(set(expected)-matched),'red_misses':sum(expected[x]['severity']=='RED' for x in set(expected)-matched),'unsupported_quotes':quote_errors,'wrong_locations':locator_errors,'severity_differences':severity_errors,'route_differences':int(r['risk']!=route),'status_differences':int(r['review_status']!=status),'human_gate_errors':int(r['human_review_required'] is not True)}
            rows.append(row);all_rows.append(row)
        totals={k:sum(x[k] for x in rows) for k in rows[0] if k not in ['review','document_id']}
        totals.update({'review':name,'documents':len(rows),'precision':ratio(totals['supported_matches'],totals['returned_findings']),'recall':ratio(totals['supported_matches'],totals['reference_issues'])})
        summaries.append(totals)
    out={'scope':'Synthetic evaluation; policy-rule match, source quote and location checks.','counting':'One document_id plus rule_id. Exact source support is required for a match. Extra under key includes supported cross-family overlap; it is not a legal-falsity determination.','review_credit':key['review_credit'],'reviews':summaries}
    (ROOT/'evaluation/results_summary.json').write_text(json.dumps(out,indent=2)+'\n')
    for name,rows in [('document_scores.csv',all_rows),('evidence_checks.csv',evidence)]:
        with (ROOT/'evaluation'/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(summaries,indent=2))
if __name__=='__main__':main()
