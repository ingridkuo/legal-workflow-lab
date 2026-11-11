"""Build the one-page observed-results brief and the method addendum."""
from pathlib import Path
import json
from build_ai_method import MethodPDF, register_fonts, markdown

PUB = Path(__file__).resolve().parents[1]
LAB = PUB / '01_ai_review'

def make_page(summary):
    runs = summary['runs']
    c = summary['consistency']
    pct = lambda n: 'undefined' if n is None else f'{n:.0%}'
    return {
        'kicker': '06 / Repeated generation study',
        'title': 'Same request. Three observed batches.',
        'subtitle': '15 synthetic NDAs reviewed three times; findings checked against source text and reviewed reference labels.',
        'blocks': [
            {'type':'p','text':'The three isolated agent batches received the same frozen prompt, policy, schema and source documents. Reference labels were excluded from reviewer inputs. Each batch reviewed all 15 documents in a shared context: 45 document reviews in total.'},
            {'type':'table','headers':['Batch','TP / FP / FN','Precision','Recall'], 'widths':[96,180,126,126], 'rows':[[r['run_id'].replace('run_', '').upper(),f"{r['tp']} / {r['fp']} / {r['fn']}",pct(r['precision']),pct(r['recall'])] for r in runs]},
            {'type':'section','text':'Consistency and correctness are separate'},
            {'type':'p','text':f"All {c['positive_issues_supported_in_every_run']} of {c['positive_reference_issues']} positive reference issues had supported matches in every batch. Detection decisions agreed across {c['document_rule_opportunities']} document-rule opportunities: {c['positive_reference_issues']} positives and {c['negative_opportunities']} negatives. No unstable positive detection was observed. These are issue instances; the policy has {summary['rule_types']} rule types."},
            {'type':'section','text':'What the scorer verified'},
            {'type':'p','text':'A true positive requires the expected document-rule pair and an exact quotation in its stated Section. All 48 finding occurrences passed source and locator checks. No severity, route or source-status differences were observed, and every result retained the required human-review flag. Zero denominators return undefined, rather than a perfect score.'},
            {'type':'section','text':'Execution boundary'},
            {'type':'p','text':'The runtime did not expose a model ID, snapshot or sampling settings. These are three isolated Codex agent batches, not 45 separately logged API requests or a fixed-version provider benchmark. The original held-out partition was reused; it is not a new unseen validation set. No population-accuracy estimate or confidence interval is inferred.'},
            {'type':'note','text':'Decision: retain the result as a reproducible local demonstration. Before a production pilot, pre-register a fixed provider/model configuration, fresh representative agreements, error thresholds and reviewer decisions. Preserved responses, input hashes, per-run metrics and issue-level consistency are included beside this brief.'}
        ]
    }

def main():
    summary=json.loads((LAB/'repeatability/results_summary.json').read_text())
    page=make_page(summary)
    data={'title':'Repeated NDA Review | Observed Results','author':'Ingrid Kao','edition':'11 November 2026','subject':'Three isolated agent batches; fixed synthetic sources and descriptive scoring','pages':[page]}
    register_fonts()
    pdf=MethodPDF(LAB/'repeatability/Repeatability_Results.pdf',data)
    pdf.start(page)
    for block in page['blocks']: pdf.block(block)
    pdf.end();pdf.save()
    (LAB/'repeatability/Repeatability_Results.md').write_text(markdown(data)+'\n')
    method_path=LAB/'method_content.json'
    method=json.loads(method_path.read_text())
    method['pages']=[p for p in method['pages'] if p.get('kicker')!=page['kicker']]+[page]
    method_path.write_text(json.dumps(method,ensure_ascii=False,indent=2)+'\n')
    print('Built one-page observed-results brief and synchronized method addendum.')

if __name__=='__main__': main()
