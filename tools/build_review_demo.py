"""Build the offline saved-model demonstration from preserved evidence files."""
from pathlib import Path
import hashlib
import json
import argparse
import base64
import re

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT/'tools'
LAB = ROOT/'01_ai_review'
REVIEWS = ('v1_development','v2_development','v2_heldout')
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def build(standalone=False):
    reviews={k:json.loads((LAB/f'evaluation/saved_reviews/{k}.json').read_text()) for k in REVIEWS}
    source_paths=sorted((LAB/'inputs').rglob('NDA-*.txt'))
    paths=[LAB/'policy/nda_demo_policy.json']+[LAB/f'evaluation/saved_reviews/{k}.json' for k in REVIEWS]+source_paths+[LAB/'prompts/review_v1.md',LAB/'prompts/review_v2.md']
    data={
        'reviews':reviews,
        'sources':{p.stem:p.read_text() for p in source_paths},
        'policy':json.loads((LAB/'policy/nda_demo_policy.json').read_text()),
        'prompts':{v:(LAB/f'prompts/review_{v}.md').read_text() for v in ['v1','v2']},
        'summaries':json.loads((LAB/'evaluation/results_summary.json').read_text())['reviews'],
        'provenance':{str(p.relative_to(LAB)):digest(p) for p in paths},
    }
    template=(HERE/'review_demo_template.html').read_text()
    data_text=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    for key,value in [('@@DATA@@',data_text),('@@CORE@@',(HERE/'review_demo_core.cjs').read_text()),('@@APP@@',(HERE/'review_demo_app.js').read_text())]:
        assert template.count(key)==1,key
        template=template.replace(key,value)
    (LAB/'replay.html').write_text(template)
    print('Built offline saved-model demonstration (20 source documents, three archived batches).')
    if standalone:
        single=template
        for font in ['Inter.woff2']:
            encoded=base64.b64encode((ROOT/'assets'/font).read_bytes()).decode('ascii')
            single=single.replace("../assets/"+font, "data:font/woff2;base64,"+encoded)
        single=single.replace('href="../index.html" aria-label="Ingrid Kao portfolio"', 'href="#title" aria-label="Demonstration home"')
        single=single.replace('<a class="back" href="../index.html">← Portfolio</a>', '<a class="back" href="#demo-about">About this demo</a>')
        single=single.replace('<a href="AI_Contract_Review_Method.pdf">Read the method brief ↗</a>', '<a href="#review-workspace" data-open-tab="method">Inspect the rules &amp; prompts ↓</a>')
        single=re.sub(r'<div class="lower-links">.*?</div>', '<section id="demo-about" class="evaluation-note"><h3>About this demonstration</h3><p>This self-contained file displays preserved model outputs against fictional source documents. Select a scenario, inspect exact quotes, and test the local evidence checks. No account, upload or live model is involved.</p><p>The companion portfolio package contains the full method brief, reference-label review record, controls design, source files and reproducible builders. This file grants no legal approval or authority to sign.</p></section>',single)
        if re.search(r'(?:href|src)="(?:\.\.?/|AI_Contract_Review|Controls_)',single):
            raise ValueError('A companion-file link remains in the standalone demonstration')
        destination=ROOT.parent/'AI_Review_Demonstration.html'
        destination.write_text(single)
        print('Built standalone offline demonstration: '+str(destination))
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--standalone',action='store_true',help='Also write one self-contained HTML beside the public folder.')
    build(parser.parse_args().standalone)
