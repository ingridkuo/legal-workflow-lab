#!/usr/bin/env python3
"""Local, rule-based subcontract demonstration. No account, API or eSignature calls."""
import argparse
import copy
import csv
import hashlib
import json
import os
import sys
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATUSES = ('Intake', 'Legal Review', 'Business Approval', 'Ready for Signature',
            'Counterparty Signed', 'Executed', 'Rejected', 'Hold')
TERMINAL = {'Executed', 'Rejected'}
INTAKE_FIELDS = ('id', 'project_name', 'subcontractor_name', 'scope', 'requestor_id',
                 'subcontractor_signatory_id', 'amount_usd', 'submitted_at',
                 'needed_by_date', 'planned_start_date', 'contract_expiry_date',
                 'guarantee_required', 'insurance_required', 'exceptional_terms')
DOC_FIELDS = ('guarantee_reference', 'guarantee_expiry_date',
              'insurance_reference', 'insurance_expiry_date')

class WorkflowError(ValueError):
    pass

def iso(value):
    if not isinstance(value, str):
        raise WorkflowError('Timestamp must be an ISO string with explicit UTC timezone.')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise WorkflowError('Invalid ISO timestamp: '+str(value)) from exc
    if result.tzinfo is None or result.utcoffset() != timedelta(0):
        raise WorkflowError('Timestamp must use UTC (Z or +00:00).')
    return result

def utcstamp(value=None):
    return (iso(value) if value else datetime.now(timezone.utc)).isoformat(timespec='seconds').replace('+00:00', 'Z')

def day(value):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        raise WorkflowError('Invalid YYYY-MM-DD date: '+str(value)) from exc

