"""Build exhibit pages from the archived demonstration results.

Python standard library only. This builder displays evidence; it does not execute
the migration validator, knowledge gate, or a model, and does not change their data.
"""
from pathlib import Path
import hashlib
import html
import json

ROOT = Path(__file__).resolve().parents[1]

CSS = r"""
@font-face{font-family:Inter;src:url('../assets/Inter.woff2') format('woff2');font-weight:100 900;font-display:swap}
:root{--ink:#172331;--muted:#5d6876;--accent:#4355db;--line:#e0e5eb;--paper:#f8f9fb;--sage:#edf3ef;--red:#963f38;--amber:#805e1d}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:28px}body{margin:0;color:var(--ink);background:var(--paper);font:16px/1.65 Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-feature-settings:'calt' 1,'tnum' 1}a{color:var(--accent);text-underline-offset:4px}button,select{font:inherit}a:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid #d4a42f;outline-offset:4px}button{cursor:pointer}header{border-bottom:1px solid var(--line);background:#fff}nav{display:flex;justify-content:space-between;align-items:center;gap:20px;max-width:1144px;padding:22px 32px;margin:auto}.identity{font-weight:650;text-decoration:none;color:var(--ink);letter-spacing:-.3px}.back{font-size:14px;text-decoration:none}main{max-width:1144px;padding:48px 32px 56px;margin:auto}.eyebrow{font-size:11px;letter-spacing:1.5px;text-transform:uppercase;font-weight:650;color:var(--accent)}h1{font-size:clamp(34px,4.8vw,54px);line-height:1.13;letter-spacing:-1.8px;font-weight:550;margin:17px 0 21px;max-width:850px}h2{font-size:27px;line-height:1.25;letter-spacing:-.8px;font-weight:600;margin:0}h3{font-size:18px;line-height:1.35;font-weight:600;margin:0 0 10px}p{margin:0 0 16px}.intro{font-size:18px;line-height:1.7;color:var(--muted);max-width:800px}.tagline{display:flex;gap:9px;flex-wrap:wrap;margin:25px 0 36px}.tag{font-size:12px;line-height:1.5;color:#52616d;border:1px solid var(--line);background:#fff;padding:6px 10px;border-radius:6px}.section-heading{display:flex;align-items:end;justify-content:space-between;gap:24px;margin:42px 0 20px}.section-heading p{font-size:14px;color:var(--muted);margin:0}.card{background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}.card-pad{padding:27px 28px}.switcher{display:inline-flex;gap:5px;border:1px solid var(--line);padding:5px;border-radius:9px;background:#f2f4f8}.switcher button{min-height:44px;padding:8px 18px;background:none;border:0;border-radius:5px;color:var(--muted);font-size:14px;font-weight:600}.switcher button[aria-pressed=true]{background:#fff;color:var(--accent);box-shadow:0 1px 4px #1d2b4112}.preview-head{display:flex;align-items:center;justify-content:space-between;gap:22px;padding:25px 28px;border-bottom:1px solid var(--line)}.preview-head p{font-size:14px;margin:7px 0 0;color:var(--muted)}.chip{display:inline-block;padding:5px 10px;border-radius:5px;font-size:11px;line-height:1.4;font-weight:650;letter-spacing:.5px;text-transform:uppercase}.chip.hold{background:#fbede8;color:var(--red)}.chip.ready{background:#eaf2ec;color:#3c624b}.chip.amber{background:#faf1da;color:var(--amber)}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;border-bottom:1px solid var(--line);padding:24px 0}.stat{padding:0 28px;border-left:1px solid var(--line)}.stat:first-child{border:0}.stat b{font-size:31px;line-height:1.1;font-weight:550;letter-spacing:-1px;display:block;margin-bottom:9px}.stat span{font-size:12px;color:var(--muted);display:block}.decision{margin:25px 28px;padding:19px 21px;border:1px solid #d9e5dc;border-radius:7px;background:var(--sage)}.decision.hold{background:#fcf5ed;border-color:#eedfca}.decision h3{font-size:15px;margin-bottom:7px}.decision p{font-size:14px;color:#4f6060;margin:0}.record-strip{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:8px;margin:19px 0 10px}.record{padding:14px 4px;text-align:center;font-size:11px;font-weight:600;border:1px solid #d8e4da;background:#f1f6f1;color:#45634d;border-radius:5px}.record.held{background:#fbf0e8;border-color:#e8d2c2;color:#83523b}.caption{font-size:12px;color:var(--muted)}.table-wrap{overflow:auto;max-width:100%}table{width:100%;border-collapse:collapse;font-size:13px}th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.7px;color:#687482;font-weight:650;background:#f5f6f8}th,td{padding:15px 17px;border-bottom:1px solid var(--line);vertical-align:top}td{line-height:1.6}td b{font-weight:600}tbody tr:last-child td{border-bottom:0}.check-name{display:block;font-size:11px;color:var(--muted);margin-top:5px}.muted{color:var(--muted)}.value{font:12px/1.6 ui-monospace,SFMono-Regular,Consolas,monospace;overflow-wrap:anywhere}.empty{padding:26px 28px;background:#f3f7f2;color:#3f6549;font-size:15px}.bar-head{display:flex;justify-content:space-between;align-items:center;gap:18px}.button{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:10px 17px;text-decoration:none;border-radius:6px;border:1px solid #ccd3df;font-size:13px;font-weight:600;color:var(--ink);background:#fff}.button.primary{background:var(--accent);color:#fff;border-color:var(--accent)}.actions{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:22px}.actions a:not(.button){font-size:13px}details{border:1px solid var(--line);border-radius:8px;background:#fff;margin-top:14px}summary{padding:18px 22px;cursor:pointer;min-height:56px;font-size:14px;font-weight:600;list-style-position:inside}details>div{padding:0 22px 22px}.details-copy{font-size:14px;max-width:800px;color:var(--muted)}pre{margin:13px 0 0;padding:17px 19px;background:#f3f5f8;border-radius:6px;font:12px/1.7 ui-monospace,SFMono-Regular,Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere}.split{display:grid;grid-template-columns:1fr 1fr;gap:28px}.fact-label{font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#69788a;font-weight:650;margin-bottom:9px}.scope{border-top:1px solid var(--line);padding-top:22px;margin-top:31px;color:var(--muted);font-size:12px;max-width:970px}.footer{border-top:1px solid var(--line);margin-top:44px;padding-top:23px;display:flex;justify-content:space-between;gap:20px;font-size:12px;color:var(--muted)}.footer a{text-decoration:none}.escalation-layout{display:grid;grid-template-columns:260px minmax(0,1fr);gap:22px;align-items:start}.case-menu{display:grid;gap:8px}.case-menu button{text-align:left;min-height:92px;border:1px solid var(--line);background:#fff;border-radius:8px;padding:18px 19px;color:var(--ink)}.case-menu button[aria-pressed=true]{border-color:var(--accent);box-shadow:inset 3px 0 var(--accent);background:#f4f5ff}.case-menu small{display:block;font-size:10px;letter-spacing:1px;color:var(--accent);margin-bottom:8px;font-weight:650}.case-menu b{display:block;font-size:14px;line-height:1.45;font-weight:600}.case-body{padding:27px 28px}.case-title{display:flex;justify-content:space-between;align-items:start;gap:18px;border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:23px}.case-title h3{font-size:22px;letter-spacing:-.5px;margin:6px 0 5px}.case-title p{font-size:12px;color:var(--muted);margin:0}.decision-quote{border-left:3px solid var(--accent);background:#f4f5fc;padding:19px 21px;border-radius:0 6px 6px 0;font-size:15px;margin-bottom:25px}.evidence-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px 27px}.evidence-grid section{border-top:1px solid var(--line);padding-top:16px}.evidence-grid h4{margin:0 0 10px;font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:#5a6f80}.evidence-grid p,.evidence-grid li{font-size:14px;line-height:1.7}.evidence-grid ul{padding-left:18px;margin:0}.evidence-grid li{margin-bottom:9px}.evidence-grid li:last-child{margin:0}.wide{grid-column:1/-1}blockquote{margin:11px 0;padding:14px 17px;border:1px solid #e0e4e7;border-radius:6px;color:#455563;font-size:13px;background:#fafbfc}.quote-fact{margin-top:4px;font-size:12px;color:var(--muted)}.articles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.article-card{padding:23px;border:1px solid var(--line);border-radius:10px;background:#fff}.article-card h3{font-size:16px;margin-top:14px;min-height:66px}.article-card p,.article-card li{font-size:12px;color:var(--muted)}.article-card ul{margin:15px 0;padding-left:17px}.article-card .button{margin-top:7px;font-size:12px;min-height:44px}.article-detail{margin-top:19px;display:none}.article-detail.visible{display:block}.article-meta{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px;border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:19px}.article-meta span{font-size:11px;display:block;color:var(--muted);margin-bottom:4px}.article-meta b{font-size:13px;font-weight:600}.close-row{display:flex;justify-content:space-between;gap:20px;align-items:center}.text-button{border:0;background:none;color:var(--accent);min-height:44px;font-size:13px;text-decoration:underline;text-underline-offset:4px;padding:5px 0}noscript{display:block;padding:20px;background:#fff4d7;color:#705c28}.sr-only{position:absolute;width:1px;height:1px;clip:rect(0,0,0,0);overflow:hidden}
@media(max-width:900px){.escalation-layout{grid-template-columns:210px minmax(0,1fr)}.stat{padding:0 20px}.record-strip{gap:5px}.record{font-size:10px}.evidence-grid{grid-template-columns:1fr}.wide{grid-column:auto}}
@media(max-width:700px){nav{padding:18px 20px;gap:12px}.identity{font-size:14px}.back{font-size:12px}main{padding:32px 20px 40px}h1{font-size:36px;letter-spacing:-1.1px}.intro{font-size:16px}.tagline{margin-bottom:28px}.section-heading{align-items:start;flex-direction:column;gap:9px;margin-top:31px}h2{font-size:24px}.preview-head{padding:22px;align-items:start;flex-direction:column}.stats{grid-template-columns:1fr 1fr;row-gap:22px}.stat:nth-child(3){border-left:0}.stat b{font-size:28px}.decision{margin:21px;padding:17px}.card-pad,.case-body{padding:22px}.record-strip{grid-template-columns:repeat(4,minmax(0,1fr));gap:7px}.record{font-size:11px;padding:12px 3px}.split{grid-template-columns:1fr;gap:19px}.bar-head{align-items:start;flex-direction:column;gap:9px}.escalation-layout{grid-template-columns:1fr}.case-menu{grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}.case-menu button{padding:12px 10px;min-height:118px}.case-menu b{font-size:12px}.case-menu small{font-size:9px}.case-title{display:block}.case-title .chip{margin-top:14px}.articles{grid-template-columns:1fr}.article-card h3{min-height:0}.article-meta{grid-template-columns:1fr 1fr}.footer{flex-direction:column;gap:8px}.footer p{margin:0}.exception-table thead{display:none}.exception-table,.exception-table tbody,.exception-table tr,.exception-table td{display:block;width:100%}.exception-table tr{padding:18px 22px;border-bottom:1px solid var(--line)}.exception-table td{border:0;padding:6px 0}.exception-table td::before{content:attr(data-label);display:block;font-size:10px;letter-spacing:.7px;text-transform:uppercase;color:var(--muted);margin-bottom:3px}.exception-table tr:last-child{border:0}.mapping-table{min-width:580px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""


def load(path):
    return json.loads(path.read_text())


def inline(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def shell(title, body, script):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{html.escape(title)}: inspect the working example and evidence by Ingrid Kao."><title>{html.escape(title)} | Ingrid Kao</title><style>{CSS}</style></head><body>
<header><nav aria-label="Exhibit navigation"><a class="identity" href="../index.html">Ingrid Kao <span class="muted">/ Selected work</span></a><a class="back" href="../index.html#work">Back to work samples ↗</a></nav></header>
<main>{body}<footer class="footer"><p>Ingrid Kao · Commercial contracts, legal operations and legal AI</p><p><a href="mailto:kuoingrid0118@gmail.com">Contact</a> · <a href="../Ingrid_Kao_Work_Samples.pdf">Application PDF</a></p></footer></main><script>{script}</script></body></html>
'''


MIGRATION_BODY = '''
<span class="eyebrow">Working example / Data quality</span>
<h1>Verify the move.<br>Keep the exceptions visible.</h1>
<p class="intro">At Lawsnote, I validated a migration of more than 10,000 contract records through field mapping and import checks. This fictional example makes that checking method inspectable.</p>
<div class="tagline"><span class="tag">XML → JSON</span><span class="tag">Independent source comparison</span><span class="tag">Eight fictional contracts</span></div>
<section aria-labelledby="batch-heading"><div class="section-heading"><h2 id="batch-heading">Compare the two saved batches</h2><p>Change the batch to see what the next owner receives.</p></div>
<div class="card"><div class="preview-head"><div><h3 id="batch-title">Flawed import</h3><p id="batch-subtitle"></p></div><div class="switcher" role="group" aria-label="Saved import batch"><button data-batch="flawed" aria-pressed="true">Before correction</button><button data-batch="corrected" aria-pressed="false">After correction</button></div></div>
<div class="stats" aria-live="polite" aria-atomic="true"><div class="stat"><b id="record-count"></b><span>Destination records</span></div><div class="stat"><b id="held-count"></b><span>Records held</span></div><div class="stat"><b id="clean-count"></b><span>Records clean</span></div><div class="stat"><b id="issue-count"></b><span>Exception types</span></div></div>
<div class="card-pad"><div class="bar-head"><h3>Every source record remains accounted for.</h3><span class="chip" id="reconcile-status"></span></div><div class="record-strip" id="record-strip" aria-label="Per-record validation status"></div><p class="caption">These labels show metadata-check results, not a production release decision.</p></div>
<div class="decision" id="release-decision"><h3 id="release-title"></h3><p id="release-copy"></p></div>
</div></section>
<section aria-labelledby="exceptions-heading"><div class="section-heading"><h2 id="exceptions-heading">The exception handoff</h2><p>Expected value, observed value and next action stay together.</p></div><div class="card"><div id="exceptions"></div></div><div class="actions"><a class="button" id="report-download" href="results/flawed_report.json" download>Download the saved report ↓</a><a href="README.md">Code, fixtures and reproduction guide</a></div></section>
<section aria-labelledby="controls-heading"><div class="section-heading"><h2 id="controls-heading">What is checked</h2><p>Executable controls, with a defined boundary.</p></div><div class="split"><article class="card card-pad"><h3>Compare the destination with an independent source</h3><p class="details-copy">The check does not validate a transformation against itself. It compares the XML export with the separately saved JSON destination, using a source-to-destination crosswalk.</p><p class="details-copy">Source IDs, revisions, required owners, dates and access metadata remain visible when a record is held.</p></article><article class="card card-pad"><h3>Preserve meaning during import</h3><p class="details-copy">Amounts use exact decimals. A missing amount stays null; a known zero stays zero. DTD/entity input is rejected, and destination identifiers are checked for case-insensitive collisions.</p><p class="details-copy">Metadata matching does not establish that real system permissions are enforced.</p></article></div>
<details><summary>Inspect the field mapping</summary><div><div class="table-wrap"><table class="mapping-table"><thead><tr><th>XML source</th><th>JSON field</th><th>Transformation</th></tr></thead><tbody id="mapping"></tbody></table></div><p class="caption" id="access-groups"></p></div></details>
<details><summary>Reproduce the fixed example</summary><div><p class="details-copy" id="test-summary"></p><pre id="commands"></pre><div class="actions"><a href="fixtures/source_contracts.xml">XML source</a><a href="fixtures/target_flawed.json">Flawed destination</a><a href="fixtures/target_corrected.json">Corrected destination</a><a href="results/demo_facts.json">Verification facts</a></div></div></details></section>
<p class="scope">This page displays archived results for deliberately flawed and corrected fictional fixtures. Changing the view does not rerun the validator. The Python code and tests are included. Record-owner signoff and platform checks remain separate release requirements.</p>
<noscript>This exhibit needs JavaScript for the batch switcher. The saved reports, field mapping and reproduction guide remain available in this folder.</noscript>
'''

MIGRATION_SCRIPT = r'''
const DATA=@@DATA@@;
const $=id=>document.getElementById(id);
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const value=v=>v===''?'[blank]':v===null?'null':String(v);
let active='flawed';
function render(){
 const r=DATA.reports[active],held=new Set(r.exceptions.flatMap(e=>e.source_record_id.split(',').map(x=>x.trim())));
 document.querySelectorAll('[data-batch]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.batch===active)));
 $('batch-title').textContent=active==='flawed'?'Flawed import':'Corrected import';
 $('batch-subtitle').textContent=`Source: ${r.source_records} records · Destination: ${r.destination_records} records · As of ${r.as_of_date}`;
 $('record-count').textContent=r.destination_records;$('held-count').textContent=r.held_records;$('clean-count').textContent=r.clean_records;$('issue-count').textContent=r.exception_types.length;
 $('reconcile-status').textContent=r.counts_reconcile?'Counts reconcile':'Reconciliation needed';$('reconcile-status').className='chip '+(r.counts_reconcile?'ready':'hold');
 $('record-strip').innerHTML=DATA.ids.map(id=>`<span class="record${held.has(id)?' held':''}" aria-label="${esc(id)} ${held.has(id)?'held for correction':'clean'}">${esc(id)}<br>${held.has(id)?'Held':'Clean'}</span>`).join('');
 const clean=r.validation_gate_passed;
 $('release-decision').className='decision'+(clean?'':' hold');
 $('release-title').textContent=clean?'Ready for owner signoff':'Hold for correction';
 $('release-copy').textContent=clean?'All eight records pass these metadata checks. The record owner still needs to sign off, and actual platform permissions need verification. Release approval remains false.':'Correct the five affected records against the source, then rerun validation. A duplicated destination ID affects two records, so four exception types hold five records.';
 $('exceptions').innerHTML=r.exceptions.length?'<table class="exception-table"><thead><tr><th>Record / check</th><th>Expected</th><th>Observed</th><th>Owner and next action</th></tr></thead><tbody>'+r.exceptions.map(e=>`<tr><td data-label="Record / check"><b>${esc(e.source_record_id)}</b><span class="check-name">${esc(e.code.replaceAll('_',' '))}<br>${esc(e.field)}</span></td><td data-label="Expected"><span class="value">${esc(value(e.expected))}</span></td><td data-label="Observed"><span class="value">${esc(value(e.actual))}</span></td><td data-label="Owner and next action"><b>${esc(e.owner)}</b><br>${esc(e.action)}</td></tr>`).join('')+'</tbody></table>':'<div class="empty"><b>No exceptions in the corrected fixture.</b><br>All eight records are clean. The batch is ready for record-owner signoff.</div>';
 $('report-download').href=`results/${active}_report.json`;
}
document.querySelectorAll('[data-batch]').forEach(b=>b.addEventListener('click',()=>{active=b.dataset.batch;render()}));
$('mapping').innerHTML=DATA.mapping.fields.map(f=>`<tr><td class="value">${esc(f.xml_source)}</td><td class="value">${esc(f.target_field)}</td><td>${esc(f.transform)}${f.nullable?' · nullable':''}</td></tr>`).join('');
$('access-groups').textContent='Allowed metadata groups: '+DATA.mapping.approved_access_groups.join(', ')+'.';
$('commands').textContent='cd 05_solution_delivery\n'+DATA.facts.reproduce_command+'\n'+DATA.facts.test_command+'\n'+DATA.facts.verification_command;
$('test-summary').textContent=`${DATA.facts.tests_passed} of ${DATA.facts.test_count} behavioral tests passed. ${DATA.facts.verified_report_files.length} archived reports match a fresh run. This page reports that saved verification; the commands below reproduce it.`;
render();
'''

KNOWLEDGE_BODY = '''
<span class="eyebrow">Working example / Knowledge and escalation</span>
<h1>Separate the facts.<br>Keep the next owner clear.</h1>
<p class="intro">A usable handoff distinguishes the source from the interpretation, names what is missing, and gives the next person a specific action. These fictional packets show that structure in practice.</p>
<div class="tagline"><span class="tag">Source-backed handoffs</span><span class="tag">Approval and version checks</span><span class="tag">Synthetic local workflow</span></div>
<section aria-labelledby="handoff-heading"><div class="section-heading"><h2 id="handoff-heading">Inspect an escalation</h2><p>Three saved packets. Each keeps a named reviewer.</p></div><div class="escalation-layout"><div class="case-menu" role="group" aria-label="Escalation packet"><button data-case="ESC-101" aria-pressed="true"><small>ESC-101</small><b>Retention and export request</b></button><button data-case="ESC-102" aria-pressed="false"><small>ESC-102</small><b>Termination and refund request</b></button><button data-case="ESC-103" aria-pressed="false"><small>ESC-103</small><b>NDA residuals exception</b></button></div><article class="card case-body" aria-live="polite"><div class="case-title"><div><span class="eyebrow" id="case-id"></span><h3 id="case-title"></h3><p id="case-channel"></p></div><span class="chip hold">Named review required</span></div><div class="decision-quote" id="case-decision"></div><div class="evidence-grid"><section class="wide"><h4>Confirmed facts and their source</h4><div id="case-facts"></div></section><section><h4>Interpretation</h4><div id="case-interpretation"></div></section><section><h4>Still unknown</h4><div id="case-unknowns"></div></section><section class="wide"><h4>Owner and next action</h4><p id="case-owner"></p><p id="case-next"></p></section></div><details><summary>Inspect the source and structured packet</summary><div><p class="details-copy" id="case-check"></p><pre id="case-hash"></pre><div class="actions"><a id="case-source" href="escalations/sources/ESC-101.txt">Read the source</a><a id="case-record" href="escalations/ESC-101.json">Open the JSON packet</a></div></div></details></article></div></section>
<section aria-labelledby="guidance-heading"><div class="section-heading"><h2 id="guidance-heading">Check guidance before use</h2><p id="article-scope"></p></div><div class="articles" id="article-cards"></div><article class="card card-pad article-detail" id="article-detail" aria-live="polite"><div class="close-row"><h3 id="article-title"></h3><button class="text-button" id="close-article">Close details</button></div><div class="article-meta" id="article-meta"></div><div class="split"><section><div class="fact-label">Gate result</div><div id="article-reasons"></div><div class="fact-label" style="margin-top:20px">Permitted sample roles</div><p class="details-copy" id="article-roles"></p></section><section><div class="fact-label">Approval record</div><p class="details-copy" id="article-approval"></p><p class="details-copy">Approvals are simulated workflow records. Eligibility means the article passes this local gate on the stated date; it does not authenticate a real person or grant authority to act.</p></section></div><details><summary>Inspect the text and bound source snapshots</summary><div><pre id="article-text"></pre><pre id="article-snapshots"></pre></div></details></article></section>
<section aria-labelledby="gate-heading"><div class="section-heading"><h2 id="gate-heading">What makes the gate useful</h2><p>Proposed controls with inspectable checks.</p></div><div class="split"><article class="card card-pad"><h3>Keep the approval attached to the text</h3><p class="details-copy">The gate checks the article hash, approved version, independent reviewer, review date and cited policy snapshots. Changed content cannot silently inherit an old approval.</p></article><article class="card card-pad"><h3>Keep facts attached to a source</h3><p class="details-copy">Each recorded fact needs its own exact quote. Missing authority fields, invalid dates and source paths outside the collection fail the local checks.</p></article></div><details><summary>Reproduce the saved checks</summary><div><p class="details-copy" id="knowledge-test-summary"></p><pre id="knowledge-commands"></pre><div class="actions"><a href="README.md">Code and reproduction guide</a><a href="results/summary.json">Saved summary</a><a href="results/demo_facts.json">Verification facts</a><a href="Management_Handoff.md">Management handoff</a></div></div></details></section>
<p class="scope">The records, policies and approvals are fictional. This page displays saved local results as of the stated date; it does not execute operational actions. In ESC-101, preservation is requested and acknowledgment is still open. Disclosure and export remain blocked pending verification and Counsel approval.</p>
<noscript>This exhibit needs JavaScript for packet selection. The source messages, structured records and saved gate results remain available in this folder.</noscript>
'''

KNOWLEDGE_SCRIPT = r'''
const DATA=@@DATA@@;
const $=id=>document.getElementById(id);
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const titles={'ESC-101':'Retention and export request','ESC-102':'Termination and refund request','ESC-103':'NDA residuals exception'};
let active='ESC-101';
function list(items){return '<ul>'+items.map(i=>`<li>${esc(i)}</li>`).join('')+'</ul>'}
function renderCase(){
 const c=DATA.cases.find(x=>x.id===active),check=DATA.caseChecks.find(x=>x.id===active);
 document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.case===active)));
 $('case-id').textContent=c.id;$('case-title').textContent=titles[c.id];$('case-channel').textContent=c.channel+' · Received '+c.received;$('case-decision').textContent=c.decision;
 $('case-facts').innerHTML=c.fact_support.map(f=>`<p>${esc(f.fact)}</p><blockquote>“${esc(f.quote)}”</blockquote>`).join('');
 $('case-interpretation').innerHTML=list(c.interpretations);$('case-unknowns').innerHTML=list(c.unknowns);$('case-owner').innerHTML=`<b>${esc(c.owner)}</b> → ${esc(c.named_reviewer)}`;$('case-next').textContent=c.next_action;
 $('case-check').textContent=check.ok?'The saved packet passes the local source, structure and named-review checks. No action authority is granted.':'The saved packet needs correction before handoff.';
 $('case-hash').textContent='Source SHA-256\n'+c.source.sha256;
 $('case-source').href='escalations/'+c.source.path;$('case-record').href='escalations/'+c.id+'.json';
}
function showArticle(id){
 const a=DATA.registry.find(x=>x.id===id),check=DATA.articleChecks.find(x=>x.id===id),approval=DATA.approvals.find(x=>x.approval_id===a.approval_id);
 $('article-detail').classList.add('visible');$('article-title').textContent=id+' / '+a.title;
 $('article-meta').innerHTML=[['Version',a.version],['Owner',a.owner],['Last reviewed',a.reviewed_on||'Not recorded'],['Review due',a.next_review_due||'Not recorded'],['Status',a.status],['Gate as of',DATA.facts.as_of]].map(([label,v])=>`<div><span>${esc(label)}</span><b>${esc(v)}</b></div>`).join('');
 $('article-reasons').innerHTML=check.eligible?'<p class="details-copy">Eligible for the permitted sample roles. The recorded text, approval and source snapshots pass the fixed local checks.</p>':list(check.reasons);
 $('article-roles').textContent=a.access_roles.join(', ');
 $('article-approval').textContent=approval?`${approval.approval_id} · ${approval.approver} · ${approval.approved_on} · ${approval.record_type}`:'No approval record is attached to this article.';
 $('article-text').textContent=DATA.articleText[id];$('article-snapshots').textContent=JSON.stringify({article_sha256:a.sha256,source_snapshots:a.sources},null,2);
 document.querySelectorAll('[data-article]').forEach(b=>b.setAttribute('aria-expanded',String(b.dataset.article===id)));
 $('article-title').scrollIntoView({block:'nearest',behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'});
}
document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>{active=b.dataset.case;renderCase()}));
$('article-scope').textContent=`As of ${DATA.facts.as_of}: ${DATA.facts.articles.eligible} eligible, ${DATA.facts.articles.blocked} blocked.`;
$('article-cards').innerHTML=DATA.articleChecks.map(a=>`<article class="article-card"><span class="chip ${a.eligible?'ready':a.status==='draft'?'amber':'hold'}">${a.eligible?'Eligible':a.status==='draft'?'Draft blocked':'Review overdue'}</span><h3>${esc(a.title)}</h3><p>${esc(a.id)} · Version ${a.version}</p>${a.reasons.length?'<ul>'+a.reasons.map(x=>`<li>${esc(x)}</li>`).join('')+'</ul>':'<p>Approval, text, sources and dates pass the saved local check.</p>'}<button class="button" data-article="${esc(a.id)}" aria-expanded="false" aria-controls="article-detail">Inspect the gate →</button></article>`).join('');
document.querySelectorAll('[data-article]').forEach(b=>b.addEventListener('click',()=>showArticle(b.dataset.article)));
$('close-article').addEventListener('click',()=>{$('article-detail').classList.remove('visible');document.querySelectorAll('[data-article]').forEach(b=>b.setAttribute('aria-expanded','false'))});
$('knowledge-test-summary').textContent=`${DATA.facts.tests.tests_run} behavioral tests passed. ${DATA.facts.escalations.packets_passing} of ${DATA.facts.escalations.total} escalation packets pass; all retain named review gates. Article results are evaluated against the fixed date ${DATA.facts.as_of}.`;
$('knowledge-commands').textContent='cd 06_knowledge_operations\n'+DATA.facts.primary_commands.join('\n');
renderCase();
'''


def build_migration():
    folder = ROOT/'05_solution_delivery'
    facts = load(folder/'results/demo_facts.json')
    reports = {key:load(folder/f'results/{key}_report.json') for key in ('flawed','corrected')}
    source = load(folder/'results/normalized_source.json')
    if isinstance(source, dict):
        records = source.get('records', source.get('contracts', []))
    else:
        records = source
    ids = [r['source_record_id'] for r in records]
    assert len(ids) == facts['scenarios']['flawed']['source_records']
    assert len(set(ids)) == len(ids)
    for key, report in reports.items():
        for field in ['source_records','destination_records','held_records','clean_records','exception_count','release_approved']:
            assert report[field] == facts['scenarios'][key][field], (key, field)
        assert report['held_records']+report['clean_records']==report['destination_records']
    data = {'facts':facts,'reports':reports,'mapping':load(folder/'field_mapping.json'),'ids':ids}
    script = MIGRATION_SCRIPT.replace('@@DATA@@',inline(data))
    output = folder/'index.html'
    output.write_text(shell('Migration validation', MIGRATION_BODY, script))
    return output


def build_knowledge():
    folder = ROOT/'06_knowledge_operations'
    cases = [load(p) for p in sorted((folder/'escalations').glob('ESC-*.json'))]
    for case in cases:
        source = folder/'escalations'/case['source']['path']
        assert hashlib.sha256(source.read_bytes()).hexdigest()==case['source']['sha256']
        text = source.read_text()
        assert all(s['quote'] in text and s['fact'] in case['known_facts'] for s in case['fact_support'])
        assert not any(case['authority_granted'].values())
    registry = load(folder/'knowledge/registry.json')['articles']
    data = {'facts':load(folder/'results/demo_facts.json'),'cases':cases,'caseChecks':load(folder/'results/escalation_checks.json'),'articleChecks':load(folder/'results/article_checks.json'),'registry':registry,'approvals':load(folder/'knowledge/approvals.json'),'articleText':{a['id']:(folder/'knowledge'/a['path']).read_text() for a in registry}}
    output = folder/'index.html'
    output.write_text(shell('Knowledge and escalation',KNOWLEDGE_BODY,KNOWLEDGE_SCRIPT.replace('@@DATA@@',inline(data))))
    return output


def main():
    for output in [build_migration(),build_knowledge()]:
        print('Built '+str(output.relative_to(ROOT))+' from saved evidence.')


if __name__ == '__main__':
    main()
