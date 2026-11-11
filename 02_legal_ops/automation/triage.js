'use strict';
const RED_FIELDS = ['personal_data','controlled_technology','shared_model_training',
  'unlimited_liability','commercial_exclusivity','residuals','sanctions_export_alert','other_red_flag'];
const YES = v => v === true || String(v).toLowerCase() === 'yes';
const NO = v => v === false || String(v).toLowerCase() === 'no';
function triage(r) {
  r = r && typeof r === 'object' ? r : {};
  const hasText = v => typeof v === 'string' && v.trim().length > 0;
  const red = RED_FIELDS.filter(k => YES(r[k]));
  const missing = [];
  if (!hasText(r.request_id) || !hasText(r.business_owner) || !['NDA','SaaS','Hardware supply','Equipment','Lease','Subcontract','Supply','Services','Other'].includes(r.type)) missing.push('valid request identity/type/owner');
  if (typeof r.value_usd !== 'number' || !Number.isFinite(r.value_usd) || r.value_usd < 0) missing.push('valid USD value');
  for (const k of RED_FIELDS) if (!YES(r[k]) && !NO(r[k])) missing.push(k);
  for (const k of ['entity_verified','signature_authority']) if (!YES(r[k])) missing.push(k);
  if (r.type === 'NDA') for (const k of ['template_unchanged','routine_purpose']) if (!YES(r[k]) && !NO(r[k])) missing.push(k);
  if (typeof r.value_usd === 'number' && Number.isFinite(r.value_usd) && r.value_usd >= 250000) red.push('value >= USD 250,000');
  let route, owners, reasons;
  // Known critical risk always stays visible, even when another input is missing.
  if (red.length) { route='RED'; owners=['Senior Legal','Finance','Business owner']; if (YES(r.personal_data)) owners.push('Privacy/Security'); if (YES(r.controlled_technology) || YES(r.sanctions_export_alert)) owners.push('Trade compliance specialist'); reasons=red; }
  else if (missing.length) { route='NEEDS INPUT'; owners=['Requester','Legal intake']; reasons=missing; }
  else if (r.value_usd >= 100000 || r.type !== 'NDA' || !YES(r.template_unchanged) || !YES(r.routine_purpose) || !YES(r.legal_reference_policy_validated)) {
    route='YELLOW'; owners=['Legal','Finance']; reasons=['Legal review required: value, document type or approved-paper gate'];
  } else { route='GREEN'; owners=['Authorized business delegate']; reasons=['Routine unchanged approved mutual NDA; eligibility gates satisfied']; }
  return {policy_id:'OPS-DEMO-1.0',request_id:r.request_id || null,route,owners,reasons,
    missing_inputs:missing,hold:route !== 'GREEN',approval_granted:false,
    instruction:route === 'GREEN' ? 'Eligible for approved self-service workflow only; delegation and signature controls still apply.' : 'Hold routing completion/execution until the named reviewers resolve the gate.'};
}
if (typeof module !== 'undefined') module.exports={triage,RED_FIELDS};