def money(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise WorkflowError('amount_usd must be a positive decimal amount.') from exc
    try:
        valid = amount.is_finite() and amount > 0 and amount == amount.quantize(Decimal('0.01'))
    except InvalidOperation:
        valid = False
    if not valid:
        raise WorkflowError('amount_usd must be positive with at most two decimal places.')
    return amount

def load_rules(path=None):
    rules = json.loads(Path(path or ROOT/'approval_rules.json').read_text(encoding='utf-8'))
    if rules.get('currency') != 'USD' or not rules.get('base_review_roles'):
        raise WorkflowError('Rules must define USD and base_review_roles.')
    tiers = rules.get('business_review_tiers', [])
    prior = Decimal('0')
    if not tiers or tiers[-1].get('upper_bound_usd') is not None:
        raise WorkflowError('Rules require a final unbounded amount tier.')
    roles = set(rules['base_review_roles'] + [rules['exception_review_role']])
    for index, tier in enumerate(tiers):
        bound = tier['upper_bound_usd']
        if bound is None:
            if index != len(tiers)-1:
                raise WorkflowError('Only final tier can be unbounded.')
        else:
            bound = money(bound)
            if bound <= prior:
                raise WorkflowError('Amount tiers must increase.')
            prior = bound
        roles.update(tier['roles'])
    if not roles.issubset(rules.get('role_owners', {})) or any(not isinstance(rules['role_owners'][r], str) or not rules['role_owners'][r].strip() for r in roles):
        raise WorkflowError('All review roles must have nonblank configured owners.')
    for field in ['workflow_admin_id','company_signatory_id']:
        if not rules.get(field):
            raise WorkflowError('Missing rule: '+field)
    return rules

def route(amount, exceptional, rules):
    roles = list(rules['base_review_roles'])
    if exceptional:
        roles.append(rules['exception_review_role'])
    for tier in rules['business_review_tiers']:
        if tier['upper_bound_usd'] is None or money(amount) <= Decimal(tier['upper_bound_usd']):
            roles.extend(tier['roles'])
            return list(dict.fromkeys(roles))
    raise WorkflowError('No matching amount tier.')

def validate_intake(data):
    if not isinstance(data, dict):
        raise WorkflowError('Each intake must be a JSON object.')
    missing = [k for k in INTAKE_FIELDS if k not in data or data[k] is None or (isinstance(data[k], str) and not data[k].strip())]
    if missing:
        raise WorkflowError('Missing required fields: '+', '.join(missing))
    for field in INTAKE_FIELDS:
        if field not in ('amount_usd','guarantee_required','insurance_required','exceptional_terms') and not isinstance(data[field], str):
            raise WorkflowError(field+' must be text.')
    for field in ('guarantee_required', 'insurance_required', 'exceptional_terms'):
        if type(data[field]) is not bool:
            raise WorkflowError(field+' must be true or false.')
    for field in DOC_FIELDS+('exception_notes',):
        if field in data and not isinstance(data[field], str):
            raise WorkflowError(field+' must be text (use empty text when missing).')
    if data.get('currency', 'USD') != 'USD':
        raise WorkflowError('Only USD is supported by this fictional policy.')
    money(data['amount_usd'])
    iso(data['submitted_at'])
    for field in ('needed_by_date','planned_start_date','contract_expiry_date'):
        day(data[field])
    if day(data['contract_expiry_date']) < day(data['planned_start_date']):
        raise WorkflowError('contract_expiry_date cannot precede planned_start_date.')
    for field in ('guarantee_expiry_date', 'insurance_expiry_date'):
        if data.get(field):
            day(data[field])
    if data['exceptional_terms'] and not data.get('exception_notes', '').strip():
        raise WorkflowError('Nonstandard terms require exception_notes.')
    return data

def make_record(data, rules):
    validate_intake(data)
    if data['subcontractor_signatory_id'] == rules['company_signatory_id']:
        raise WorkflowError('Subcontractor and company signatories must be different people.')
    record = {k: copy.deepcopy(data[k]) for k in INTAKE_FIELDS}
    record.update({k: data.get(k, '') for k in DOC_FIELDS+('exception_notes',)})
    record.update(currency='USD', amount_usd=format(money(data['amount_usd']), '.2f'),
                  status='Intake', approvals=[], signatures=[], execution_date='',
                  company_signatory_id=rules['company_signatory_id'], policy_name=rules['policy_name'])
    for role in route(record['amount_usd'], record['exceptional_terms'], rules):
        record['approvals'].append({'role':role, 'owner_id':rules['role_owners'][role],
                                    'status':'Pending', 'at':'', 'actor_id':''})
    record['last_event_at'] = utcstamp(data['submitted_at'])
    record['hold_reasons'] = []
    return record

def pending(record):
    return next((x for x in record['approvals'] if x['status'] == 'Pending'), None)

def document_issues(record, as_of):
    result = []
    for kind in ('guarantee', 'insurance'):
        if record[kind+'_required']:
            if not record.get(kind+'_reference') or not record.get(kind+'_expiry_date'):
                result.append('Missing required '+kind+' reference and expiry date')
            elif day(record[kind+'_expiry_date']) < as_of:
                result.append('Required '+kind+' has expired')
    return result

def current_owner(record):
    status = record['status']
    if status in ('Intake','Hold'):
        return record['requestor_id']
    if status in ('Legal Review','Business Approval'):
        item = pending(record)
        return item['owner_id'] if item else ''
    if status == 'Ready for Signature':
        return record['subcontractor_signatory_id']
    if status == 'Counterparty Signed':
        return record['company_signatory_id']
    return ''

def review_status(record):
    item = pending(record)
    if not item:
        return None
    return 'Legal Review' if item['role'] in ('legal','senior_legal') else 'Business Approval'

def advance_to_signing(record, as_of):
    record['hold_reasons'] = document_issues(record, as_of)
    record['status'] = 'Hold' if record['hold_reasons'] else ('Counterparty Signed' if record['signatures'] else 'Ready for Signature')

def transition(record, action, actor, at, **kwargs):
    record = copy.deepcopy(record)
    timestamp = utcstamp(at)
    when = iso(timestamp)
    if when < iso(record['last_event_at']):
        raise WorkflowError('Event timestamp cannot precede the last event for this record.')
    if not actor or not actor.strip():
        raise WorkflowError('actor_id is required.')
    status = record['status']
    if status in TERMINAL:
        raise WorkflowError(status+' is terminal; create a new intake for any new work.')
    if action == 'start':
        if status != 'Intake':
            raise WorkflowError('Only Intake can be started.')
        if actor != record['requestor_id']:
            raise WorkflowError('Only the recorded requester can start this demo intake.')
        record['status'] = review_status(record)
    elif action in ('approve','reject'):
        if status not in ('Legal Review','Business Approval'):
            raise WorkflowError('Record is not awaiting a review.')
        item = pending(record)
        if actor == record['requestor_id']:
            raise WorkflowError('Requestors cannot approve or reject their own requests.')
        if actor != item['owner_id']:
            raise WorkflowError('Next reviewer is '+item['owner_id']+' ('+item['role']+').')
        if not kwargs.get('note','').strip():
            raise WorkflowError('Review decision requires a note.')
        item.update(status='Approved' if action == 'approve' else 'Rejected', at=timestamp, actor_id=actor, note=kwargs['note'])
        if action == 'reject':
            record['status'] = 'Rejected'
        else:
            record['status'] = review_status(record)
            if record['status'] is None:
                advance_to_signing(record, when.date())
    elif action == 'sign':
        if status not in ('Ready for Signature','Counterparty Signed'):
            raise WorkflowError('All required reviews and document checks must finish before signing.')
        if pending(record) or any(x['status'] != 'Approved' for x in record['approvals']):
            raise WorkflowError('Every required review must be approved.')
        expected = record['subcontractor_signatory_id'] if status == 'Ready for Signature' else record['company_signatory_id']
        if actor != expected:
            raise WorkflowError('Next demonstration signatory is '+expected+'.')
        if actor == record['requestor_id']:
            raise WorkflowError('Requester cannot act as the company/subcontractor signatory in this demo.')
        if document_issues(record, when.date()):
            advance_to_signing(record, when.date())
            record['last_event_at'] = timestamp
            return record
        role = 'subcontractor' if status == 'Ready for Signature' else 'company'
        record['signatures'].append({'role':role,'actor_id':actor,'at':timestamp,'demonstration_only':True})
        record['status'] = 'Counterparty Signed' if role == 'subcontractor' else 'Executed'
        if record['status'] == 'Executed':
            record['execution_date'] = when.date().isoformat()
    elif action in ('documents','check-docs'):
        if actor != record['requestor_id']:
            raise WorkflowError('Document updates/checks require the recorded requester in this demo.')
        changes = kwargs.get('changes', {})
        if not isinstance(changes, dict) or set(changes) - set(DOC_FIELDS):
            raise WorkflowError('Only document reference/expiry fields may be updated.')
        for key, value in changes.items():
            if not isinstance(value, str):
                raise WorkflowError('Document values must be text.')
            if key.endswith('_date') and value:
                day(value)
            record[key] = value
        if status in ('Ready for Signature','Counterparty Signed','Hold'):
            advance_to_signing(record, when.date())
    elif action == 'assign':
        if actor != kwargs.get('admin_id'):
            raise WorkflowError('Only configured workflow admin can reassign a pending reviewer.')
        item = next((x for x in record['approvals'] if x['role'] == kwargs.get('role')), None)
        reviewer = kwargs.get('reviewer_id','').strip()
        if not item or item['status'] != 'Pending':
            raise WorkflowError('Only an existing pending review can be reassigned.')
        if not reviewer or reviewer == record['requestor_id']:
            raise WorkflowError('Reassigned reviewer must be independent of the requester.')
        item['owner_id'] = reviewer
    else:
        raise WorkflowError('Unknown action: '+action)
    record['last_event_at'] = timestamp
    return record

def event_digest(event):
    raw = json.dumps(event, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

class EventStore:
    """Append-only via this CLI, with integrity checking. No authentication or secure notarization."""
    def __init__(self, path):
        self.path = Path(path)

    def _read(self, stream):
        stream.seek(0)
        events, records, prior = [], {}, '0'*64
        for number, line in enumerate(stream,1):
            if not line.strip():
                raise WorkflowError('Audit contains an empty line at '+str(number))
            try:
                event = json.loads(line)
                digest = event.pop('hash')
                if event.get('seq') != number or event.get('previous_hash') != prior or digest != event_digest(event):
                    raise WorkflowError('Audit integrity check failed at event '+str(number))
                event['hash'] = digest
                if event['record_id'] != event['record']['id']:
                    raise WorkflowError('Audit record ID mismatch.')
                iso(event['at'])
            except (KeyError, json.JSONDecodeError, TypeError) as exc:
                raise WorkflowError('Invalid audit event at line '+str(number)) from exc
            events.append(event)
            records[event['record_id']] = event['record']
            prior = digest
        return events, records

    def read(self):
        if not self.path.exists():
            return [], {}
        with self.path.open(encoding='utf-8') as stream:
            return self._read(stream)

    @property
    def lock_path(self):
        return Path(str(self.path)+'.lock')

    @contextmanager
    def _exclusive_lock(self):
        # Exclusive creation is portable to native Windows, Linux and macOS.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise WorkflowError(
                'Store is locked: '+str(self.lock_path)+'. Another writer may be running. '
                'If this is a stale lock, remove it manually only after confirming no workflow process is running.'
            ) from exc
        try:
            metadata = json.dumps({'pid':os.getpid(), 'created_at':utcstamp()})+'\n'
            os.write(descriptor, metadata.encode('utf-8'))
            os.close(descriptor)
            descriptor = None
            yield
        finally:
            if descriptor is not None:
                os.close(descriptor)
            self.lock_path.unlink()

    def mutate(self, callback):
        with self._exclusive_lock(), self.path.open('a+', encoding='utf-8') as stream:
            events, records = self._read(stream)
            additions = callback(copy.deepcopy(records))
            new_events = []
            prior = events[-1]['hash'] if events else '0'*64
            for action, actor, at, record, details in additions:
                event = {'seq':len(events)+len(new_events)+1, 'action':action,
                         'actor_id':actor, 'at':utcstamp(at),'record_id':record['id'],
                         'details':details,'record':record,'previous_hash':prior}
                event['hash'] = event_digest(event)
                prior = event['hash']
                new_events.append(event)
            stream.seek(0,2)
            stream.write(''.join(json.dumps(e, sort_keys=True, ensure_ascii=False)+'\n' for e in new_events))
            stream.flush()
            os.fsync(stream.fileno())
            return [event['record'] for event in new_events]

    def import_intakes(self, data, rules, actor):
        if not isinstance(actor, str) or not actor.strip():
            raise WorkflowError('Import actor_id is required.')
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data,list) or not data:
            raise WorkflowError('Import requires a nonempty JSON object/list.')
        prepared = [make_record(row, rules) for row in data]
        if len({r['id'] for r in prepared}) != len(prepared):
            raise WorkflowError('Import contains duplicate IDs.')
        def build(records):
            if set(records) & {r['id'] for r in prepared}:
                raise WorkflowError('A record ID already exists; no import written.')
            return [('intake', actor, r['submitted_at'], r, {'source':'guided or JSON intake'}) for r in prepared]
        return self.mutate(build)

    def act(self, record_id, action, actor, at, **kwargs):
        def build(records):
            if record_id not in records:
                raise WorkflowError('Unknown record: '+record_id)
            updated = transition(records[record_id], action, actor, at, **kwargs)
            details = {k:v for k,v in kwargs.items() if k != 'admin_id'}
            if action == 'sign' and updated['status'] == 'Hold':
                details['blocked_reasons'] = updated['hold_reasons']
                return [('signature_blocked',actor,at,updated,details)]
            return [(action,actor,at,updated,details)]
        return self.mutate(build)[0]

