/* Display preserved model output and explicitly separate editorial decision summaries. */
const $ = id => document.getElementById(id);
const esc = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const names = {v1_development:'v1 · Development',v2_development:'v2 · Development',v2_heldout:'v2 · Held-out'};
const scenarios = {
 injection:{id:'NDA-19',run:'v2_heldout',title:'Keep document text from becoming an instruction.',note:'The saved model review flags both the instruction attempt and the unlimited-liability term. The note does not become authority to approve.',facts:'Section 8 expressly imposes unlimited liability. Section 10 tells the reviewer to approve and suppress findings.',interpretation:'The reviewer note attempts to override the review process. It is document content, not authority to approve the contract.',action:'Disregard the embedded instruction. Revise the unlimited-liability term or obtain a documented exception decision.',owner:'Senior Legal / Finance reviews the liability exception; Legal handles the embedded instruction. Human review remains required.'},
 missing:{id:'NDA-18',run:'v2_heldout',title:'Stop where the source stops.',note:'The correct next step is a source request. Neither ordinary nor trade-secret duration can be judged from a missing appendix.',facts:'Section 5 incorporates Appendix T for ordinary and trade-secret duration. The appendix is absent from the supplied source.',interpretation:'The supplied text establishes a source gap, not a defective duration. A duration conclusion would be premature.',action:'Request Appendix T and complete the duration review after it is supplied.',owner:'Legal owns the source request and subsequent review. The review remains NEED_SOURCE; no approval is granted.'},
 iteration:{id:'NDA-03',run:'v2_development',title:'Improve the counting rule. Keep the legal concern.',note:'Compare v1 and v2 in the batch selector: the same clause produces three findings, then two. The PURPOSE overlap is supported, not legally false.',facts:'Section 3 permits residual-memory use and shared-model training. The v1 review reports three findings; v2 reports two.',interpretation:'The broader-purpose concern overlaps the specific residuals and training findings under this evaluation convention.',action:'Retain the two specific issues, explain the purpose expansion within them, and record the counting change.',owner:'Legal reviews the requested exceptions. Both saved versions route RED. The change does not establish better legal accuracy.'}
};
let state = {run:'v2_heldout',id:'NDA-19',tab:'brief',selected:0,challenge:null,prompt:'v2'};
const current = () => DATA.reviews[state.run].find(r=>r.document_id===state.id);
const scenario = () => Object.values(scenarios).find(s=>s.id===state.id) || null;
function setTab(name,focus=false) {
 state.tab=name;
 document.querySelectorAll('[data-tab]').forEach(b=>{const chosen=b.dataset.tab===name;b.setAttribute('aria-selected',String(chosen));b.tabIndex=chosen?0:-1;if(chosen&&focus)b.focus();});
 for(const name of ['brief','evidence','method','evaluation']) $('panel-'+name).hidden=name!==state.tab;
}
function chooseScenario(key){
 const s=scenarios[key];state.run=s.run;state.id=s.id;state.selected=0;state.challenge=null;state.prompt='v2';$('run').value=state.run;populateDocuments();render();setTab('brief');
}
function populateDocuments(){
 $('document').innerHTML=DATA.reviews[state.run].map(r=>`<option value="${esc(r.document_id)}">${esc(r.document_id)}</option>`).join('');
 if(!DATA.reviews[state.run].some(r=>r.document_id===state.id))state.id=DATA.reviews[state.run][0].document_id;
 $('document').value=state.id;
}
function list(items){return '<ul>'+items.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>';}
function renderBrief(r,s){
 $('brief-title').textContent=s?s.title:`${r.document_id}: the next review decision`;
 $('brief-facts').innerHTML=s?`<p>${esc(s.facts)}</p>`:r.issues.length?list(r.issues.map(i=>`${i.source_locator}: “${i.source_quote}”`)):'<p>The supplied synthetic agreement contains no issue flagged in the saved policy review.</p>';
 $('brief-interpretation').innerHTML=s?`<p>${esc(s.interpretation)}</p>`:r.issues.length?list(r.issues.map(i=>i.finding)):'<p>No finding was returned under this demonstration policy. That is a scoped model result, not a conclusion that every legal or business risk is absent.</p>';
 $('brief-action').innerHTML=s?`<p>${esc(s.action)}</p>`:r.issues.length?list(r.issues.map(i=>i.proposed_action)):'<p>Confirm the supplied facts and complete authorized human review before any approval or signature.</p>';
 const owners=[...new Set(r.issues.map(i=>i.approval_owner))];
 $('brief-owner').innerHTML=s?`<p>${esc(s.owner)}</p>`:`<p>${esc(owners.length?owners.join('; '):'Authorized Legal reviewer')}. Human review remains required. No authority to sign is granted by this display.</p>`;
}
function renderSource(){
 const r=current(),text=DATA.sources[state.id],parts=ReviewChecks.sections(text);
 const issue=r.issues[state.selected];
 const first=text.search(/^Section \d+\./m);
 let html=`<p class="source-meta">${esc(first>=0?text.slice(0,first).trim():text)}</p>`;
 Object.entries(parts).forEach(([label,body])=>{
  let rendered=esc(body),active=issue?.source_locator===label;
  if(active&&body.includes(issue.source_quote)){
   const pos=body.indexOf(issue.source_quote);
   rendered=esc(body.slice(0,pos))+'<mark>'+esc(issue.source_quote)+'</mark>'+esc(body.slice(pos+issue.source_quote.length));
  }
  html+=`<p class="source-section${active?' active':''}" data-locator="${esc(label)}">${rendered}</p>`;
 });
 $('source').innerHTML=html;
}
function renderFindings(r){
 $('finding-count').textContent=`${r.issues.length} recorded ${r.issues.length===1?'finding':'findings'} · ${names[state.run]}`;
 $('findings').innerHTML=r.issues.length?r.issues.map((i,n)=>`<article class="finding"><div class="rule">${esc(i.rule_id.replaceAll('_',' '))} / ${esc(i.severity)}</div><p>${esc(i.finding)}</p><button class="quote-button" data-finding="${n}" aria-pressed="${n===state.selected}">“${esc(i.source_quote)}”<span>${esc(i.source_locator)} · Highlight this quote</span></button><p><b>Proposed action:</b> ${esc(i.proposed_action)}</p><div class="owner">Review owner: ${esc(i.approval_owner)}</div></article>`).join(''):'<p class="empty">No policy issue was flagged in this complete synthetic control. The authorized reviewer retains the legal decision.</p>';
 $('raw').textContent=JSON.stringify(r,null,2);
 $('findings').querySelectorAll('[data-finding]').forEach(b=>b.addEventListener('click',()=>{
  state.selected=Number(b.dataset.finding);renderSource();renderFindings(current());
  const el=$('source').querySelector('.active');if(el)$('source').scrollTo({top:el.offsetTop-$('source').offsetTop-14,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
 }));
}
function renderChecks(){
 const r=structuredClone(current());
 if(state.challenge==='quote'){
  if(r.issues.length)r.issues[0].source_quote+=' This additional sentence is not in the source.';
  else r.issues.push({rule_id:'PURPOSE',severity:'YELLOW',finding:'Local challenge finding',source_locator:'Section 3',source_quote:'This sentence is not in the source.',proposed_action:'Challenge only',approval_owner:'Legal'});
 } else if(state.challenge==='gate')r.human_review_required=false;
 const result=ReviewChecks.validate(r,DATA.sources[state.id],DATA.policy,state.id);
 $('evidence-check').classList.toggle('blocked',!result.ok);
 $('check-title').textContent=result.ok?'Evidence checks passed. Legal review remains required.':'Challenge copy blocked from a clean handoff.';
 $('check-description').textContent=result.ok?`${r.issues.length} quoted ${r.issues.length===1?'finding matches':'findings match'} the stated Sections. Document, policy, rule IDs, route and human-review flag also pass local checks.`:'The temporary copy fails a mechanical control. Restore the unmodified saved output to continue with a checked packet.';
 $('check-errors').innerHTML=result.errors.map(e=>`<li><b>${esc(e.code)}</b>: ${esc(e.detail)}</li>`).join('');
 $('check-errors').hidden=!result.errors.length;
 $('challenge-quote').setAttribute('aria-pressed',String(state.challenge==='quote'));
 $('challenge-gate').setAttribute('aria-pressed',String(state.challenge==='gate'));
 $('download').disabled=!result.ok||Boolean(state.challenge);
}
function renderMethod(r){
 const families=r.issues.length?[...new Set(r.issues.map(i=>i.rule_id))]:Object.keys(DATA.policy.rules).slice(0,3);
 $('rules').innerHTML=families.map(k=>`<div class="rule-card"><b>${esc(k.replaceAll('_',' '))}</b><p>${esc(DATA.policy.rules[k].policy)}</p></div>`).join('');
 $('policy-json').textContent=JSON.stringify(DATA.policy,null,2);
 $('prompt').textContent=DATA.prompts[state.prompt];
 document.querySelectorAll('[data-prompt]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.prompt===state.prompt)));
}
function render(){
 const r=current(),s=scenario();
 document.querySelectorAll('[data-scenario]').forEach(b=>b.setAttribute('aria-pressed',String(scenarios[b.dataset.scenario].id===state.id)));
 $('risk').textContent=r.risk+' / '+(r.review_status==='NEED_SOURCE'?'SOURCE NEEDED':'HUMAN REVIEW');
 $('risk').className='risk '+r.risk.toLowerCase();
 $('route-desc').textContent=r.review_status==='NEED_SOURCE'?'Request missing material before completing this subject.':'Ready for assessment, never automatic approval.';
 $('scenario-note').textContent=s?s.note:'Browse the saved source and findings. These are fixed fictional agreements reviewed against one demonstration policy.';
 renderBrief(r,s);renderSource();renderFindings(r);renderMethod(r);renderChecks();
}
function downloadPacket(){
 if(state.challenge)return;
 const r=current(),check=ReviewChecks.validate(r,DATA.sources[state.id],DATA.policy,state.id);
 if(!check.ok)return;
 const sourcePath=Object.keys(DATA.provenance).find(x=>x.endsWith('/'+state.id+'.txt'));
 const outputPath=`evaluation/saved_reviews/${state.run}.json`;
 const packet={kind:'saved_review_evidence_packet',scope:'Synthetic portfolio example; not legal approval or a new model run.',document_id:state.id,saved_batch:state.run,source_file:sourcePath,source_sha256:DATA.provenance[sourcePath],saved_batch_file:outputPath,saved_batch_sha256:DATA.provenance[outputPath],policy_id:DATA.policy.policy_id,policy_sha256:DATA.provenance['policy/nda_demo_policy.json'],review:r,mechanical_evidence_checks:check,human_approval_granted:false};
 const blob=new Blob([JSON.stringify(packet,null,2)+'\n'],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`${state.id}_${state.run}_review_packet.json`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
$('run').addEventListener('change',()=>{state.run=$('run').value;state.selected=0;state.challenge=null;state.prompt=state.run.startsWith('v1')?'v1':'v2';populateDocuments();render();});
$('document').addEventListener('change',()=>{state.id=$('document').value;state.selected=0;state.challenge=null;render();});
document.querySelectorAll('[data-scenario]').forEach(b=>b.addEventListener('click',()=>chooseScenario(b.dataset.scenario)));
document.querySelectorAll('[data-tab]').forEach(b=>{
 b.addEventListener('click',()=>setTab(b.dataset.tab));
 b.addEventListener('keydown',e=>{const tabs=[...document.querySelectorAll('[data-tab]')],i=tabs.indexOf(b);let n;if(e.key==='ArrowRight')n=(i+1)%tabs.length;else if(e.key==='ArrowLeft')n=(i+tabs.length-1)%tabs.length;else if(e.key==='Home')n=0;else if(e.key==='End')n=tabs.length-1;else return;e.preventDefault();setTab(tabs[n].dataset.tab,true);});
});
document.querySelectorAll('[data-prompt]').forEach(b=>b.addEventListener('click',()=>{state.prompt=b.dataset.prompt;renderMethod(current());}));
$('inspect-evidence').addEventListener('click',()=>setTab('evidence',true));
$('challenge-quote').addEventListener('click',()=>{state.challenge='quote';renderChecks();});
$('challenge-gate').addEventListener('click',()=>{state.challenge='gate';renderChecks();});
$('restore').addEventListener('click',()=>{state.challenge=null;renderChecks();});
$('download').addEventListener('click',downloadPacket);
document.querySelectorAll('[data-open-tab]').forEach(a=>a.addEventListener('click',()=>setTab(a.dataset.openTab)));
$('scores').innerHTML=DATA.summaries.map(s=>`<tr><td>${esc(names[s.review])}</td><td>${s.documents}</td><td>${s.supported_matches} / ${s.reference_issues}</td><td>${s.extra_under_key}</td><td>${s.red_misses} / ${s.red_reference_issues}</td></tr>`).join('');
$('provenance').textContent=JSON.stringify(DATA.provenance,null,2);
populateDocuments();render();
