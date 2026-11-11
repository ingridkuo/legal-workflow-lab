"""Offline tests only: mocked HTTP responses are not model-study results."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import api_study as api

class APIStudyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'lab'
        shutil.copytree(api.ROOT, self.root, ignore=shutil.ignore_patterns('api_studies', '__pycache__'))
        self.calls = []
        self.pool = {}
        for name in ['v2_development', 'v2_heldout']:
            self.pool.update({r['document_id']:r for r in api.load(self.root / f'evaluation/saved_reviews/{name}.json')})

    def transport(self, payload, key, timeout):
        self.calls.append(copy.deepcopy(payload))
        doc = payload['input'][0]['content'].splitlines()[0].split(': ')[1]
        body = {'id':f'mocked-response-{len(self.calls)}', 'model':payload['model'], 'status':'completed',
                'usage':{'input_tokens':1,'output_tokens':1},
                'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(self.pool[doc])}]}]}
        return 200, {'x-request-id':f'mocked-request-{len(self.calls)}'}, json.dumps(body).encode()

    def smoke(self, name='smoke-test', transport=None):
        return api.execute(self.root, name, 'smoke', 'FAKE_TEST_KEY', 1, transport or self.transport)

    def test_plan_has_45_distinct_document_replicate_jobs(self):
        p = api.make_protocol(self.root,'full')
        self.assertEqual(45,len(p['jobs']))
        self.assertEqual(45,len({j['job_id'] for j in p['jobs']}))
        self.assertEqual(15,len({j['document_id'] for j in p['jobs']}))
        self.assertEqual(1,len({j['payload']['instructions'] for j in p['jobs']}))
        self.assertNotIn('expected', p['jobs'][0]['payload'])
        self.assertNotIn('reference_labels', json.dumps([j['payload'] for j in p['jobs']]))

    def test_smoke_calls_once_and_records_model_usage_ids(self):
        self.assertEqual('COMPLETE',self.smoke()['status'])
        r=api.load(self.root/'api_studies/smoke-test/jobs/run_a_NDA-01/result.json')
        self.assertEqual('mocked-response-1',r['response_id'])
        self.assertEqual('mocked-request-1',r['provider_request_id'])
        self.assertEqual(1,r['usage']['input_tokens'])
        self.assertNotIn('FAKE_TEST_KEY',''.join(p.read_text() for p in (self.root/'api_studies').rglob('*.json')))

    def test_request_omits_temperature_conversation_tools_and_prior_response(self):
        self.smoke()
        for field in ['temperature','top_p','previous_response_id','conversation','tools']:
            self.assertNotIn(field,self.calls[0])
        self.assertFalse(self.calls[0]['store'])

    def test_resume_does_not_repeat_accepted_call(self):
        self.smoke();result=self.smoke()
        self.assertEqual(1,len(self.calls))
        self.assertEqual(0,result['new_network_attempts'])

    def test_modified_configuration_blocks_resume(self):
        self.smoke()
        p=self.root/'api_study_config.json';c=api.load(p);c['reasoning_effort']='medium';api.write(p,c)
        with self.assertRaises(api.StudyError):self.smoke()
        self.assertEqual(1,len(self.calls))

    def test_response_mutation_blocks_score(self):
        self.smoke();p=self.root/'api_studies/smoke-test/jobs/run_a_NDA-01/response.json'
        p.write_text(p.read_text()+' ')
        with self.assertRaises(api.StudyError):api.score(self.root,'smoke-test')

    def test_request_mutation_blocks_resume_and_score(self):
        self.smoke();p=self.root/'api_studies/smoke-test/jobs/run_a_NDA-01/request.json'
        data=api.load(p);data['instructions']+=' modified';api.write(p,data)
        with self.assertRaises(api.StudyError):self.smoke()
        with self.assertRaises(api.StudyError):api.score(self.root,'smoke-test')

    def test_editable_result_id_must_match_provider_body(self):
        self.smoke();p=self.root/'api_studies/smoke-test/jobs/run_a_NDA-01/result.json'
        data=api.load(p);data['response_id']='invented-new-id';api.write(p,data)
        with self.assertRaises(api.StudyError):api.score(self.root,'smoke-test')

    def test_transport_metadata_mutation_blocks_score(self):
        self.smoke();p=self.root/'api_studies/smoke-test/jobs/run_a_NDA-01/transport.json'
        data=api.load(p);data['http_status']=429;api.write(p,data)
        with self.assertRaises(api.StudyError):api.score(self.root,'smoke-test')

    def test_incomplete_study_cannot_publish_metrics(self):
        api.execute(self.root,'full-test','full','FAKE_TEST_KEY',1,self.transport)
        with self.assertRaises(api.StudyError):api.score(self.root,'full-test')
        self.assertFalse((self.root/'api_studies/full-test/results_summary.json').exists())

    def test_full_study_scores_45_separate_mocked_responses(self):
        result=api.execute(self.root,'full-test','full','FAKE_TEST_KEY',45,self.transport)
        self.assertEqual('COMPLETE',result['status']);self.assertEqual(45,len(self.calls))
        scored=api.score(self.root,'full-test')
        self.assertEqual(45,scored['independent_api_responses'])
        self.assertEqual(16,scored['consistency']['supported_in_all_three'])
        self.assertEqual([1.0]*3,[r['recall'] for r in scored['runs']])

    def test_source_unsupported_output_counts_fp_and_fn(self):
        self.pool['NDA-07']['issues'][0]['source_quote']='fabricated source span'
        api.execute(self.root,'flawed-test','full','FAKE_TEST_KEY',45,self.transport)
        scored=api.score(self.root,'flawed-test')
        self.assertEqual([1]*3,[r['fp'] for r in scored['runs']])
        self.assertEqual([1]*3,[r['fn'] for r in scored['runs']])
        self.assertEqual(1,scored['consistency']['missed_in_all_three'])

    def bad_response(self, mutation, status=200):
        def send(payload,key,timeout):
            _,headers,raw=self.transport(payload,key,timeout)
            body=json.loads(raw);mutation(body)
            return status,headers,json.dumps(body).encode()
        return send

    def test_refusal_is_preserved_without_retry(self):
        t=self.bad_response(lambda b:b.update(output=[{'content':[{'type':'refusal','refusal':'mock'}]}]))
        with self.assertRaises(api.StudyError):self.smoke(transport=t)
        with self.assertRaises(api.StudyError):self.smoke()
        self.assertEqual(1,len(self.calls))
        self.assertTrue((self.root/'api_studies/smoke-test/jobs/run_a_NDA-01/response.json').exists())

    def test_incomplete_model_output_stops_without_score(self):
        with self.assertRaises(api.StudyError):self.smoke(transport=self.bad_response(lambda b:b.update(status='incomplete')))
        self.assertEqual(1,len(self.calls))

    def test_model_mismatch_stops(self):
        with self.assertRaises(api.StudyError):self.smoke(transport=self.bad_response(lambda b:b.update(model='different-model')))

    def test_malformed_output_stops(self):
        with self.assertRaises(api.StudyError):self.smoke(transport=self.bad_response(lambda b:b['output'][0]['content'][0].update(text='not JSON')))

    def test_duplicate_finding_stops_instead_of_silent_deduplication(self):
        full=api.make_protocol(self.root,'full');job=next(j for j in full['jobs'] if j['document_id']=='NDA-07')
        review=copy.deepcopy(self.pool['NDA-07']);review['issues'].append(copy.deepcopy(review['issues'][0]))
        body={'id':'mock','status':'completed','model':job['payload']['model'],'output':[{'content':[{'type':'output_text','text':json.dumps(review)}]}]}
        with self.assertRaises(api.StudyError):api.extract_review(body,job,job['payload']['model'],api.load(self.root/'review_output.schema.json'))

    def test_timeout_preserves_attempt_and_does_not_retry(self):
        def timeout(*args):raise TimeoutError('FAKE_TEST_KEY must never be saved')
        with self.assertRaises(api.StudyError):self.smoke(transport=timeout)
        with self.assertRaises(api.StudyError):self.smoke()
        failure=(self.root/'api_studies/smoke-test/jobs/run_a_NDA-01/failure.json').read_text()
        self.assertNotIn('FAKE_TEST_KEY',failure)

    def test_http_error_preserved_no_automatic_retry(self):
        with self.assertRaises(api.StudyError):self.smoke(transport=self.bad_response(lambda b:b.update(error='mock'),429))
        with self.assertRaises(api.StudyError):self.smoke()
        self.assertEqual(1,len(self.calls))

    def test_alias_model_and_path_traversal_rejected(self):
        p=self.root/'api_study_config.json';c=api.load(p);c['model']='gpt-5.4-mini';api.write(p,c)
        with self.assertRaises(api.StudyError):api.make_protocol(self.root,'full')
        with self.assertRaises(api.StudyError):api.study_path(self.root,'../outside')

    def test_transport_disables_redirects_before_following_other_host(self):
        observed=[]
        def make_opener(handler):
            observed.append(handler)
            class Stop:
                def open(self,*args,**kwargs):raise TimeoutError
            return Stop()
        with patch.object(api.urllib.request,'build_opener',make_opener):
            with self.assertRaises(TimeoutError):api.http_transport({},'FAKE_TEST_KEY',1)
        self.assertIsNone(observed[0].redirect_request(None,None,302,'redirect',{},'https://other.invalid/'))

    def test_schema_adaptation_does_not_change_original(self):
        original=api.load(self.root/'review_output.schema.json');before=copy.deepcopy(original)
        schema=api.api_schema(original)
        self.assertEqual(before,original)
        self.assertEqual({'type':'boolean','enum':[True]},schema['properties']['human_review_required'])
        self.assertNotIn('pattern',schema['properties']['document_id'])

if __name__=='__main__':unittest.main(verbosity=2)