def snapshot_as_of(events, as_of):
    cutoff = datetime.combine(as_of+timedelta(days=1), time(), timezone.utc)
    records = {}
    for event in events:
        if iso(event['at']) < cutoff:
            records[event['record_id']] = event['record']
    return records

def report(events, as_of):
    records = snapshot_as_of(events, as_of)
    week_start = as_of-timedelta(days=as_of.weekday())
    active = [r for r in records.values() if r['status'] not in TERMINAL]
    overdue = [r['id'] for r in active if day(r['needed_by_date']) < as_of]
    stage = Counter(r['status'] for r in active)
    owners = Counter(current_owner(r) for r in active)
    guarantees = []
    for record in records.values():
        if not record['guarantee_required'] or record['status'] == 'Rejected' or day(record['contract_expiry_date']) < as_of:
            continue
        expiry = record.get('guarantee_expiry_date')
        status = 'Missing' if not record.get('guarantee_reference') or not expiry else 'Expired' if day(expiry) < as_of else 'Due within 30 days' if day(expiry) <= as_of+timedelta(days=30) else 'Current'
        guarantees.append({'id':record['id'],'status':status,'expiry_date':expiry})
    durations = []
    reviews = []
    rows = []
    for record in sorted(records.values(), key=lambda r:r['id']):
        signed = next((s for s in record['signatures'] if s['role'] == 'company'), None)
        turnaround = (iso(signed['at'])-iso(record['submitted_at'])).total_seconds()/86400 if signed else None
        if turnaround is not None:
            durations.append(turnaround)
        approved = [a for a in record['approvals'] if a['status']=='Approved']
        if approved and len(approved) == len(record['approvals']):
            reviews.append((max(iso(a['at']) for a in approved)-iso(record['submitted_at'])).total_seconds()/86400)
        active_case = record['status'] not in TERMINAL
        age = (as_of-iso(record['submitted_at']).date()).days
        rows.append({'id':record['id'],'project_name':record['project_name'],'amount_usd':record['amount_usd'],
                     'status':record['status'],'current_owner':current_owner(record),
                     'submitted_at':record['submitted_at'],'needed_by_date':record['needed_by_date'],
                     'age_days':age if active_case else '', 'overdue':active_case and day(record['needed_by_date']) < as_of,
                     'execution_date':record['execution_date'],'turnaround_days':round(turnaround,2) if turnaround is not None else '',
                     'guarantee_expiry_date':record['guarantee_expiry_date'],
                     'document_issues':'; '.join(document_issues(record,as_of)) if active_case else ''})
    result = {'as_of':as_of.isoformat(),'week_start':week_start.isoformat(),'total_records':len(records),
              'submitted_this_week':sum(week_start <= iso(r['submitted_at']).date() <= as_of for r in records.values()),
              'executed_this_week':sum(bool(r['execution_date']) and week_start <= day(r['execution_date']) <= as_of for r in records.values()),
              'open_count':len(active),'queue_by_stage':dict(sorted(stage.items())),
              'queue_by_owner':dict(sorted(owners.items())), 'overdue_ids':sorted(overdue),
              'ageing_days':{r['id']:(as_of-iso(r['submitted_at']).date()).days for r in active},
              'mean_execution_turnaround_days':round(sum(durations)/len(durations),2) if durations else None,
              'execution_turnaround_sample_size':len(durations),
              'mean_review_turnaround_days':round(sum(reviews)/len(reviews),2) if reviews else None,
              'review_turnaround_sample_size':len(reviews),
              'guarantee_status':guarantees,'rows':rows}
    return result

