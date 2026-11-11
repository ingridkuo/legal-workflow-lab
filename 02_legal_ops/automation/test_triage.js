'use strict';
const assert=require('node:assert/strict');
const {triage,RED_FIELDS}=require('./triage');
const {normalizeRequest,BOOL_KEYS}=require('./normalize_request');
const base={request_id:'REQ-001',type:'NDA',business_owner:'Maya Chen',value_usd:99999,entity_verified:true,signature_authority:true,template_unchanged:true,routine_purpose:true,legal_reference_policy_validated:true};
for(const field of RED_FIELDS)base[field]=false;
let count=0;
function expectRoute(name,patch,expected){const result=triage({...base,...patch});assert.equal(result.route,expected,name);assert.equal(result.approval_granted,false,name);count++;}
for(const [value,route]of[[0,'GREEN'],[99999,'GREEN'],[100000,'YELLOW'],[249999,'YELLOW'],[250000,'RED'],[250001,'RED'],[null,'NEEDS INPUT'],[-1,'NEEDS INPUT'],['250000','NEEDS INPUT'],[Infinity,'NEEDS INPUT'],[NaN,'NEEDS INPUT']])expectRoute('amount '+String(value),{value_usd:value},route);
for(const field of RED_FIELDS){expectRoute(field+' true',{[field]:true},'RED');expectRoute(field+' unknown',{[field]:null},'NEEDS INPUT');expectRoute(field+' critical with missing amount',{[field]:true,value_usd:null},'RED');}
for(const type of['Supply','SaaS','Services','Hardware supply','Equipment','Lease','Subcontract','Other'])expectRoute('non-NDA '+type,{type},'YELLOW');
for(const field of['request_id','business_owner','type'])expectRoute('blank '+field,{[field]:' '},'NEEDS INPUT');
for(const field of['entity_verified','signature_authority','template_unchanged','routine_purpose'])expectRoute('missing '+field,{[field]:null},'NEEDS INPUT');
expectRoute('changed NDA',{template_unchanged:false},'YELLOW');expectRoute('non-routine purpose',{routine_purpose:false},'YELLOW');expectRoute('policy not validated',{legal_reference_policy_validated:false},'YELLOW');expectRoute('high value and missing verification',{value_usd:250000,entity_verified:null},'RED');
assert(triage({...base,personal_data:true}).owners.includes('Privacy/Security'));count++;
assert(triage({...base,controlled_technology:true}).owners.includes('Trade compliance specialist'));count++;
for(const amount of['$1,000','1,000','1 000','','-1','NaN','Infinity']){assert.equal(normalizeRequest({value_usd:amount}).value_usd,null,amount);count++;}
for(const [amount,expected]of[['0',0],['100000',100000],['250000.25',250000.25],['.5',0.5]]){assert.equal(normalizeRequest({value_usd:amount}).value_usd,expected);count++;}
for(const field of BOOL_KEYS){assert.equal(normalizeRequest({[field]:' Yes '})[field],true);assert.equal(normalizeRequest({[field]:'No'})[field],false);assert.equal(normalizeRequest({[field]:'Unknown'})[field],null);count++;}
assert.equal(normalizeRequest(null).value_usd,null);count++;
assert.equal(normalizeRequest({value_usd:'0',legal_reference_policy_validated:true}).legal_reference_policy_validated,false);count++;
assert.equal(normalizeRequest({value_usd:'0'},{policyValidated:true}).legal_reference_policy_validated,true);count++;
const labels=normalizeRequest({'request_id | Reference':[' REQ-002 '],'business_owner':[' Maya Chen '],value_usd:['0']});assert.equal(labels.request_id,'REQ-002');assert.equal(labels.business_owner,'Maya Chen');assert.equal(labels.value_usd,0);count++;
console.log(`${count} tests passed.`);
