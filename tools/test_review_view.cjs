/* The replay's shareable links: a copied link opens the same document, tab and finding. Page state only. */
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const view = require('./review_demo_view.cjs'), root = path.resolve(__dirname, '../01_ai_review');
const reviews = Object.fromEntries(['v1_development', 'v2_development', 'v2_heldout']
  .map(n => [n, JSON.parse(fs.readFileSync(path.join(root, `evaluation/saved_reviews/${n}.json`), 'utf8'))]));
const find = (run, id) => reviews[run].find(r => r.document_id === id);
let cases = 0; const test = (name, fn) => { fn(); cases++; console.log('PASS ' + name); };

test('a shared link opens NDA-18 at Section 5, where Appendix T is missing', () => {
  const v = view.parse('#doc=NDA-18&run=v2_heldout&tab=evidence', reviews);
  assert.deepEqual([v.run, v.id, v.tab, v.selected], ['v2_heldout', 'NDA-18', 'evidence', 0]);
  const issue = find(v.run, v.id).issues[v.selected];
  assert.equal(issue.source_locator, 'Section 5');
  assert.match(issue.source_quote, /Appendix T has not been supplied/);
});
test('the finding number in a link is the finding shown', () => {
  const v = view.parse('#doc=NDA-19&run=v2_heldout&tab=evidence&finding=2', reviews);
  assert.equal(find(v.run, v.id).issues[v.selected].source_locator, 'Section 10');
});
test('every view a page can show survives its own link', () => {
  for (const run of Object.keys(reviews)) for (const r of reviews[run]) for (const tab of view.TABS)
    for (let selected = 0; selected < Math.max(1, r.issues.length); selected++) for (const prompt of view.PROMPTS) {
      const back = view.parse(view.format({run, id: r.document_id, tab, selected, prompt}), reviews);
      assert.deepEqual([back.run, back.id, back.tab, back.selected, back.prompt], [run, r.document_id, tab, selected, prompt]);
    }
});
test('the prompt on screen travels with the link', () => {
  const shared = view.format({run: 'v2_heldout', id: 'NDA-19', tab: 'method', selected: 0, prompt: 'v1'});
  assert.equal(shared, '#doc=NDA-19&run=v2_heldout&tab=method&prompt=v1');
  assert.equal(view.parse(shared, reviews).prompt, 'v1');
  assert.equal(view.format({run: 'v2_heldout', id: 'NDA-19', tab: 'brief', selected: 0, prompt: 'v2'}), '#doc=NDA-19&run=v2_heldout');
  assert.equal(view.parse('#doc=NDA-19&run=v2_heldout', reviews).prompt, 'v2');
  assert.equal(view.parse('#doc=NDA-01&run=v1_development', reviews).prompt, 'v1');
  assert.equal(view.parse('#doc=NDA-19&run=v2_heldout&prompt=v9', reviews).prompt, 'v2');
});
test('a document without a batch opens in the batch that holds it', () => {
  assert.equal(view.parse('#doc=NDA-03', reviews).run, 'v2_development');
  assert.equal(view.parse('#doc=NDA-18', reviews).run, 'v2_heldout');
});
test('a plain anchor is not a view', () => {
  assert.equal(view.parse('#review-workspace', reviews), null);
  assert.equal(view.parse('', reviews), null);
});
test('unknown values fall back instead of failing', () => {
  assert.equal(view.parse('#doc=NDA-99&run=nope', reviews), null);
  const v = view.parse('#doc=NDA-99&run=v2_heldout&tab=settings&finding=9', reviews);
  assert.deepEqual([v.id, v.tab, v.selected], [reviews.v2_heldout[0].document_id, 'brief', 0]);
  assert.equal(view.parse('#doc=NDA-19&run=__proto__', reviews).run, 'v2_heldout');
});
console.log(`${cases} link tests passed. Page state only; the saved reviews are read, not changed.`);