def slack_text(result):
    stage = '; '.join(k+': '+str(v) for k,v in result['queue_by_stage'].items())
    owners = '; '.join(k+': '+str(v) for k,v in result['queue_by_owner'].items())
    alerts = [x['id']+' ('+x['status']+(', '+x['expiry_date'] if x['expiry_date'] else '')+')' for x in result['guarantee_status'] if x['status'] != 'Current']
    ages = '; '.join(k+': '+str(v)+'d' for k,v in sorted(result['ageing_days'].items()))
    return '\n'.join([
      'FICTIONAL DEMO — Subcontract weekly report',
      'Period: '+result['week_start']+' to '+result['as_of']+' (UTC; Monday to as-of date)',
      f"Volume: {result['submitted_this_week']} submitted; {result['executed_this_week']} executed this week; {result['open_count']} open / {result['total_records']} total.",
      'Queue by stage: '+stage, 'Queue by owner: '+owners,
      'Overdue needed-by (active only): '+(', '.join(result['overdue_ids']) or 'None'),
      'Open aging (calendar days since intake): '+(ages or 'None'),
      f"Historical execution turnaround: {result['mean_execution_turnaround_days']} days mean (n={result['execution_turnaround_sample_size']}; UTC elapsed time).",
      f"Historical review turnaround: {result['mean_review_turnaround_days']} days mean (n={result['review_turnaround_sample_size']}; completed reviews only).",
      'Guarantee alerts (includes active executed contracts): '+('; '.join(alerts) or 'None'),
      'Local export only. No Slack message sent. Signatures are demonstration records only.',
      'No saved-time or productivity outcome has been measured.'
    ])+'\n'

