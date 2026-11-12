#!/usr/bin/env python3
"""Inspect versioned fictional review instructions over authored annotations."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parent
RULES = ('TERM', 'PURPOSE', 'RESIDUALS')
OUTCOMES = ('POLICY_MATCH', 'ESCALATE', 'NEEDS_REVIEW', 'OUT_OF_SCOPE')
OUTPUTS = ('case_evaluations.csv', 'rule_evaluations.csv', 'change_impact.csv',
           'review_freshness.csv', 'metrics.json', 'report.md', 'input_manifest.json')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(clauses):
    payload = json.dumps(clauses, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def fact(case, source, field, expected_type, allowed=None):
    """Validate annotation provenance and shape, not its substantive meaning."""
    if case['source_version'] != source['source_version']:
        return None, 'case_source_version_mismatch'
    item = case.get('facts', {}).get(field)
    if not isinstance(item, dict):
        return None, field + ':missing_fact'
    required = {'value', 'source_version', 'clause_id', 'quote'}
    if not required <= item.keys() or not item.keys() <= required | {'conflicting'}:
        return None, field + ':invalid_annotation_fields'
    if item['source_version'] != source['source_version']:
        return None, field + ':stale_source_version'
    locator, quote = item['clause_id'], item['quote']
    if not isinstance(locator, str) or locator not in source['clauses']:
        return None, field + ':unknown_clause_locator'
    if not isinstance(quote, str) or not quote:
        return None, field + ':missing_quote'
    if quote not in source['clauses'][locator]:
        return None, field + ':quote_absent_from_cited_clause'
    if 'conflicting' in item and type(item['conflicting']) is not bool:
        return None, field + ':invalid_conflict_flag'
    if item.get('conflicting'):
        return None, field + ':conflicting_annotation'
    value = item['value']
    if value is None:
        return None, field + ':unknown_value'
    # type(True) is bool rather than int, so booleans cannot become durations.
    if type(value) is not expected_type:
        return None, field + ':invalid_value_type'
    if allowed is not None and value not in allowed:
        return None, field + ':unsupported_value'
    if expected_type is int and not 0 < value <= 1200:
        return None, field + ':invalid_duration_range'
    return value, None


def result(status, reason):
    return {'status': status, 'reason': reason}


def evaluate(case, source, policy):
    if digest(source['clauses']) != source['source_sha256']:
        raise ValueError('Source digest mismatch: ' + source['document_id'])
    scope, error = fact(case, source, 'agreement_type', str, {'NDA', 'SOW'})
    if error:
        outcomes = {r: result('NEEDS_REVIEW', error) for r in RULES}
    elif scope != policy['scope']:
        outcomes = {r: result('OUT_OF_SCOPE', 'agreement_type=' + scope) for r in RULES}
    else:
        outcomes = {}
        months, month_error = fact(case, source, 'duration_months', int)
        start, start_error = fact(case, source, 'term_start', str,
                                  {'each_disclosure', 'effective_date'})
        term_errors = [x for x in (month_error, start_error) if x]
        if not term_errors and start != policy['duration']['required_start']:
            term_errors.append('term_start:requires_interpretation_or_normalization')
        minimum = policy['duration']['minimum_months']
        exceptions = policy['duration']['class_minimum_months']
        if not term_errors and exceptions:
            info, info_error = fact(case, source, 'information_class', str,
                                    {'ordinary', 'source_code', 'mixed'})
            if info_error:
                term_errors.append(info_error)
            elif info == 'mixed':
                assert policy['duration']['mixed_class_outcome'] == 'NEEDS_REVIEW'
                term_errors.append('information_class:mixed_scope_mapping_not_approved')
            else:
                minimum = exceptions.get(info, minimum)
        if term_errors:
            outcomes['TERM'] = result('NEEDS_REVIEW', ';'.join(term_errors))
        else:
            outcomes['TERM'] = result('ESCALATE' if months < minimum else 'POLICY_MATCH',
                                      f'minimum_months={minimum};annotated_months={months};start={start}')
        purpose, error = fact(case, source, 'purpose', str, {'project_atlas', 'any_business'})
        if error:
            outcomes['PURPOSE'] = result('NEEDS_REVIEW', error)
        else:
            outcomes['PURPOSE'] = result('POLICY_MATCH' if purpose == policy['permitted_purpose'] else 'ESCALATE',
                                         'annotated_purpose=' + purpose)
        residuals, error = fact(case, source, 'unrestricted_residuals', bool)
        if error:
            outcomes['RESIDUALS'] = result('NEEDS_REVIEW', error)
        else:
            violates = residuals and not policy['allow_unrestricted_residuals']
            outcomes['RESIDUALS'] = result('ESCALATE' if violates else 'POLICY_MATCH',
                                           'unrestricted_residuals=' + str(residuals).lower())
    statuses = {x['status'] for x in outcomes.values()}
    aggregate = next(x for x in ('ESCALATE', 'NEEDS_REVIEW', 'OUT_OF_SCOPE', 'POLICY_MATCH')
                     if x in statuses)
    return {'aggregate': aggregate, 'rules': outcomes}


def review_freshness(prior, current):
    """A comparison instruction; it never revokes or changes a prior decision."""
    reasons = []
    for field in ('policy_version', 'source_version', 'source_sha256'):
        if prior[field] != current[field]:
            reasons.append(field + '_changed')
    return {'status': 'RECHECK_REQUIRED' if reasons else 'CURRENT',
            'reason': ';'.join(reasons) if reasons else 'same_policy_and_pinned_source'}


def write_csv(path, fields, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)


def run(out_dir):
    policies = [read_json(ROOT / 'policies' / x) for x in ('v1.json', 'v2.json')]
    for policy in policies:
        assert policy['scope'] == 'NDA'
        assert policy['duration']['required_start'] == 'each_disclosure'
        assert type(policy['duration']['minimum_months']) is int
        assert policy['duration']['minimum_months'] > 0
        assert policy['duration']['mixed_class_outcome'] in (None, 'NEEDS_REVIEW')
        if policy['duration']['class_minimum_months']:
            assert policy['duration']['mixed_class_outcome'] == 'NEEDS_REVIEW'
        assert type(policy['allow_unrestricted_residuals']) is bool
        assert policy['permitted_purpose'] == 'project_atlas'
        for cls, months in policy['duration']['class_minimum_months'].items():
            assert cls in {'ordinary', 'source_code'}
            assert type(months) is int and months > 0
    assert len({p['version'] for p in policies}) == len(policies)
    documents = read_json(ROOT / 'fixtures' / 'source_documents.json')
    cases = read_json(ROOT / 'fixtures' / 'annotated_scenarios.json')
    freshness_cases = read_json(ROOT / 'fixtures' / 'review_freshness.json')
    source_index = {x['document_id']: x for x in documents}
    if len(source_index) != len(documents):
        raise ValueError('Duplicate document IDs')
    out_dir.mkdir(parents=True, exist_ok=True)
    case_rows, rule_rows, impacts = [], [], []
    counters = {p['version']: Counter() for p in policies}
    for case in cases:
        source = source_index[case['document_id']]
        evaluated = []
        for policy in policies:
            actual = evaluate(case, source, policy)
            expected = case['expected'][policy['version']]
            assert actual['aggregate'] == expected['aggregate'], (case['case_id'], policy['version'], actual)
            assert {k: v['status'] for k, v in actual['rules'].items()} == expected['rules'], (case['case_id'], policy['version'], actual)
            counters[policy['version']][actual['aggregate']] += 1
            row = {'case_id': case['case_id'], 'scenario': case['scenario'],
                   'policy_version': policy['version'], 'source_version': source['source_version'],
                   'aggregate': actual['aggregate'], 'matches_authored_expectation': True}
            row.update({r.lower(): actual['rules'][r]['status'] for r in RULES})
            case_rows.append(row)
            for rule, value in actual['rules'].items():
                rule_rows.append({'case_id': case['case_id'], 'policy_version': policy['version'],
                                  'rule_id': rule, **value})
            evaluated.append(actual)
        before, after = evaluated
        changed_status = [r for r in RULES if before['rules'][r]['status'] != after['rules'][r]['status']]
        changed_reason = [r for r in RULES if before['rules'][r]['reason'] != after['rules'][r]['reason']]
        impacts.append({'case_id': case['case_id'], 'scenario': case['scenario'],
                        'from_policy': policies[0]['version'], 'to_policy': policies[1]['version'],
                        'prior_aggregate': before['aggregate'], 'revised_aggregate': after['aggregate'],
                        'aggregate_changed': before['aggregate'] != after['aggregate'],
                        'rules_with_changed_status': ';'.join(changed_status),
                        'rules_with_changed_reason': ';'.join(changed_reason),
                        'review_instruction': 'COMPARE_FOR_NEW_REVIEW_CONTEXT',
                        'prior_decision_action': 'UNCHANGED_NO_AUTOMATIC_REVOCATION'})
    freshness_rows = []
    for case in freshness_cases:
        actual = review_freshness(case['prior'], case['current'])
        assert actual == case['expected'], (case['scenario_id'], actual)
        freshness_rows.append({'scenario_id': case['scenario_id'], 'scenario': case['scenario'], **actual,
                               'prior_decision_action': 'UNCHANGED_NO_AUTOMATIC_REVOCATION'})
    metrics = {
        'study_date': '2026-11-11', 'data_status': 'authored_synthetic_sources_and_annotations',
        'model_calls': 0, 'automated_legal_extraction': False,
        'scenarios': len(cases), 'policy_versions': len(policies), 'policy_evaluations': len(case_rows),
        'policy_evaluations_matching_authored_expectations': len(case_rows),
        'per_rule_evaluations': len(rule_rows),
        'aggregate_counts_by_policy': {k: dict(sorted(v.items())) for k, v in counters.items()},
        'scenarios_with_changed_aggregate': sum(x['aggregate_changed'] for x in impacts),
        'scenarios_with_changed_rule_status': sum(bool(x['rules_with_changed_status']) for x in impacts),
        'scenarios_with_changed_rule_reason': sum(bool(x['rules_with_changed_reason']) for x in impacts),
        'freshness_scenarios': len(freshness_rows),
        'freshness_checks_matching_authored_expectations': len(freshness_rows),
        'freshness_status_counts': dict(sorted(Counter(x['status'] for x in freshness_rows).items())),
        'legal_accuracy': None, 'human_review_minutes': None, 'production_roi': None,
    }
    write_csv(out_dir / 'case_evaluations.csv', list(case_rows[0]), case_rows)
    write_csv(out_dir / 'rule_evaluations.csv', list(rule_rows[0]), rule_rows)
    write_csv(out_dir / 'change_impact.csv', list(impacts[0]), impacts)
    write_csv(out_dir / 'review_freshness.csv', list(freshness_rows[0]), freshness_rows)
    (out_dir / 'metrics.json').write_text(json.dumps(metrics, indent=2, sort_keys=True) + '\n')
    inputs = [ROOT / 'run.py'] + sorted((ROOT / 'policies').glob('*.json')) + sorted((ROOT / 'fixtures').glob('*.json'))
    manifest = {x.relative_to(ROOT).as_posix(): hashlib.sha256(x.read_bytes()).hexdigest() for x in inputs}
    (out_dir / 'input_manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    report = f'''# Versioned rulebook demonstration results

The run matched authored expectations on {len(case_rows)} policy evaluations across {len(cases)} synthetic scenarios and two policy versions. It produced {len(rule_rows)} per-rule results. These are checks of software behavior against authored fixtures, not legal or model accuracy.

| Aggregate result | Policy 1.0 | Policy 2.0 |
| --- | --- | --- |
'''
    for status in OUTCOMES:
        report += f"| {status} | {counters['1.0'][status]} | {counters['2.0'][status]} |\n"
    report += f'''
{metrics['scenarios_with_changed_aggregate']} scenarios changed aggregate outcomes. {metrics['scenarios_with_changed_rule_reason']} scenarios had a changed rule reason, including threshold changes where the outcome remained the same. The change report identifies comparisons for a new review context. It does not apply a policy retroactively or revoke a prior decision.

All {len(freshness_rows)} review-freshness scenarios matched authored expectations: one CURRENT and three RECHECK_REQUIRED. A changed version identifies a comparison task, without changing any earlier decision.

The engine evaluates supplied annotations and exact source-linkage fields. It does not extract contractual meaning, verify annotation correctness, authenticate counsel, approve agreements, or resolve substantive uncertainty. The policy's 36- and 60-month thresholds are fictional sponsor instructions. Missing, stale, conflicting or incorrectly typed material facts produce NEEDS_REVIEW for the affected rule. A confirmed policy departure remains ESCALATE even if another rule needs review.

No network request or model inference occurred. Legal accuracy, reviewer effort and ROI are unmeasured.
'''
    (out_dir / 'report.md').write_text(report, encoding='utf-8')
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'outputs')
    parser.add_argument('--regression', action='store_true')
    args = parser.parse_args()
    if args.regression:
        with tempfile.TemporaryDirectory(prefix='rulebook-check-') as td:
            one, two = Path(td) / 'one', Path(td) / 'two'
            metrics = run(one); run(two)
            for name in OUTPUTS:
                assert (one / name).read_bytes() == (two / name).read_bytes(), name
            print(json.dumps({'regression': 'passed', 'artifacts_compared': len(OUTPUTS), 'metrics': metrics}, sort_keys=True))
    else:
        print(json.dumps(run(args.output_dir), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
