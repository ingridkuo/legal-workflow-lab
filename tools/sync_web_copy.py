"""Build the recruiter homepage from canonical case and demonstration evidence."""
from pathlib import Path
import html
import json

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT/'tools'
esc = html.escape
cases = json.loads((ROOT/'04_case_studies/case_studies.json').read_text())
by_id = {row['n']:row for row in cases}
migration = json.loads((ROOT/'05_solution_delivery/results/demo_facts.json').read_text())
knowledge = json.loads((ROOT/'06_knowledge_operations/results/demo_facts.json').read_text())
reviews = json.loads((ROOT/'01_ai_review/evaluation/saved_reviews/v2_heldout.json').read_text())
review = next(row for row in reviews if row['document_id']=='NDA-19')
finding = next(row for row in review['issues'] if row['rule_id']=='EMBEDDED_INSTRUCTION')
triage = (HERE/'homepage_triage.js').read_text()
assert (ROOT/'02_legal_ops/automation/triage.js').read_text().strip() in triage

outcomes=[]
for n,label,title in [('01','Technology license','Resolved the ownership impasse.'),('02','Cloud services','Made the liability-cap issue visible.'),('05','Legal data permission','Obtained permission for the product’s data source.')]:
    c=by_id[n]
    contribution = c['featured_summary'].split(';')[0].split('. ')[0].rstrip('.') + '.'
    outcomes.append(f'<article class="outcome-card"><p class="kicker">{esc(label)}</p><h3>{esc(title)}</h3><p>{esc(contribution)}</p><div class="outcome-result"><span aria-hidden="true"></span><strong>{esc(c["outcome"])}</strong></div></article>')
details=[]
for c in cases:
    details.append(f'<details class="case-detail"><summary><span class="case-number">{esc(c["n"])}</span><span>{esc(c["title"])}</span><span class="plus" aria-hidden="true">+</span></summary><div class="case-body"><p class="kicker">{esc(c["context"])}</p><p>{esc(c["body"])}</p><p class="case-outcome"><strong>{esc(c.get("result_label","Outcome"))}:</strong> {esc(c["outcome"])}</p></div></details>')
values={'@@OUTCOME_CARDS@@':''.join(outcomes),'@@CASE_DETAILS@@':''.join(details),'@@SOURCE_QUOTE@@':esc(finding['source_quote']),'@@SOURCE_LOCATOR@@':esc(finding['source_locator']),'@@SAVED_FINDING@@':esc(finding['finding']),'@@MIGRATION_TESTS@@':str(migration['test_count']),'@@KNOWLEDGE_TESTS@@':str(knowledge['tests']['tests_run']),'@@TRIAGE_SCRIPT@@':triage}
s=(HERE/'homepage_template.html').read_text()
for key,value in values.items():
    assert key in s,key
    s=s.replace(key,value)
assert '@@' not in s
(ROOT/'index.html').write_text(s)
print('Built professional homepage from canonical cases, saved model output and demonstrated facts.')