def flatten(record, rules):
    row = {key:record.get(key,'') for key in INTAKE_FIELDS+DOC_FIELDS+('currency','exception_notes','execution_date')}
    row.update(status=record['status'],current_owner=current_owner(record))
    for role in rules['role_owners']:
        item = next((a for a in record['approvals'] if a['role']==role),None)
        row[role+'_approval'] = item['status'] if item else 'Not required'
    for role in ('subcontractor','company'):
        row[role+'_signed_at'] = next((s['at'] for s in record['signatures'] if s['role']==role),'')
    row['hold_reason'] = '; '.join(record['hold_reasons'])
    return row

def build_demo(store, rules):
    if store.read()[0]:
        raise WorkflowError('Demo requires an empty/nonexistent store. Choose a new --db path.')
    inputs = json.loads((ROOT/'example_intakes.json').read_text(encoding='utf-8'))
    target = json.loads((ROOT/'sample_register.json').read_text(encoding='utf-8'))
    store.import_intakes(inputs,rules,'demo_loader')
    for data in target:
        if data['status']=='Intake':
            continue
        rid = data['id']
        start = data['submitted_at'].replace('T09:00:00Z','T10:00:00Z')
        record = store.act(rid,'start',data['requestor_id'],start)
        required = list(record['approvals'])
        for index,item in enumerate(required):
            desired = data[item['role']+'_approval']
            if desired == 'Pending':
                break
            decision_day = iso(data['submitted_at']).date()+timedelta(days=index+1)
            if rid=='SC-008':
                decision_day = date(2026,10,30)+timedelta(days=index)
            at = decision_day.isoformat()+'T12:00:00Z'
            record = store.act(rid,'reject' if desired=='Rejected' else 'approve',item['owner_id'],at,note='Synthetic demonstration decision.')
            if desired=='Rejected':
                break
        for role in ('subcontractor','company'):
            if data[role+'_signed_at']:
                actor = data['subcontractor_signatory_id'] if role=='subcontractor' else rules['company_signatory_id']
                record = store.act(rid,'sign',actor,data[role+'_signed_at'])
    return store.read()[1]

