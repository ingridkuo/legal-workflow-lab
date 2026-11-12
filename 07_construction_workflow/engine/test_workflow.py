"""Behavior tests for the fictional local workflow; no external calls."""
import copy
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
import workflow as w

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.rules=w.load_rules()
        self.input=json.loads((w.ROOT/'example_intakes.json').read_text(encoding='utf-8'))[0]
        self.input['id']='TEST-001'
        self.input['submitted_at']='2026-11-01T09:00:00Z'
        self.record=w.make_record(self.input,self.rules)

    def started(self, **overrides):
        data={**self.input,**overrides}
        r=w.make_record(data,self.rules)
        return w.transition(r,'start',r['requestor_id'],'2026-11-01T10:00:00Z')

    def reviewed(self, **overrides):
        r=self.started(**overrides)
        for index, item in enumerate(copy.deepcopy(r['approvals'])):
            r=w.transition(r,'approve',item['owner_id'],f'2026-11-0{index+2}T12:00:00Z',note='Demo review complete')
        return r

    def test_exact_threshold_boundaries(self):
        for amount,roles in [
          ('0.01',['legal','project_manager']),
          ('50000.00',['legal','project_manager']),
          ('50000.01',['legal','project_manager','finance']),
          ('250000.00',['legal','project_manager','finance']),
          ('250000.01',['legal','project_manager','finance','executive'])]:
            with self.subTest(amount=amount):
                self.assertEqual(w.route(amount,False,self.rules),roles)

    def test_low_value_exception_escalates_senior_legal_before_business(self):
        self.assertEqual(w.route('1.00',True,self.rules),['legal','senior_legal','project_manager'])
        r=self.started(amount_usd='1.00',exceptional_terms=True,exception_notes='Nonstandard indemnity')
        r=w.transition(r,'approve','legal_001','2026-11-02T12:00:00Z',note='Escalate')
        self.assertEqual(r['status'],'Legal Review')
        self.assertEqual(w.current_owner(r),'senior_legal_001')

    def test_rules_are_configurable_and_existing_route_is_snapshotted(self):
        rules=copy.deepcopy(self.rules)
        rules['business_review_tiers'][0]['upper_bound_usd']='10000.00'
        new=w.make_record(self.input,rules)
        self.assertEqual(len(new['approvals']),3)
        self.assertEqual(len(self.record['approvals']),2)

    def test_missing_required_intake_fields(self):
        for key in w.INTAKE_FIELDS:
            data=copy.deepcopy(self.input); del data[key]
            with self.subTest(key=key),self.assertRaises(w.WorkflowError):
                w.make_record(data,self.rules)

    def test_money_invalid_values(self):
        for value in [True,False,'NaN','Infinity','-1','0','2.001','1e500','bad']:
            with self.subTest(value=value),self.assertRaises(w.WorkflowError):
                w.money(value)

    def test_boolean_fields_are_strict(self):
        for field in ['exceptional_terms','guarantee_required','insurance_required']:
            with self.subTest(field=field),self.assertRaises(w.WorkflowError):
                w.make_record({**self.input,field:'false'},self.rules)

    def test_exception_requires_explanation(self):
        with self.assertRaises(w.WorkflowError):
            self.started(exceptional_terms=True,exception_notes='')

    def test_explicit_utc_timestamps_required(self):
        for value in ['2026-11-01T09:00:00','2026-11-01','2026-11-01T09:00:00+01:00']:
            with self.subTest(value=value),self.assertRaises(w.WorkflowError): w.iso(value)
        self.assertEqual(w.utcstamp('2026-11-01T09:00:00+00:00'),'2026-11-01T09:00:00Z')

    def test_contract_expiry_order_and_date_validation(self):
        for changes in [{'contract_expiry_date':'2026-01-01'},{'needed_by_date':'2026-02-30'},{'insurance_expiry_date':123}]:
            with self.subTest(changes=changes),self.assertRaises(w.WorkflowError): self.started(**changes)

    def test_import_cannot_forge_status_approvals_or_signatures(self):
        data={**self.input,'status':'Executed','approvals':[{'status':'Approved'}],'signatures':[{'role':'company'}]}
        r=w.make_record(data,self.rules)
        self.assertEqual(r['status'],'Intake'); self.assertEqual(r['signatures'],[])
        self.assertTrue(all(x['status']=='Pending' for x in r['approvals']))

    def test_requestor_self_approval_blocked_even_when_configured_as_owner(self):
        r=self.started(requestor_id='legal_001')
        with self.assertRaisesRegex(w.WorkflowError,'own requests'):
            w.transition(r,'approve','legal_001','2026-11-02T12:00:00Z',note='Self')

    def test_sequential_approval_cannot_skip_legal(self):
        r=self.started(amount_usd='300000.00')
        for actor in ['finance_001','pm_001','exec_001','intruder']:
            with self.subTest(actor=actor),self.assertRaises(w.WorkflowError):
                w.transition(r,'approve',actor,'2026-11-02T12:00:00Z',note='Too early')

    def test_decision_requires_note(self):
        r=self.started()
        with self.assertRaises(w.WorkflowError): w.transition(r,'approve','legal_001','2026-11-02T12:00:00Z',note='')

    def test_no_premature_signatures_or_company_first(self):
        with self.assertRaises(w.WorkflowError):
            w.transition(self.started(),'sign','sub_signatory_001','2026-11-02T12:00:00Z')
        r=self.reviewed()
        self.assertEqual(r['status'],'Ready for Signature')
        with self.assertRaises(w.WorkflowError): w.transition(r,'sign','company_signatory_001','2026-11-05T12:00:00Z')

    def test_authorized_company_only_after_counterparty(self):
        r=self.reviewed()
        r=w.transition(r,'sign','sub_signatory_001','2026-11-05T12:00:00Z')
        self.assertEqual(r['status'],'Counterparty Signed')
        for actor in ['intruder','sub_signatory_001']:
            with self.subTest(actor=actor),self.assertRaises(w.WorkflowError): w.transition(r,'sign',actor,'2026-11-06T12:00:00Z')
        r=w.transition(r,'sign','company_signatory_001','2026-11-06T12:00:00Z')
        self.assertEqual(r['status'],'Executed'); self.assertEqual(r['execution_date'],'2026-11-06')
        self.assertTrue(all(s['demonstration_only'] for s in r['signatures']))

    def test_executed_and_rejected_are_terminal(self):
        r=self.reviewed(); r=w.transition(r,'sign','sub_signatory_001','2026-11-05T12:00:00Z'); r=w.transition(r,'sign','company_signatory_001','2026-11-06T12:00:00Z')
        rejected=w.transition(self.started(),'reject','legal_001','2026-11-02T12:00:00Z',note='Decline')
        for record in [r,rejected]:
            for action in ['approve','start','sign','documents','assign','check-docs']:
                with self.subTest(status=record['status'],action=action),self.assertRaises(w.WorkflowError):
                    w.transition(record,action,record['requestor_id'],'2026-11-07T12:00:00Z')

    def test_missing_guarantee_hold_then_resolution(self):
        r=self.reviewed(guarantee_required=True,guarantee_reference='',guarantee_expiry_date='')
        self.assertEqual(r['status'],'Hold')
        with self.assertRaises(w.WorkflowError): w.transition(r,'sign','sub_signatory_001','2026-11-05T12:00:00Z')
        r=w.transition(r,'documents',r['requestor_id'],'2026-11-05T12:00:00Z',changes={'guarantee_reference':'G-test','guarantee_expiry_date':'2027-01-01'})
        self.assertEqual(r['status'],'Ready for Signature')

    def test_missing_insurance_also_holds(self):
        r=self.reviewed(insurance_reference='')
        self.assertEqual(r['status'],'Hold')
        self.assertIn('insurance',r['hold_reasons'][0])

    def test_expiry_between_reviews_and_signature_blocks_then_holds(self):
        r=self.reviewed(insurance_expiry_date='2026-11-04')
        self.assertEqual(r['status'],'Ready for Signature')
        r=w.transition(r,'sign','sub_signatory_001','2026-11-05T12:00:00Z')
        self.assertEqual(r['status'],'Hold')
        self.assertEqual(r['signatures'],[])

    def test_expiry_after_counterparty_signature_can_resume_company_stage(self):
        r=self.reviewed(insurance_expiry_date='2026-11-05')
        r=w.transition(r,'sign','sub_signatory_001','2026-11-05T12:00:00Z')
        r=w.transition(r,'sign','company_signatory_001','2026-11-06T12:00:00Z')
        self.assertEqual(r['status'],'Hold'); self.assertEqual(len(r['signatures']),1)
        r=w.transition(r,'documents',r['requestor_id'],'2026-11-07T09:00:00Z',changes={'insurance_expiry_date':'2027-06-30'})
        self.assertEqual(r['status'],'Counterparty Signed')
        r=w.transition(r,'sign','company_signatory_001','2026-11-07T12:00:00Z')
        self.assertEqual(r['status'],'Executed')

    def test_distinct_signatories_required(self):
        with self.assertRaises(w.WorkflowError):
            self.started(subcontractor_signatory_id=self.rules['company_signatory_id'])

    def test_document_updates_cannot_inject_workflow_or_rewrite_signatures(self):
        with self.assertRaises(w.WorkflowError): w.transition(self.started(),'documents',self.input['requestor_id'],'2026-11-02T12:00:00Z',changes={'status':'Executed'})

    def test_expiry_today_is_valid(self):
        r=self.reviewed(insurance_expiry_date='2026-11-05')
        r=w.transition(r,'sign','sub_signatory_001','2026-11-05T12:00:00Z')
        self.assertEqual(r['status'],'Counterparty Signed')

    def test_event_timestamp_cannot_go_backwards(self):
        with self.assertRaises(w.WorkflowError): w.transition(self.started(),'approve','legal_001','2026-10-31T12:00:00Z',note='Past')

    def test_pending_reviewer_reassignment_requires_admin_and_independence(self):
        r=self.started(requestor_id='legal_001')
        for actor,new in [('intruder','new_legal'),('ops_001','legal_001')]:
            with self.subTest(actor=actor,new=new),self.assertRaises(w.WorkflowError):
                w.transition(r,'assign',actor,'2026-11-02T09:00:00Z',admin_id='ops_001',role='legal',reviewer_id=new)
        r=w.transition(r,'assign','ops_001','2026-11-02T09:00:00Z',admin_id='ops_001',role='legal',reviewer_id='new_legal')
        r=w.transition(r,'approve','new_legal','2026-11-02T12:00:00Z',note='Independent review')
        self.assertEqual(r['status'],'Business Approval')

class StoreAndReportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'events.jsonl'; self.store=w.EventStore(self.path); self.rules=w.load_rules()

    def test_existing_lock_blocks_write_without_removing_owners_lock(self):
        self.store.lock_path.write_text('active or stale lock',encoding='utf-8')
        with self.assertRaisesRegex(w.WorkflowError,'Store is locked'):
            self.store.mutate(lambda records: self.fail('Contended writer entered callback'))
        self.assertFalse(self.path.exists())
        self.assertEqual(self.store.lock_path.read_text(encoding='utf-8'),'active or stale lock')

    def test_lock_released_after_success_and_callback_failure(self):
        self.assertEqual(self.store.mutate(lambda records: []),[])
        self.assertFalse(self.store.lock_path.exists())
        def fail(records):
            self.assertTrue(self.store.lock_path.exists())
            raise w.WorkflowError('Synthetic callback failure')
        with self.assertRaisesRegex(w.WorkflowError,'Synthetic callback failure'):
            self.store.mutate(fail)
        self.assertFalse(self.store.lock_path.exists())
        self.assertEqual(self.store.mutate(lambda records: []),[])

    def test_lock_released_after_audit_validation_failure(self):
        self.path.write_text('invalid event\n',encoding='utf-8')
        before=self.path.read_bytes()
        with self.assertRaises(w.WorkflowError): self.store.mutate(lambda records: [])
        self.assertFalse(self.store.lock_path.exists())
        self.assertEqual(self.path.read_bytes(),before)

    def test_overlapping_writer_cannot_enter_or_remove_current_lock(self):
        other=w.EventStore(self.path)
        def outer(records):
            with self.assertRaisesRegex(w.WorkflowError,'Store is locked'):
                other.mutate(lambda inner: self.fail('Overlapping writer entered'))
            self.assertTrue(self.store.lock_path.exists())
            return []
        self.store.mutate(outer)
        self.assertFalse(self.store.lock_path.exists())

    def test_utf8_audit_round_trip_preserves_unicode_policy(self):
        data=json.loads((w.ROOT/'example_intakes.json').read_text(encoding='utf-8'))[0]
        self.rules['policy_name']='Fictional USD subcontract policy: café UTF-8 test'
        self.store.import_intakes(data,self.rules,'demo_loader')
        self.assertEqual(self.store.read()[1][data['id']]['policy_name'],self.rules['policy_name'])
        self.assertIn('café'.encode('utf-8'),self.path.read_bytes())

    def test_demo_matches_shared_final_fixture_exactly(self):
        records=w.build_demo(self.store,self.rules)
        expected=json.loads((w.ROOT/'sample_register.json').read_text(encoding='utf-8'))
        actual=[w.flatten(records[x['id']],self.rules) for x in expected]
        self.assertEqual(actual,expected)

    def test_audit_appends_keeps_prior_bytes_and_detects_edit(self):
        data=json.loads((w.ROOT/'example_intakes.json').read_text(encoding='utf-8'))[0]
        self.store.import_intakes(data,self.rules,'demo_loader'); before=self.path.read_bytes()
        self.store.act(data['id'],'start',data['requestor_id'],data['submitted_at'].replace('09:00','10:00'))
        self.assertTrue(self.path.read_bytes().startswith(before)); self.assertEqual(len(self.store.read()[0]),2)
        self.path.write_text(self.path.read_text(encoding='utf-8').replace('Harbor Office Interior Buildout','ALTERED',1),encoding='utf-8')
        with self.assertRaisesRegex(w.WorkflowError,'integrity'): self.store.read()

    def test_import_rejects_blank_actor(self):
        data=json.loads((w.ROOT/'example_intakes.json').read_text(encoding='utf-8'))[0]
        with self.assertRaises(w.WorkflowError): self.store.import_intakes(data,self.rules,'  ')
        self.assertEqual(self.store.read()[0],[])

    def test_import_duplicate_ids_is_atomic(self):
        data=json.loads((w.ROOT/'example_intakes.json').read_text(encoding='utf-8'))[0]
        with self.assertRaises(w.WorkflowError): self.store.import_intakes([data,data],self.rules,'demo_loader')
        self.assertEqual(self.store.read()[0],[])
        self.store.import_intakes(data,self.rules,'demo_loader'); before=self.path.read_bytes()
        with self.assertRaises(w.WorkflowError): self.store.import_intakes(data,self.rules,'demo_loader')
        self.assertEqual(self.path.read_bytes(),before)

    def test_report_counts_and_definitions(self):
        w.build_demo(self.store,self.rules); r=w.report(self.store.read()[0],date(2026,11,11))
        self.assertEqual(r['week_start'],'2026-11-09')
        self.assertEqual((r['total_records'],r['submitted_this_week'],r['executed_this_week'],r['open_count']),(10,2,1,8))
        self.assertEqual(r['overdue_ids'],['SC-002','SC-004','SC-007'])
        self.assertEqual(r['queue_by_stage'],{'Business Approval':2,'Counterparty Signed':1,'Hold':1,'Intake':1,'Legal Review':2,'Ready for Signature':1})
        self.assertEqual(r['queue_by_owner']['senior_legal_001'],1)
        self.assertEqual(r['ageing_days']['SC-004'],14)
        due=[x['id'] for x in r['guarantee_status'] if x['status']=='Due within 30 days']
        self.assertEqual(due,['SC-003','SC-008']); self.assertEqual(r['execution_turnaround_sample_size'],1)
        self.assertEqual(r['review_turnaround_sample_size'],4)
        self.assertIn('No Slack message sent',w.slack_text(r))

    def test_as_of_snapshot_excludes_future_events_and_records(self):
        w.build_demo(self.store,self.rules); r=w.report(self.store.read()[0],date(2026,11,9))
        self.assertEqual(r['total_records'],9); self.assertEqual(r['executed_this_week'],0)
        self.assertEqual(next(x for x in r['rows'] if x['id']=='SC-008')['status'],'Counterparty Signed')

    def test_guarantee_expiry_boundaries_and_rejected_exclusion(self):
        events=[]
        base=json.loads((w.ROOT/'example_intakes.json').read_text(encoding='utf-8'))[0]
        for n,expiry,status in [(1,'2026-11-11','Intake'),(2,'2026-12-11','Intake'),(3,'2026-12-12','Intake'),(4,'2026-11-10','Intake'),(5,'2026-11-11','Rejected')]:
            r=w.make_record({**base,'id':str(n),'guarantee_required':True,'guarantee_reference':'G','guarantee_expiry_date':expiry},self.rules)
            r['status']=status
            events.append({'at':base['submitted_at'],'record_id':str(n),'record':r})
        r=w.report(events,date(2026,11,11)); alerts={g['id']:g['status'] for g in r['guarantee_status']}
        self.assertEqual(alerts,{'1':'Due within 30 days','2':'Due within 30 days','3':'Current','4':'Expired'})

    def test_empty_report_has_no_fabricated_turnaround(self):
        r=w.report([],date(2026,11,11)); self.assertEqual(r['total_records'],0)
        self.assertIsNone(r['mean_execution_turnaround_days']); self.assertEqual(r['execution_turnaround_sample_size'],0)

if __name__=='__main__': unittest.main(verbosity=2)
