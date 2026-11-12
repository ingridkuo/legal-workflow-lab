#!/usr/bin/env python3
"""Reconstruct original fictional inputs and independently enumerated expectations."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def expected(codes):
    names = {'M': 'POLICY_MATCH', 'E': 'ESCALATE', 'N': 'NEEDS_REVIEW', 'O': 'OUT_OF_SCOPE'}
    # Each tuple independently enumerates TERM, PURPOSE, RESIDUALS, aggregate.
    return {'aggregate': names[codes[3]],
            'rules': {r: names[c] for r, c in zip(('TERM', 'PURPOSE', 'RESIDUALS'), codes[:3])}}


def main():
    for version, class_minimum, effective in [('1.0', {}, '2026-11-10'),
                                               ('2.0', {'source_code': 60}, '2026-11-11')]:
        policy = {
            'version': version, 'policy_status': 'fictional_sponsor_instruction',
            'effective_date': effective, 'policy_owner_role': 'designated_counsel',
            'approval_reference': 'FICTIONAL-POLICY-' + version,
            'scope': 'NDA',
            'duration': {'minimum_months': 36, 'required_start': 'each_disclosure',
                         'class_minimum_months': class_minimum,
                         'mixed_class_outcome': 'NEEDS_REVIEW' if class_minimum else None},
            'permitted_purpose': 'project_atlas', 'allow_unrestricted_residuals': False,
            'scope_note': 'Illustrative instructions, not law or market-standard terms. Mixed information classes require an approved mapping under version 2.0.',
        }
        write(ROOT / 'policies' / ('v' + version[0] + '.json'), policy)

    # The expected outcomes are authored test values, not computed by the engine.
    specs = [
        ('S01', 'Ordinary information at 35 months', 35, 'ordinary', 'each_disclosure', 'project_atlas', False, None, 'EMME', 'EMME'),
        ('S02', 'Ordinary information at 36 months', 36, 'ordinary', 'each_disclosure', 'project_atlas', False, None, 'MMMM', 'MMMM'),
        ('S03', 'Ordinary information at 60 months', 60, 'ordinary', 'each_disclosure', 'project_atlas', False, None, 'MMMM', 'MMMM'),
        ('S04', 'Source code at 35 months', 35, 'source_code', 'each_disclosure', 'project_atlas', False, None, 'EMME', 'EMME'),
        ('S05', 'Source code at 36 months', 36, 'source_code', 'each_disclosure', 'project_atlas', False, None, 'MMMM', 'EMME'),
        ('S06', 'Source code at 59 months', 59, 'source_code', 'each_disclosure', 'project_atlas', False, None, 'MMMM', 'EMME'),
        ('S07', 'Source code at 60 months', 60, 'source_code', 'each_disclosure', 'project_atlas', False, None, 'MMMM', 'MMMM'),
        ('S08', 'Mixed information without approved mapping', 36, 'mixed', 'each_disclosure', 'project_atlas', False, None, 'MMMM', 'NMMN'),
        ('S09', 'Unknown information class', 36, None, 'each_disclosure', 'project_atlas', False, None, 'MMMM', 'NMMN'),
        ('S10', 'Different term start requires interpretation', 36, 'ordinary', 'effective_date', 'project_atlas', False, None, 'NMMN', 'NMMN'),
        ('S11', 'Conflicting durations', 36, 'ordinary', 'each_disclosure', 'project_atlas', False, 'conflicting_duration', 'NMMN', 'NMMN'),
        ('S12', 'Missing duration quotation', 36, 'ordinary', 'each_disclosure', 'project_atlas', False, 'missing_quote', 'NMMN', 'NMMN'),
        ('S13', 'Incorrect duration clause locator', 36, 'ordinary', 'each_disclosure', 'project_atlas', False, 'bad_locator', 'NMMN', 'NMMN'),
        ('S14', 'Stale duration source version', 36, 'ordinary', 'each_disclosure', 'project_atlas', False, 'stale_fact', 'NMMN', 'NMMN'),
        ('S15', 'Statement of work outside NDA scope', 36, 'ordinary', 'each_disclosure', 'project_atlas', False, 'non_nda', 'OOOO', 'OOOO'),
        ('S16', 'Broad purpose remains an exception despite uncertain term start', 36, 'ordinary', None, 'any_business', False, None, 'NEME', 'NEME'),
        ('S17', 'Unrestricted residuals', 36, 'ordinary', 'each_disclosure', 'project_atlas', True, None, 'MMEE', 'MMEE'),
        ('S18', 'String duration and unresolved purpose', 36, 'ordinary', 'each_disclosure', None, False, 'invalid_duration_type', 'NNMN', 'NNMN'),
    ]
    docs, cases = [], []
    for num, spec in enumerate(specs, 1):
        cid, label, months, info, start, purpose, residuals, mutation, one, two = spec
        if start == 'each_disclosure':
            term = f'Confidentiality lasts {months} months after each disclosure.'
        elif start == 'effective_date':
            term = f'Confidentiality lasts {months} months after the effective date.'
        else:
            term = f'Confidentiality lasts {months} months from a starting event to be agreed.'
        if mutation == 'conflicting_duration':
            term = 'Confidentiality lasts 36 months after each disclosure. A separate sentence states a 12-month period for the same information.'
        info_text = {'ordinary': 'The disclosed information consists of ordinary commercial information.',
                     'source_code': 'The disclosed information consists of source code.',
                     'mixed': 'The disclosure combines ordinary commercial information and source code.',
                     None: 'The class of the disclosed information is not identified.'}[info]
        purpose_text = {'project_atlas': 'The recipient may use the information only to evaluate Project Atlas.',
                        'any_business': 'The recipient may use the information for any business purpose.',
                        None: 'The permitted use will be agreed later.'}[purpose]
        residuals_text = ('Information retained in unaided memory may be used without restriction.' if residuals else
                          'No unrestricted use of information retained in unaided memory is permitted.')
        scope_text = 'This is a statement of work for technical services.' if mutation == 'non_nda' else 'This is a nondisclosure agreement.'
        clauses = {'C0': scope_text, 'C1': term, 'C2': info_text, 'C3': purpose_text, 'C4': residuals_text}
        payload = json.dumps(clauses, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        doc = {'document_id': f'D{num:02}', 'source_version': '1', 'clauses': clauses,
               'source_sha256': hashlib.sha256(payload.encode()).hexdigest()}
        docs.append(doc)

        def ann(value, locator):
            return {'value': value, 'source_version': '1', 'clause_id': locator, 'quote': clauses[locator]}

        facts = {'agreement_type': ann('SOW' if mutation == 'non_nda' else 'NDA', 'C0'),
                 'duration_months': ann(months, 'C1'), 'term_start': ann(start, 'C1'),
                 'information_class': ann(info, 'C2'), 'purpose': ann(purpose, 'C3'),
                 'unrestricted_residuals': ann(residuals, 'C4')}
        if mutation == 'conflicting_duration':
            facts['duration_months']['value'] = None
            facts['duration_months']['conflicting'] = True
        elif mutation == 'missing_quote':
            facts['duration_months']['quote'] = ''
        elif mutation == 'bad_locator':
            facts['duration_months']['clause_id'] = 'C99'
        elif mutation == 'stale_fact':
            facts['duration_months']['source_version'] = '0'
        elif mutation == 'invalid_duration_type':
            facts['duration_months']['value'] = '36'
        cases.append({'case_id': cid, 'scenario': label, 'document_id': doc['document_id'],
                      'source_version': '1', 'annotation_status': 'deliberately_authored_test_input',
                      'facts': facts, 'expected': {'1.0': expected(one), '2.0': expected(two)}})
    write(ROOT / 'fixtures' / 'source_documents.json', docs)
    write(ROOT / 'fixtures' / 'annotated_scenarios.json', cases)
    current = {'policy_version': '2.0', 'source_version': '1', 'source_sha256': docs[0]['source_sha256']}
    old_source = {'source_version': '0', 'source_sha256': '0' * 64}
    freshness = [
        {'scenario_id': 'F01', 'scenario': 'Same policy and source', 'prior': dict(current), 'current': dict(current),
         'expected': {'status': 'CURRENT', 'reason': 'same_policy_and_pinned_source'}},
        {'scenario_id': 'F02', 'scenario': 'Policy version changed', 'prior': {**current, 'policy_version': '1.0'}, 'current': dict(current),
         'expected': {'status': 'RECHECK_REQUIRED', 'reason': 'policy_version_changed'}},
        {'scenario_id': 'F03', 'scenario': 'Source version and digest changed', 'prior': {**current, **old_source}, 'current': dict(current),
         'expected': {'status': 'RECHECK_REQUIRED', 'reason': 'source_version_changed;source_sha256_changed'}},
        {'scenario_id': 'F04', 'scenario': 'Both policy and source changed', 'prior': {**current, **old_source, 'policy_version': '1.0'}, 'current': dict(current),
         'expected': {'status': 'RECHECK_REQUIRED', 'reason': 'policy_version_changed;source_version_changed;source_sha256_changed'}},
    ]
    write(ROOT / 'fixtures' / 'review_freshness.json', freshness)


if __name__ == '__main__':
    main()
