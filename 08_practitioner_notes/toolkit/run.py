#!/usr/bin/env python3
"""Reproduce fictional output gates and legal-program control scenarios.

No network requests, model calls, external actions, or production identity system.
"""
import argparse
import csv
import hashlib
import json
import sqlite3
import sys
import tempfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED_OUTPUT_FIELDS = {'document_id', 'source_version', 'source_sha256', 'rule_id', 'severity', 'clause_id', 'quote', 'proposed_action'}


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def stable_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def hash_value(value):
    return hashlib.sha256(stable_json(value).encode('utf-8')).hexdigest()


def parse_time(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def format_time(value):
    return value.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def validate_output(raw, documents, config):
    """Check shape and source linkage; deliberately do not decide legal meaning."""
    try:
        output = json.loads(raw)
    except (ValueError, TypeError):
        return {'gate': 'BLOCKED', 'code': 'INVALID_JSON'}
    if isinstance(output, dict) and set(output) == {'refusal'} and isinstance(output['refusal'], str) and output['refusal'].strip():
        return {'gate': 'MANUAL_REVIEW', 'code': 'MODEL_REFUSAL'}
    if not isinstance(output, dict) or set(output) != REQUIRED_OUTPUT_FIELDS:
        return {'gate': 'BLOCKED', 'code': 'SCHEMA_FIELDS'}
    if any(not isinstance(value, str) for value in output.values()):
        return {'gate': 'BLOCKED', 'code': 'SCHEMA_TYPES'}
    if output['rule_id'] not in config['review_rules']:
        return {'gate': 'BLOCKED', 'code': 'UNKNOWN_RULE'}
    if output['severity'] not in config['severities']:
        return {'gate': 'BLOCKED', 'code': 'UNKNOWN_SEVERITY'}
    document = documents.get(output['document_id'])
    if document is None:
        return {'gate': 'BLOCKED', 'code': 'UNKNOWN_DOCUMENT'}
    # Recompute the pinned source hash; never rely only on a stored manifest value.
    source_hash = hashlib.sha256(document['text'].encode('utf-8')).hexdigest()
    if output['source_version'] != document['source_version']:
        return {'gate': 'BLOCKED', 'code': 'SOURCE_VERSION_MISMATCH'}
    if output['source_sha256'] != source_hash or document['sha256'] != source_hash:
        return {'gate': 'BLOCKED', 'code': 'SOURCE_HASH_MISMATCH'}
    quote = output['quote']
    if not quote.strip():
        return {'gate': 'BLOCKED', 'code': 'EMPTY_QUOTE'}
    if len(quote) > config['max_quote_characters']:
        return {'gate': 'BLOCKED', 'code': 'QUOTE_TOO_LONG'}
    clause = next((c for c in document['clauses'] if c['clause_id'] == output['clause_id']), None)
    if clause is None or quote not in clause['text']:
        return {'gate': 'BLOCKED', 'code': 'QUOTE_NOT_IN_CLAUSE'}
    if not output['proposed_action'].strip():
        return {'gate': 'BLOCKED', 'code': 'EMPTY_PROPOSED_ACTION'}
    return {'gate': 'READY_FOR_HUMAN_REVIEW', 'code': 'SOURCE_LINKAGE_CHECKS_PASSED'}


class ProgramError(Exception):
    pass


class ClosureBlocked(ProgramError):
    def __init__(self, reasons):
        self.reasons = reasons
        super().__init__(', '.join(reasons))


class Program:
    """A single-process demonstration of workflow controls, not an IAM system."""
    def __init__(self, path, config, mapping):
        self.config = config
        self.mapping = mapping
        self.clock = parse_time(config['as_of'])
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys = ON')
        self.db.executescript('''
        CREATE TABLE cases (
          case_id TEXT PRIMARY KEY,
          external_key TEXT NOT NULL UNIQUE,
          payload_hash TEXT NOT NULL,
          source_version TEXT NOT NULL,
          source_ref TEXT NOT NULL,
          summary TEXT NOT NULL,
          category TEXT NOT NULL,
          priority TEXT NOT NULL,
          coordinator TEXT NOT NULL,
          action_owner TEXT,
          handoff_accepted INTEGER NOT NULL DEFAULT 0,
          decision_needed INTEGER NOT NULL,
          decision_authority TEXT NOT NULL,
          decision_evidence_ref TEXT,
          approved_source_version TEXT,
          execution_receipt_ref TEXT,
          execution_source_version TEXT,
          state TEXT NOT NULL CHECK(state IN ('new','assigned','awaiting_counsel','ready_to_execute','pending_confirmation','blocked','closed')),
          created_at TEXT NOT NULL,
          due_at TEXT NOT NULL,
          last_action_at TEXT NOT NULL,
          next_review_at TEXT,
          preservation_status TEXT NOT NULL CHECK(preservation_status IN ('not_requested','pending','active','released')),
          preservation_owner TEXT,
          preservation_accepted INTEGER NOT NULL DEFAULT 0,
          preservation_next_review TEXT,
          preservation_decision_ref TEXT,
          evidence_visibility TEXT NOT NULL CHECK(evidence_visibility IN ('restricted','sanitized')),
          last_blockers TEXT NOT NULL DEFAULT '[]'
        );
        CREATE TABLE audit_events (
          event_id INTEGER PRIMARY KEY AUTOINCREMENT,
          case_id TEXT NOT NULL REFERENCES cases(case_id),
          event_at TEXT NOT NULL,
          actor_role TEXT NOT NULL,
          event_type TEXT NOT NULL,
          details_json TEXT NOT NULL
        );
        ''')
        self.db.commit()

    def row(self, case_id):
        row = self.db.execute('SELECT * FROM cases WHERE case_id = ?', (case_id,)).fetchone()
        if row is None:
            raise ProgramError('Unknown case')
        return dict(row)

    def audit(self, case_id, actor, event, details):
        self.db.execute('INSERT INTO audit_events(case_id,event_at,actor_role,event_type,details_json) VALUES(?,?,?,?,?)', (case_id, self.config['as_of'], actor, event, stable_json(details)))
        self.db.commit()

    def update(self, case_id, **values):
        values['last_action_at'] = self.config['as_of']
        fields = ', '.join(key + ' = ?' for key in values)
        self.db.execute('UPDATE cases SET ' + fields + ' WHERE case_id = ?', (*values.values(), case_id))
        self.db.commit()

    @staticmethod
    def require_role(actual, required):
        # This is a simulated role argument, not authentication or authorization.
        if not isinstance(actual, str) or not actual or not isinstance(required, str) or not required or actual != required:
            raise ProgramError('ROLE_NOT_PERMITTED')

    def intake(self, external, actor='program_coordinator'):
        self.require_role(actor, 'program_coordinator')
        if set(external) != set(self.mapping['required']):
            raise ProgramError('INTAKE_FIELDS')
        if any(not isinstance(v, str) or not v.strip() for v in external.values()):
            raise ProgramError('INTAKE_TYPES')
        canonical = {target: external[source] for source, target in self.mapping['external_to_canonical'].items()}
        if len(canonical['summary']) > 140:
            raise ProgramError('SUMMARY_TOO_LONG')
        if canonical['category'] not in self.config['routing'] or canonical['priority'] not in self.config['illustrative_case_review_hours']:
            raise ProgramError('UNKNOWN_ROUTING_VALUE')
        if canonical['evidence_visibility'] not in {'restricted', 'sanitized'}:
            raise ProgramError('UNKNOWN_VISIBILITY')
        created = parse_time(canonical['created_at'])
        payload_hash = hash_value(external)
        existing = self.db.execute('SELECT case_id,payload_hash FROM cases WHERE external_key = ?', (canonical['external_key'],)).fetchone()
        if existing:
            if existing['payload_hash'] != payload_hash:
                self.audit(existing['case_id'], actor, 'duplicate_conflict', {'external_key': canonical['external_key']})
                raise ProgramError('IDEMPOTENCY_CONFLICT')
            self.audit(existing['case_id'], actor, 'duplicate_reused', {'external_key': canonical['external_key']})
            return existing['case_id']
        policy = self.config['routing'][canonical['category']]
        case_id = 'CASE-' + canonical['external_key'].rsplit('-', 1)[-1]
        due = created + timedelta(hours=self.config['illustrative_case_review_hours'][canonical['priority']])
        values = dict(canonical, case_id=case_id, payload_hash=payload_hash, decision_needed=int(policy['decision_needed']), decision_authority=policy['decision_authority'], state='new', due_at=format_time(due), next_review_at=format_time(due), last_action_at=self.config['as_of'], preservation_status='not_requested')
        keys = list(values)
        self.db.execute('INSERT INTO cases(' + ','.join(keys) + ') VALUES(' + ','.join('?' for _ in keys) + ')', [values[k] for k in keys])
        self.db.commit()
        self.audit(case_id, actor, 'intake_created', {'source_version': canonical['source_version'], 'mapping_version': '1.0', 'visibility': canonical['evidence_visibility']})
        return case_id

    @staticmethod
    def require_open(row):
        if row['state'] == 'closed':
            raise ProgramError('CLOSED_CASE_REQUIRES_EXPLICIT_SOURCE_CHANGE')

    def assign(self, case_id, owner, actor='program_coordinator'):
        self.require_role(actor, 'program_coordinator')
        if not isinstance(owner, str) or not owner:
            raise ProgramError('OWNER_REQUIRED')
        old = self.row(case_id)
        self.require_open(old)
        self.update(case_id, action_owner=owner, handoff_accepted=0, state='assigned')
        self.audit(case_id, actor, 'owner_assigned', {'previous_owner': old['action_owner'], 'owner': owner})

    def accept_handoff(self, case_id, actor):
        row = self.row(case_id)
        self.require_open(row)
        self.require_role(actor, row['action_owner'])
        self.update(case_id, handoff_accepted=1)
        self.audit(case_id, actor, 'handoff_accepted', {})

    def record_decision(self, case_id, evidence_ref, actor='counsel'):
        row = self.row(case_id)
        self.require_open(row)
        self.require_role(actor, row['decision_authority'])
        if not row['action_owner']:
            raise ProgramError('ACTION_OWNER_REQUIRED')
        if not row['handoff_accepted']:
            raise ProgramError('HANDOFF_NOT_ACCEPTED')
        if not evidence_ref:
            raise ProgramError('DECISION_REFERENCE_REQUIRED')
        self.update(case_id, decision_evidence_ref=evidence_ref, approved_source_version=row['source_version'], state='ready_to_execute')
        self.audit(case_id, actor, 'decision_recorded', {'source_version': row['source_version'], 'evidence_ref': evidence_ref})

    def record_execution(self, case_id, receipt, actor):
        row = self.row(case_id)
        self.require_open(row)
        self.require_role(actor, row['action_owner'])
        if not row['handoff_accepted']:
            raise ProgramError('HANDOFF_NOT_ACCEPTED')
        if row['decision_needed'] and (not row['decision_evidence_ref'] or row['approved_source_version'] != row['source_version']):
            raise ProgramError('CURRENT_DECISION_REQUIRED')
        if not receipt:
            raise ProgramError('RECEIPT_REQUIRED')
        self.update(case_id, execution_receipt_ref=receipt, execution_source_version=row['source_version'], state='pending_confirmation')
        self.audit(case_id, actor, 'execution_recorded', {'receipt_ref': receipt, 'source_version': row['source_version']})

    def request_preservation(self, case_id, actor='program_coordinator'):
        self.require_role(actor, 'program_coordinator')
        self.require_open(self.row(case_id))
        self.update(case_id, preservation_status='pending')
        self.audit(case_id, actor, 'preservation_review_requested', {'note': 'Request only; no legal determination or deletion action.'})

    def decide_preservation(self, case_id, status, decision_ref, owner=None, next_review=None, actor='counsel'):
        self.require_role(actor, 'counsel')
        if status not in {'active', 'released'} or not decision_ref:
            raise ProgramError('PRESERVATION_DECISION_REQUIRED')
        if next_review:
            parse_time(next_review)
        self.update(case_id, preservation_status=status, preservation_decision_ref=decision_ref, preservation_owner=owner, preservation_accepted=0, preservation_next_review=next_review)
        self.audit(case_id, actor, 'preservation_decision_recorded', {'status': status, 'decision_ref': decision_ref, 'owner': owner, 'next_review': next_review})

    def accept_preservation(self, case_id, actor):
        row = self.row(case_id)
        self.require_role(actor, row['preservation_owner'])
        self.update(case_id, preservation_accepted=1)
        self.audit(case_id, actor, 'preservation_followup_accepted', {'next_review': row['preservation_next_review']})

    def update_source(self, case_id, version, source_ref, actor='program_coordinator'):
        self.require_role(actor, 'program_coordinator')
        row = self.row(case_id)
        if version == row['source_version']:
            raise ProgramError('NEW_SOURCE_VERSION_REQUIRED')
        self.update(case_id, source_version=version, source_ref=source_ref, decision_evidence_ref=None, approved_source_version=None, execution_receipt_ref=None, execution_source_version=None, state='awaiting_counsel', last_blockers='[]')
        self.audit(case_id, actor, 'source_changed_reviews_invalidated', {'previous_version': row['source_version'], 'new_version': version})

    def close(self, case_id, actor='program_coordinator'):
        self.require_role(actor, 'program_coordinator')
        row = self.row(case_id)
        if row['state'] == 'closed':
            return
        reasons = []
        if not row['action_owner']: reasons.append('action_owner_missing')
        if not row['handoff_accepted']: reasons.append('handoff_not_accepted')
        if row['decision_needed'] and (not row['decision_evidence_ref'] or row['approved_source_version'] != row['source_version']): reasons.append('current_counsel_decision_missing')
        if not row['execution_receipt_ref'] or row['execution_source_version'] != row['source_version']: reasons.append('current_execution_receipt_missing')
        if row['preservation_status'] == 'pending': reasons.append('preservation_decision_pending')
        if row['preservation_status'] == 'active':
            if not row['preservation_owner'] or not row['preservation_accepted']: reasons.append('preservation_custodian_not_accepted')
            if not row['preservation_next_review'] or parse_time(row['preservation_next_review']) <= self.clock: reasons.append('preservation_next_review_missing_or_due')
            if not row['preservation_decision_ref']: reasons.append('preservation_decision_reference_missing')
        if reasons:
            self.update(case_id, state='blocked', last_blockers=stable_json(reasons))
            self.audit(case_id, actor, 'closure_blocked', {'reasons': reasons})
            raise ClosureBlocked(reasons)
        self.update(case_id, state='closed', last_blockers='[]')
        self.audit(case_id, actor, 'case_closed', {'preservation_status': row['preservation_status'], 'ongoing_preservation_owner': row['preservation_owner']})

    def report(self):
        # The checked-in SQL is the actual source of the generated reports.
        queries = {}
        name = None
        for line in (ROOT / 'reporting.sql').read_text().splitlines():
            if line.startswith('-- name: '):
                name = line[len('-- name: '):].strip()
                queries[name] = ''
            elif name:
                queries[name] += line + '\n'
        required = {'state_counts', 'overdue_cases', 'cases_by_owner', 'preservation_commitments'}
        if set(queries) != required:
            raise ProgramError('REPORT_QUERY_SET_MISMATCH')
        rows = {name: [dict(r) for r in self.db.execute(query, {'as_of': self.config['as_of']})] for name, query in queries.items()}
        states = {r['state']: r['case_count'] for r in rows['state_counts']}
        return {'as_of': self.config['as_of'], 'total_cases': sum(states.values()), 'states': states,
                'overdue_cases': rows['overdue_cases'], 'cases_by_owner': rows['cases_by_owner'],
                'preservation_commitments': rows['preservation_commitments']}


def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def exercise_workflows(program, intakes, scenarios):
    intake_by_key = {item['ticket_id']: item for item in intakes}
    results = []
    for scenario in scenarios:
        scenario_id = scenario['case_id']
        name = scenario['scenario']
        external = intake_by_key[scenario['external_key']]
        case_id = program.intake(external)
        owner = program.config['routing'][external['case_kind']]['suggested_owner']
        checks = []
        if name != 'missing_owner':
            program.assign(case_id, owner)
        if name not in {'missing_owner', 'unaccepted_handoff'}:
            program.accept_handoff(case_id, owner)
        if name not in {'missing_owner', 'unaccepted_handoff', 'missing_approval', 'duplicate_idempotent', 'conflicting_duplicate', 'overdue_reporting'}:
            program.record_decision(case_id, 'fixture://decisions/' + scenario_id)
        if name == 'missing_approval':
            try:
                program.record_decision(case_id, 'fixture://unauthorized', actor='program_coordinator')
            except ProgramError as exc:
                assert str(exc) == 'ROLE_NOT_PERMITTED'
                checks.append('coordinator_cannot_record_counsel_decision')
            else:
                raise AssertionError('Unauthorized counsel decision accepted')
        if name not in {'missing_owner', 'unaccepted_handoff', 'missing_approval', 'missing_receipt', 'duplicate_idempotent', 'conflicting_duplicate', 'overdue_reporting'}:
            program.record_execution(case_id, 'fixture://receipts/' + scenario_id, owner)
        if name in {'missing_owner', 'unaccepted_handoff'}:
            expected_error = 'ACTION_OWNER_REQUIRED' if name == 'missing_owner' else 'HANDOFF_NOT_ACCEPTED'
            try:
                program.record_decision(case_id, 'fixture://premature-decision/' + scenario_id)
            except ProgramError as exc:
                assert str(exc) == expected_error
                assert program.row(case_id)['state'] != 'ready_to_execute'
                assert program.row(case_id)['decision_evidence_ref'] is None
                checks.append('premature_decision_rejected_' + expected_error)
            else:
                raise AssertionError('Decision advanced without an accepted owner')
        expected_blocker = {
            'missing_owner': 'action_owner_missing', 'unaccepted_handoff': 'handoff_not_accepted',
            'missing_approval': 'current_counsel_decision_missing', 'missing_receipt': 'current_execution_receipt_missing',
            'pending_preservation': 'preservation_decision_pending',
            'active_preservation_missing_custodian': 'preservation_custodian_not_accepted',
            'source_change_invalidates_approval': 'current_counsel_decision_missing'
        }.get(name)
        if name == 'pending_preservation':
            program.request_preservation(case_id)
        if name in {'active_preservation_missing_custodian', 'active_preservation_accepted_custodian_close'}:
            program.request_preservation(case_id)
            program.decide_preservation(case_id, 'active', 'fixture://preservation/' + scenario_id, owner='records_custodian', next_review='2026-11-17T12:00:00Z')
            if name == 'active_preservation_accepted_custodian_close':
                program.accept_preservation(case_id, 'records_custodian')
        if name == 'duplicate_idempotent':
            again = program.intake(external)
            assert again == case_id
            count = program.db.execute('SELECT COUNT(*) FROM cases WHERE external_key = ?', (external['ticket_id'],)).fetchone()[0]
            assert count == 1
            checks.append('identical_duplicate_reuses_one_case')
        elif name == 'conflicting_duplicate':
            conflict = dict(external, subject='Different fictional payload under the same key')
            try:
                program.intake(conflict)
            except ProgramError as exc:
                assert str(exc) == 'IDEMPOTENCY_CONFLICT'
                checks.append('conflicting_duplicate_rejected')
            else:
                raise AssertionError('Conflicting duplicate accepted')
        elif name == 'overdue_reporting':
            report = program.report()
            assert case_id in {r['case_id'] for r in report['overdue_cases']}
            assert report['total_cases'] == len(scenarios)
            checks.append('fixed_clock_overdue_case_reported')
        else:
            if name == 'source_change_invalidates_approval':
                program.update_source(case_id, 'v2', 'fixture://sanitized/' + scenario_id + '/v2')
                changed = program.row(case_id)
                assert changed['approved_source_version'] is None and changed['execution_receipt_ref'] is None
                assert changed['state'] == 'awaiting_counsel'
                checks.append('source_change_invalidates_prior_decision_and_receipt')
            if expected_blocker:
                try:
                    program.close(case_id)
                except ClosureBlocked as exc:
                    assert expected_blocker in exc.reasons
                    checks.append(expected_blocker)
                else:
                    raise AssertionError('Closure unexpectedly allowed: ' + name)
            else:
                program.close(case_id)
                assert program.row(case_id)['state'] == 'closed'
                checks.append('closure_allowed_after_controls_satisfied')
                if name == 'active_preservation_accepted_custodian_close':
                    row = program.row(case_id)
                    assert row['preservation_status'] == 'active' and row['preservation_accepted'] == 1
                    checks.append('active_preservation_remains_active_after_case_close')
        row = program.row(case_id)
        results.append({'scenario_id': scenario_id, 'scenario': name, 'case_id': case_id, 'passed': True, 'final_state': row['state'], 'checks': '; '.join(checks)})
    return results


def make_report(metrics, report):
    lines = [
        '# Reproducible demonstration results', '',
        'Independent legal technology work sample. All records and candidate outputs are deliberately authored synthetic fixtures. No model calls or employer data.', '',
        'Fixed simulation clock: ' + report['as_of'], '',
        '## Executed checks', '',
        '| Check group | Cases | Matched expected outcome |', '| --- | ---: | ---: |',
        '| Output gate fixtures | {validation_cases} | {validation_checks_passed} |'.format(**metrics),
        '| Workflow scenarios | {workflow_scenarios} | {workflow_checks_passed} |'.format(**metrics), '',
        'Output gate counts: ' + ', '.join(k + '=' + str(v) for k, v in sorted(metrics['validation_gate_counts'].items())) + '.', '',
        'The deliberately unsound interpretation in Q16 passed the mechanical gate and remains in the human-review queue. Its REJECT_BY_DESIGN label is an authored answer key, not an independent human adjudication or a measured model error.', '',
        '## Synthetic case states', '',
        '| State | Count |', '| --- | ---: |'
    ]
    lines += ['| ' + k + ' | ' + str(v) + ' |' for k, v in sorted(report['states'].items())]
    lines += ['', 'Total cases: ' + str(report['total_cases']) + '. Overdue nonclosed cases at the fixed clock: ' + str(len(report['overdue_cases'])) + '.', '', '## Cases by operational owner', '', '| Owner | Cases | Open cases |', '| --- | ---: | ---: |']
    lines += ['| {action_owner} | {case_count} | {open_count} |'.format(**r) for r in report['cases_by_owner']]
    lines += ['', '## Overdue cases', '', '| Case | Due at UTC | Synthetic age in hours |', '| --- | --- | ---: |']
    lines += ['| {case_id} | {due_at} | {synthetic_age_hours} |'.format(**r) for r in report['overdue_cases']]
    lines += ['', '## Ongoing preservation commitments', '', '| Case | Case state | Preservation | Custodian | Accepted | Next review UTC |', '| --- | --- | --- | --- | --- | --- |']
    lines += ['| {case_id} | {state} | {preservation_status} | {owner} | {preservation_accepted} | {review} |'.format(owner=r['preservation_owner'] or 'Unassigned', review=r['preservation_next_review'] or 'Not set', **r) for r in report['preservation_commitments']]
    lines += ['', 'Closing CASE-W08 leaves its accepted preservation commitment active. Nothing in this prototype destroys or releases evidence.', '', '## Interpretation limits', '', 'These checks establish only that this implementation behaves as authored on this small fixture set. They do not measure LLM accuracy, hallucination rates, semantic correctness, production reliability, prompt-injection immunity, enterprise identity controls, user adoption, human response time, legal compliance, or ROI. Illustrative case review/completion targets and synthetic ages are not legal deadlines or observed service levels.', '']
    return '\n'.join(lines)


def run(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    config = load_json(ROOT / 'config.json')
    mapping = load_json(ROOT / 'canonical_field_mapping.json')
    source_docs = load_json(ROOT / 'fixtures/source_documents.json')
    documents = {doc['document_id']: doc for doc in source_docs}
    if len(documents) != len(source_docs):
        raise AssertionError('Duplicate source document IDs')
    for document in source_docs:
        canonical = '\n'.join(c['clause_id'] + '. ' + c['text'] for c in document['clauses'])
        if document['text'] != canonical:
            raise AssertionError('Source text and clause index disagree')
    validation_cases = load_json(ROOT / 'fixtures/output_cases.json')
    validation_results = []
    for fixture in validation_cases:
        result = validate_output(fixture['raw_output'], documents, config)
        matched = result['gate'] == fixture['expected_gate'] and (fixture['expected_code'] is None or result['code'] == fixture['expected_code'])
        if not matched:
            raise AssertionError('Output case failed: ' + fixture['case_id'] + ' ' + stable_json(result))
        validation_results.append({'case_id': fixture['case_id'], 'description': fixture['description'], 'expected_gate': fixture['expected_gate'], 'actual_gate': result['gate'], 'code': result['code'], 'passed': matched, 'authored_substantive_key': fixture['expected_substantive_disposition']})
    database = output_dir / 'operations.db'
    if database.exists(): database.unlink()
    program = Program(database, config, mapping)
    workflow_results = exercise_workflows(program, load_json(ROOT / 'fixtures/external_intake.json'), load_json(ROOT / 'fixtures/workflow_scenarios.json'))
    report = program.report()
    metrics = {
        'study_version': config['study_version'], 'as_of': config['as_of'],
        'data_status': 'deliberately_authored_synthetic_fixtures', 'model_status': 'NO_MODEL_CALLED',
        'validation_cases': len(validation_results),
        'validation_checks_passed': sum(row['passed'] for row in validation_results),
        'validation_gate_counts': dict(sorted(Counter(row['actual_gate'] for row in validation_results).items())),
        'semantic_negative_controls': sum(row['authored_substantive_key'] == 'REJECT_BY_DESIGN' for row in validation_results),
        'semantic_controls_entering_human_queue': sum(row['authored_substantive_key'] == 'REJECT_BY_DESIGN' and row['actual_gate'] == 'READY_FOR_HUMAN_REVIEW' for row in validation_results),
        'workflow_scenarios': len(workflow_results), 'workflow_checks_passed': sum(row['passed'] for row in workflow_results),
        'total_cases_in_database': report['total_cases'], 'case_states': report['states'],
        'overdue_nonclosed_cases': len(report['overdue_cases']),
        'active_preservation_cases_closed_with_followup': sum(r['state'] == 'closed' and r['preservation_status'] == 'active' and r['preservation_accepted'] == 1 for r in report['preservation_commitments']),
        'audit_events': program.db.execute('SELECT COUNT(*) FROM audit_events').fetchone()[0],
        'llm_accuracy': None, 'human_review_minutes': None, 'production_roi': None
    }
    write_csv(output_dir / 'validation_results.csv', validation_results, list(validation_results[0]))
    write_csv(output_dir / 'workflow_results.csv', workflow_results, list(workflow_results[0]))
    (output_dir / 'metrics.json').write_text(json.dumps(metrics, indent=2, sort_keys=True) + '\n')
    (output_dir / 'operations_report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    (output_dir / 'report.md').write_text(make_report(metrics, report), encoding='utf-8')
    fixture_files = [ROOT / 'config.json', ROOT / 'canonical_field_mapping.json', *sorted((ROOT / 'fixtures').glob('*.json'))]
    manifest = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in fixture_files}
    (output_dir / 'fixture_manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    execution_manifest = {'run.py': hashlib.sha256((ROOT / 'run.py').read_bytes()).hexdigest(), 'reporting.sql': hashlib.sha256((ROOT / 'reporting.sql').read_bytes()).hexdigest(), 'fixture_manifest.json': hashlib.sha256((output_dir / 'fixture_manifest.json').read_bytes()).hexdigest()}
    (output_dir / 'execution_manifest.json').write_text(json.dumps(execution_manifest, indent=2, sort_keys=True) + '\n')
    program.db.close()
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'outputs')
    parser.add_argument('--regression', action='store_true', help='Run twice in fresh directories and compare every generated artifact byte for byte.')
    args = parser.parse_args()
    if args.regression:
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / 'first', Path(directory) / 'second'
            metrics = run(first)
            run(second)
            names = sorted(path.name for path in first.iterdir())
            assert names == sorted(path.name for path in second.iterdir())
            for name in names:
                assert (first / name).read_bytes() == (second / name).read_bytes(), 'Nondeterministic artifact: ' + name
            print(stable_json({'regression': 'passed', 'artifacts_compared': len(names), 'metrics': metrics}))
    else:
        print(json.dumps(run(args.output_dir), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