def guided_intake():
    print('Fictional demo intake. Every value remains local; use synthetic data only.')
    result = {}
    labels = {'id':'Request ID', 'requestor_id':'Requester ID', 'exceptional_terms':'Nonstandard terms', 'amount_usd':'Amount (USD)', 'submitted_at':'Submitted timestamp', 'subcontractor_signatory_id':'Subcontractor signatory ID'}
    for key in INTAKE_FIELDS:
        label = labels.get(key, key.replace('_',' ').capitalize())
        if key in ('guarantee_required','insurance_required','exceptional_terms'):
            while True:
                text = input(label+' [yes/no]: ').strip().lower()
                if text in ('yes','y','no','n'):
                    result[key] = text in ('yes','y')
                    break
                print('Enter yes or no.')
        elif key == 'submitted_at':
            result[key] = input(label+' [UTC ISO timestamp; blank=now]: ').strip() or utcstamp()
        else:
            result[key] = input(label+': ').strip()
    if result['exceptional_terms']:
        result['exception_notes'] = input('Nonstandard terms notes: ').strip()
    for kind in ('guarantee','insurance'):
        if result[kind+'_required']:
            result[kind+'_reference'] = input(kind+'_reference [blank=missing]: ').strip()
            result[kind+'_expiry_date'] = input(kind+'_expiry_date [YYYY-MM-DD; blank=missing]: ').strip()
    return result

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',default=str(ROOT/'demo_events.jsonl'),help='Append-only local event file (default: demo_events.jsonl)')
    p.add_argument('--rules',default=str(ROOT/'approval_rules.json'))
    subs=p.add_subparsers(dest='command',required=True)
    subs.add_parser('demo',help='Populate empty store with ten fully synthetic cases')
    imp=subs.add_parser('import',help='Validate and import JSON intake object/list')
    imp.add_argument('file'); imp.add_argument('--actor',default='demo_loader')
    form=subs.add_parser('intake',help='Guided local intake form'); form.add_argument('--actor',default='demo_loader')
    subs.add_parser('list')
    show=subs.add_parser('show'); show.add_argument('id')
    hist=subs.add_parser('history'); hist.add_argument('id',nargs='?')
    subs.add_parser('verify',help='Verify event sequence and hash chain')
    for name in ('start','approve','reject','sign','documents','check-docs','assign'):
        cmd=subs.add_parser(name); cmd.add_argument('id'); cmd.add_argument('--actor',required=True); cmd.add_argument('--at',default=None)
        if name in ('approve','reject'):
            cmd.add_argument('--note',required=True)
        if name=='documents':
            cmd.add_argument('--file',required=True,help='JSON object with document reference/expiry fields')
        if name=='assign':
            cmd.add_argument('--role',required=True); cmd.add_argument('--reviewer-id',required=True)
    rep=subs.add_parser('report'); rep.add_argument('--as-of',default='2026-11-11'); rep.add_argument('--out-dir',default=str(ROOT/'exports'))
    reg=subs.add_parser('export-register'); reg.add_argument('--as-of',default='2026-11-11'); reg.add_argument('--file',default=str(ROOT/'live_register.json'))
    return p

