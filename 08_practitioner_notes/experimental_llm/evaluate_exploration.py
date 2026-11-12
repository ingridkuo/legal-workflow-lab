"""Score the saved synthetic response under explicit reference and grouping units.

Running this file never calls a model. The original response and provisional key
are preserved; the revised key makes the two overlap decisions inspectable.
"""
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parent
RULES = {'TERM', 'PURPOSE', 'RESIDUALS', 'DELETION'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_frozen_inputs(root, decision_record):
    for name, digest in decision_record['preserved_inputs_sha256'].items():
        require(hashlib.sha256((Path(root) / name).read_bytes()).hexdigest() == digest,
                'Frozen input changed: ' + name)


def validate_key(documents, provisional, adjudicated):
    source = {d['document_id']: d for d in documents}
    document_ids = set(source)
    require(len(document_ids) == len(documents), 'Duplicate source document')
    expected = adjudicated['expected_rule_ids']
    require(set(provisional['expected_rule_ids']) == document_ids,
            'Provisional key document coverage differs from sources')
    require(set(expected) == document_ids, 'Adjudicated key document coverage differs from sources')
    require(set(adjudicated['expected_clause_ids']) == document_ids,
            'Reference locator coverage differs from sources')
    pairs = set()
    for d, rules in expected.items():
        require(isinstance(rules, list) and len(rules) == len(set(rules)),
                'Duplicate or invalid reference labels')
        require(set(rules) <= RULES, 'Unknown reference rule')
        require(set(adjudicated['expected_clause_ids'][d]) == set(rules),
                'Reference locators do not cover expected labels')
        require(all(locator in source[d]['clauses'] for locator in adjudicated['expected_clause_ids'][d].values()),
                'Reference locator does not exist in source')
        pairs.update((d, rule) for rule in rules)
    grouped = set()
    group_ids = set()
    for group in adjudicated['issue_groups']:
        require(group['issue_id'] not in group_ids, 'Duplicate issue-group ID')
        group_ids.add(group['issue_id'])
        require(group['primary_rule_id'] in group['rule_ids'], 'Primary rule absent from group')
        require(len(group['rule_ids']) == len(set(group['rule_ids'])), 'Duplicate grouped rule')
        if {'PURPOSE', 'RESIDUALS'} <= set(group['rule_ids']):
            require(group['primary_rule_id'] == 'RESIDUALS',
                    'Residual-use overlap must retain the specific RESIDUALS primary rule')
        for rule in group['rule_ids']:
            pair = (group['document_id'], rule)
            require(pair in pairs and pair not in grouped,
                    'Unknown or multiply grouped reference pair')
            require(adjudicated['expected_clause_ids'][group['document_id']][rule] == group['clause_id'],
                    'Group locator differs from its reference pair')
            grouped.add(pair)
    require(grouped == pairs, 'Issue groups do not cover every reference pair')
    return pairs



def validate_author_adjudication(documents, provisional, adjudicated, author_record):
    """Check supplied adjudication provenance and its source evidence, not identity."""
    require(author_record.get('adjudicator') == 'Ingrid Kao (author)',
            'Unexpected author-adjudication attribution')
    require(author_record.get('independent') is False,
            'Author adjudication must remain explicitly non-independent')
    require(author_record.get('date') == '2026-11-11',
            'Unexpected author-adjudication date')
    source = {d['document_id']: d for d in documents}
    original = {(d, rule) for d, rules in provisional['expected_rule_ids'].items() for rule in rules}
    revised = {(d, rule) for d, rules in adjudicated['expected_rule_ids'].items() for rule in rules}
    expected_additions = revised - original
    recorded = set()
    for decision in author_record.get('decisions', []):
        pair = (decision.get('document_id'), decision.get('rule_id'))
        require(pair in expected_additions and pair not in recorded,
                'Author adjudication has an unknown or duplicate addition')
        recorded.add(pair)
        doc_id, rule_id = pair
        locator = decision.get('clause_id')
        require(locator == adjudicated['expected_clause_ids'][doc_id][rule_id],
                'Author-adjudication locator differs from revised key')
        quote = decision.get('quote')
        require(isinstance(quote, str) and bool(quote)
                and quote in source[doc_id]['clauses'][locator],
                'Author-adjudication quote does not match its source clause')
        require(bool(decision.get('reason')), 'Author-adjudication reason is missing')
    require(recorded == expected_additions,
            'Author adjudication must cover every added reference pair')


def score_reviews(documents, provisional, adjudicated, response, author_record=None):
    expected = validate_key(documents, provisional, adjudicated)
    if author_record is not None:
        validate_author_adjudication(documents, provisional, adjudicated, author_record)
    source = {d['document_id']: d for d in documents}
    require(isinstance(response, dict) and set(response) == {'reviews'}, 'Invalid response envelope')
    require(isinstance(response['reviews'], list) and len(response['reviews']) == len(source),
            'Response must contain one review for every source document')
    seen, actual, supported = set(), set(), set()
    rows, source_checks = [], []
    group_by_pair = {(g['document_id'], rule): g
                     for g in adjudicated['issue_groups'] for rule in g['rule_ids']}
    for review in response['reviews']:
        require(isinstance(review, dict) and set(review) == {
            'document_id', 'source_version', 'source_sha256', 'findings'}, 'Invalid review fields')
        require(all(isinstance(review[field], str) for field in ['document_id', 'source_version', 'source_sha256']),
                'Document identity fields must be strings')
        doc_id = review['document_id']
        require(doc_id in source and doc_id not in seen, 'Unknown or duplicate reviewed document')
        seen.add(doc_id)
        doc = source[doc_id]
        digest = hashlib.sha256(json.dumps(doc['clauses'], sort_keys=True,
            separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        require(digest == doc['source_sha256'], 'Source digest does not match canonical clause JSON')
        metadata_ok = (review['source_version'] == doc['source_version']
                       and review['source_sha256'] == digest)
        source_checks.append(metadata_ok)
        require(isinstance(review['findings'], list), 'Findings must be an array')
        for finding in review['findings']:
            require(isinstance(finding, dict) and set(finding) == {
                'rule_id', 'clause_id', 'quote', 'reason', 'proposed_action'}, 'Invalid finding fields')
            require(all(isinstance(v, str) for v in finding.values()), 'Finding fields must be strings')
            rule = finding['rule_id']
            require(rule in RULES, 'Unknown finding rule')
            require(finding['proposed_action'] == 'ESCALATE_TO_COUNSEL', 'Unknown proposed action')
            require(bool(finding['quote']) and bool(finding['reason']), 'Empty finding evidence or reason')
            pair = (doc_id, rule)
            require(pair not in actual, 'Duplicate document-and-rule finding')
            actual.add(pair)
            exact = (finding['clause_id'] in doc['clauses']
                     and finding['quote'] in doc['clauses'][finding['clause_id']])
            expected_locator = adjudicated['expected_clause_ids'][doc_id].get(rule)
            locator_matches = expected_locator is not None and finding['clause_id'] == expected_locator
            usable = metadata_ok and exact and locator_matches
            if pair in expected and usable:
                supported.add(pair)
            group = group_by_pair.get(pair)
            rows.append({
                'document_id': doc_id, 'rule_id': rule, 'clause_id': finding['clause_id'],
                'source_metadata_matches': metadata_ok, 'quote_matches_cited_clause': exact,
                'reference_locator_matches': locator_matches,
                'provisional_key_status': ('listed' if rule in provisional['expected_rule_ids'][doc_id]
                    else 'additional_label_accepted_by_adjudication' if pair in expected else 'not_listed'),
                'adjudicated_key_status': ('supported_match' if pair in supported
                    else 'unsupported_reference_match' if pair in expected else 'unexpected_finding'),
                'issue_group_id': group['issue_id'] if group else '',
                'primary_rule_id': group['primary_rule_id'] if group else '',
                'quote': finding['quote'], 'reason': finding['reason']})
    require(seen == set(source), 'Missing reviewed documents')
    original = {(d, rule) for d, rules in provisional['expected_rule_ids'].items() for rule in rules}
    tp, fp, fn = len(supported), len(actual) - len(supported), len(expected - supported)
    groups = []
    for group in adjudicated['issue_groups']:
        doc_id = group['document_id']
        retained = [rule for rule in group['rule_ids'] if (doc_id, rule) in supported]
        groups.append({
            'issue_group_id': group['issue_id'], 'document_id': doc_id,
            'clause_id': group['clause_id'], 'primary_rule_id': group['primary_rule_id'],
            'expected_rule_ids': group['rule_ids'], 'supported_rule_ids': retained,
            'group_supported': bool(retained),
            'all_rule_labels_supported': set(retained) == set(group['rule_ids'])})
    metrics = {
        'review_documents': len(seen), 'finding_rows': len(rows),
        'source_metadata_checks': len(source_checks), 'source_metadata_matches': sum(source_checks),
        'quote_checks': len(rows), 'quotes_matching_cited_clause': sum(row['quote_matches_cited_clause'] for row in rows),
        'provisional_key_pairs': len(original), 'provisional_key_pairs_present': len(original & actual),
        'provisional_key_pairs_missing': len(original - actual),
        'additional_label_pairs': [{'document_id': d, 'rule_id': rule} for d, rule in sorted(actual - original)],
        'adjudicated_key_version': adjudicated['key_version'],
        'reference_key_timing': 'post-run adjudication of saved outputs',
        'adjudicated_scoring_unit': 'document_id + rule_id',
        'adjudicated_key_pairs': len(expected),
        'adjudicated_key_pairs_present': len(expected & actual),
        'adjudicated_key_pairs_supported': tp,
        'adjudicated_key_pairs_missing': len(expected - actual),
        'response_pairs_outside_adjudicated_key': [{'document_id': d, 'rule_id': rule}
            for d, rule in sorted(actual - expected)],
        'distinct_flagged_clauses': len({(row['document_id'], row['clause_id']) for row in rows}),
        'supported_true_positives': tp,
        'false_positives': fp, 'false_negatives': fn,
        'adjudicated_precision': None,
        'adjudicated_recall': None,
        'rate_reporting': 'Not reported: the reference key was adjudicated after inspecting this saved response.',
        'adjudication': ({'adjudicator': author_record['adjudicator'],
            'date': author_record['date'], 'independent': False,
            'record': 'adjudication_record.json',
            'provenance': 'Author-supplied record; identity is not authenticated by this scorer.'}
            if author_record is not None else None),
        'actionable_issue_groups': len(groups),
        'supported_actionable_issue_groups': sum(g['group_supported'] for g in groups),
        'issue_groups_with_all_labels_supported': sum(g['all_rule_labels_supported'] for g in groups),
        'unresolved_label_adjudications': len(actual - expected),
        'human_review_time_minutes': None, 'model_accuracy': None,
        'note': ('One saved Codex delegated-agent batch on eight synthetic fragments. '
                 'The adopted document-and-rule convention retains both PURPOSE labels; '
                 'the actionable-issue convention groups each with RESIDUALS under the specific rule. '
                 'This post-run reference revision changes the counting convention, not the saved model behavior. '
                 'The supplied author adjudication was made after inspecting the response and is not independent. '
                 'Agreement counts describe this batch only; precision, recall and population legal accuracy are not reported. '
                 'The original provisional key and raw response remain unchanged. '
                 'Re-running this scorer does not rerun inference.')}
    return metrics, rows, groups


def main():
    read = lambda name: json.loads((ROOT / name).read_text())
    decision = read('adjudication_v1_1.json')
    check_frozen_inputs(ROOT, decision)
    metrics, rows, groups = score_reviews(read('documents.json'), read('provisional_answer_key.json'),
        read('adjudicated_answer_key.json'), read('raw_model_response.json'), read('adjudication_record.json'))
    (ROOT / 'exploration_metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    (ROOT / 'actionable_issue_groups.json').write_text(json.dumps(groups, indent=2) + '\n')
    with (ROOT / 'finding_evidence.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
