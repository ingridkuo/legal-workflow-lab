/* Shared mechanical evidence checks. This code does not assess legal correctness. */
const ReviewChecks = (() => {
  function sections(source) {
    const matches = [...String(source).matchAll(/^Section (\d+)\./gm)];
    return Object.fromEntries(matches.map((m, i) => [`Section ${m[1]}`, source.slice(m.index, matches[i + 1]?.index ?? source.length).trim()]));
  }
  function validate(review, source, policy, expectedId) {
    const errors = [], evidence = [];
    const fail = (code, detail) => errors.push({code, detail});
    if (!review || typeof review !== 'object' || Array.isArray(review)) return {ok:false,errors:[{code:'SCHEMA',detail:'A review object is required.'}],evidence:[]};
    if (review.document_id !== expectedId || !source.includes(`Document ID ${expectedId}\n`)) fail('DOCUMENT_ID', 'Review and supplied source must identify the same document.');
    if (review.policy_id !== policy.policy_id) fail('POLICY_ID', 'The supplied policy version must match the review.');
    if (review.human_review_required !== true) fail('HUMAN_GATE', 'Human review must remain explicitly required.');
    if (!['REVIEW_READY','NEED_SOURCE'].includes(review.review_status)) fail('STATUS', 'Unknown review status.');
    if (!['GREEN','YELLOW','RED'].includes(review.risk)) fail('RISK', 'Unknown routing risk.');
    if (!Array.isArray(review.issues)) { fail('ISSUES', 'Findings must be an array.'); return {ok:false,errors,evidence}; }
    const bySection = sections(source), seen = new Set();
    review.issues.forEach((issue, i) => {
      const prefix = `Finding ${i + 1}`;
      if (!issue || typeof issue !== 'object') { fail('ISSUE_SCHEMA', `${prefix}: a finding object is required.`); return; }
      if (!Object.hasOwn(policy.rules, issue.rule_id)) fail('RULE_ID', `${prefix}: unknown policy family.`);
      if (seen.has(issue.rule_id)) fail('DUPLICATE_RULE', `${prefix}: duplicate rule family in one document.`);
      seen.add(issue.rule_id);
      if (!['RED','YELLOW'].includes(issue.severity)) fail('SEVERITY', `${prefix}: invalid issue severity.`);
      for (const field of ['finding','proposed_action','approval_owner']) if (typeof issue[field] !== 'string' || !issue[field].trim()) fail('REQUIRED_FIELD', `${prefix}: ${field} is required.`);
      const section = bySection[issue.source_locator], quote = issue.source_quote;
      const ok = typeof quote === 'string' && quote.trim().length > 0 && typeof section === 'string' && section.includes(quote);
      evidence.push({rule_id:issue.rule_id,source_locator:issue.source_locator,quote_supported_in_section:ok});
      if (!ok) fail('SOURCE_QUOTE', `${prefix}: the exact quote is absent from its stated Section.`);
    });
    const top = review.issues.some(i=>i?.severity==='RED') ? 'RED' : review.issues.length ? 'YELLOW' : 'GREEN';
    if (review.risk !== top) fail('ROUTING', 'The highest finding severity must determine the route.');
    const gap = review.issues.some(i=>i?.rule_id==='SOURCE_COMPLETENESS');
    if (gap !== (review.review_status==='NEED_SOURCE')) fail('SOURCE_STATUS', 'A source-completeness finding requires NEED_SOURCE.');
    return {ok:errors.length===0,errors,evidence};
  }
  return {sections,validate};
})();
if (typeof module !== 'undefined') module.exports = ReviewChecks;
