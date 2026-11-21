/* The view a link can carry: one saved batch, one document, one tab, one finding and the prompt on screen.
   A link names the prompt only when it is not the one the batch was run with.
   A plain anchor (#review-workspace) is not a view and is left to the browser. */
const ReviewView = (() => {
  const TABS = ['brief', 'evidence', 'method', 'evaluation'];
  const RUNS = ['v2_heldout', 'v2_development', 'v1_development'];
  const PROMPTS = ['v1', 'v2'];
  const promptOf = run => (run.startsWith('v1') ? 'v1' : 'v2');
  function parse(hash, reviews) {
    const text = String(hash || '').replace(/^#/, '');
    if (!text.includes('=')) return null;
    const p = new URLSearchParams(text);
    const doc = p.get('doc');
    const has = (run, id) => Object.hasOwn(reviews, run) && reviews[run].some(r => r.document_id === id);
    let run = p.get('run');
    if (!Object.hasOwn(reviews, run || '')) run = RUNS.find(r => doc && has(r, doc)) || null;
    if (!run) return null;
    const id = doc && has(run, doc) ? doc : reviews[run][0].document_id;
    const issues = reviews[run].find(r => r.document_id === id).issues;
    const n = Number(p.get('finding'));
    const tabGiven = TABS.includes(p.get('tab'));
    return {run, id, tab: tabGiven ? p.get('tab') : 'brief', tabGiven,
            selected: Number.isInteger(n) && n >= 1 && n <= issues.length ? n - 1 : 0,
            prompt: PROMPTS.includes(p.get('prompt')) ? p.get('prompt') : promptOf(run)};
  }
  function format(view) {
    const p = new URLSearchParams({doc: view.id, run: view.run});
    if (view.tab && view.tab !== 'brief') p.set('tab', view.tab);
    if (view.selected) p.set('finding', String(view.selected + 1));
    if (PROMPTS.includes(view.prompt) && view.prompt !== promptOf(view.run)) p.set('prompt', view.prompt);
    return '#' + p.toString();
  }
  return {parse, format, promptOf, TABS, PROMPTS};
})();
if (typeof module !== 'undefined') module.exports = ReviewView;
