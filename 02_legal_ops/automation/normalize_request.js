"use strict";
const BOOL_KEYS=['entity_verified','signature_authority','template_unchanged','routine_purpose','personal_data','controlled_technology','shared_model_training','unlimited_liability','commercial_exclusivity','residuals','sanctions_export_alert','other_red_flag'];
function normalizeRequest(answers,config={}) {
 const raw={};
 if(answers && typeof answers==='object' && !Array.isArray(answers))for(const [key,entry]of Object.entries(answers))raw[key.split(' | ')[0]]=Array.isArray(entry)?entry[0]:entry;
 const bool=v=>v===true||String(v).trim().toLowerCase()==='yes'?true:v===false||String(v).trim().toLowerCase()==='no'?false:null;
 const amount=String(raw.value_usd??'').trim();
 const parsed=/^(?:\d+(?:\.\d+)?|\.\d+)$/.test(amount)?Number(amount):null;
 const result={request_id:String(raw.request_id??'').trim(),business_owner:String(raw.business_owner??'').trim(),type:raw.type??null,value_usd:Number.isFinite(parsed)?parsed:null};
 for(const key of BOOL_KEYS)result[key]=bool(raw[key]);
 result.legal_reference_policy_validated=config.policyValidated===true;
 return result;
}
module.exports={normalizeRequest,BOOL_KEYS};