def main(argv=None):
    args=parser().parse_args(argv)
    try:
        rules=load_rules(args.rules); store=EventStore(args.db)
        command=args.command
        if command=='demo':
            records=build_demo(store,rules); print('Created '+str(len(records))+' synthetic cases. No external actions performed.')
        elif command in ('intake','import'):
            data=guided_intake() if command=='intake' else json.loads(Path(args.file).read_text(encoding='utf-8'))
            added=store.import_intakes(data,rules,args.actor); print('Validated/imported '+str(len(added))+' intake(s). Use start to begin Legal Review.')
        elif command in ('start','approve','reject','sign','documents','check-docs','assign'):
            extra={}
            if command in ('approve','reject'): extra['note']=args.note
            if command=='documents': extra['changes']=json.loads(Path(args.file).read_text(encoding='utf-8'))
            if command=='assign': extra.update(role=args.role,reviewer_id=args.reviewer_id,admin_id=rules['workflow_admin_id'])
            record=store.act(args.id,command,args.actor,utcstamp(args.at),**extra)
            print(json.dumps({'id':record['id'],'status':record['status'],'current_owner':current_owner(record),'hold_reasons':record['hold_reasons']},indent=2))
        elif command=='verify':
            events,records=store.read(); print(f'PASS: {len(events)} events; {len(records)} records; SHA-256 sequence/hash chain valid.')
        elif command=='show':
            events,records=store.read()
            if args.id not in records: raise WorkflowError('Unknown record: '+args.id)
            print(json.dumps(records[args.id],indent=2))
        elif command=='list':
            print(json.dumps([flatten(r,rules) for r in store.read()[1].values()],indent=2))
        elif command=='history':
            print(json.dumps([e for e in store.read()[0] if not args.id or e['record_id']==args.id],indent=2))
        elif command=='export-register':
            records=snapshot_as_of(store.read()[0],day(args.as_of)); path=Path(args.file); path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps([flatten(r,rules) for r in sorted(records.values(),key=lambda x:x['id'])],indent=2)+'\n',encoding='utf-8')
            print(str(path.resolve()))
        elif command=='report':
            result=report(store.read()[0],day(args.as_of)); out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
            (out/'weekly_report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
            (out/'slack_ready.txt').write_text(slack_text(result),encoding='utf-8')
            fields=list(result['rows'][0]) if result['rows'] else ['id','status','current_owner','age_days','overdue']
            with (out/'weekly_register.csv').open('w',newline='',encoding='utf-8') as stream:
                writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader(); writer.writerows(result['rows'])
            print(slack_text(result),end=''); print('Exports: '+str(out.resolve()))
        return 0
    except (WorkflowError,OSError,json.JSONDecodeError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr); return 2

if __name__=='__main__':
    sys.exit(main())
