"""Failure-oriented checks of the offline NDA evaluation harness."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('run_lab', HERE / 'run_lab.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.labels, cls.policy, cls.schema, cls.sources = lab.load_inputs(lab.ROOT)
        cls.cases = {c['document_id']: c for c in cls.labels['cases'] if c['document_id'] in ['NDA-06', 'NDA-07']}
        saved = lab.read_json(lab.ROOT / 'repeatability/runs/run_a.json')
        cls.reviews = [r for r in saved if r['document_id'] in cls.cases]

    def fresh(self):
        return copy.deepcopy(self.reviews)

    def analyze(self, reviews, cases=None):
        return lab.analyze_batch(reviews, self.cases if cases is None else cases, self.sources, self.schema, self.policy['policy_id'], self.policy['rules'])

    def positive(self, reviews):
        return next(r for r in reviews if r['document_id'] == 'NDA-07')

    def negative(self, reviews):
        return next(r for r in reviews if r['document_id'] == 'NDA-06')

    def test_baseline_retains_negative_control(self):
        totals, docs, *_ = self.analyze(self.fresh())
        self.assertEqual((totals['tp'], totals['fp'], totals['fn']), (1, 0, 0))
        self.assertEqual(len(docs), 2)

    def test_missing_document_fails_instead_of_inflating_recall(self):
        with self.assertRaisesRegex(lab.LabError, 'missing='):
            self.analyze([self.positive(self.fresh())])

    def test_duplicate_document_fails(self):
        reviews = self.fresh(); reviews.append(copy.deepcopy(reviews[0]))
        with self.assertRaisesRegex(lab.LabError, 'Duplicate document:'):
            self.analyze(reviews)

    def test_duplicate_rule_cannot_double_true_positives(self):
        reviews = self.fresh(); p = self.positive(reviews); p['issues'].append(copy.deepcopy(p['issues'][0]))
        with self.assertRaisesRegex(lab.LabError, 'Duplicate document-rule'):
            self.analyze(reviews)

    def test_unknown_rule_fails_schema(self):
        reviews = self.fresh(); self.positive(reviews)['issues'][0]['rule_id'] = 'INVENTED'
        with self.assertRaises(lab.LabError):
            self.analyze(reviews)

    def test_extra_property_fails_schema(self):
        reviews = self.fresh(); reviews[0]['approval'] = True
        with self.assertRaisesRegex(lab.LabError, 'unexpected approval'):
            self.analyze(reviews)

    def test_human_gate_cannot_be_disabled(self):
        reviews = self.fresh(); reviews[0]['human_review_required'] = False
        with self.assertRaisesRegex(lab.LabError, 'const differs'):
            self.analyze(reviews)

    def test_fabricated_quote_counts_fp_and_fn(self):
        reviews = self.fresh(); self.positive(reviews)['issues'][0]['source_quote'] = 'The parties agreed to a ten-year term.'
        totals = self.analyze(reviews)[0]
        self.assertEqual((totals['tp'], totals['fp'], totals['fn'], totals['unsupported_quotes']), (0, 1, 1, 1))
        self.assertEqual(totals['presence_tp'], 1)

    def test_real_quote_under_wrong_section_is_not_supported_match(self):
        reviews = self.fresh(); self.positive(reviews)['issues'][0]['source_locator'] = 'Section 1'
        totals = self.analyze(reviews)[0]
        self.assertEqual((totals['tp'], totals['fp'], totals['fn']), (0, 1, 1))
        self.assertEqual(totals['unsupported_quotes'], 0)
        self.assertEqual(totals['wrong_locations'], 1)

    def test_unknown_section_is_not_supported(self):
        reviews = self.fresh(); self.positive(reviews)['issues'][0]['source_locator'] = 'Section 999'
        self.assertEqual(self.analyze(reviews)[0]['wrong_locations'], 1)

    def test_supported_extra_flag_is_false_positive_under_key(self):
        reviews = self.fresh(); n = self.negative(reviews)
        text = lab.sections(self.sources['NDA-06'])['Section 5'].strip()
        issue = copy.deepcopy(self.positive(reviews)['issues'][0]); issue['source_quote'] = text
        n['issues'] = [issue]; n['risk'] = 'YELLOW'
        totals = self.analyze(reviews)[0]
        self.assertEqual((totals['tp'], totals['fp'], totals['fn']), (1, 1, 0))
        self.assertEqual(totals['precision'], 0.5)

    def test_zero_denominators_are_undefined(self):
        reviews = self.fresh(); n = self.negative(reviews)
        totals = self.analyze([n], {'NDA-06': self.cases['NDA-06']})[0]
        self.assertIsNone(totals['precision']); self.assertIsNone(totals['recall'])

    def test_miss_without_findings_has_zero_recall_not_perfect_precision(self):
        reviews = self.fresh(); p = self.positive(reviews); p['issues'] = []; p['risk'] = 'GREEN'
        totals = self.analyze(reviews)[0]
        self.assertIsNone(totals['precision']); self.assertEqual(totals['recall'], 0)
        self.assertEqual(totals['fn'], 1)

    def test_three_identical_misses_are_stable_but_wrong(self):
        reviews = self.fresh(); p = self.positive(reviews); p['issues'] = []; p['risk'] = 'GREEN'
        analysis = self.analyze(reviews)
        rows = lab.consistency_rows([analysis, analysis, analysis], self.cases, self.policy['rules'])
        positive = next(r for r in rows if r['reference_positive'])
        self.assertTrue(positive['presence_agreement'])
        self.assertTrue(positive['missed_in_every_run'])
        self.assertFalse(positive['supported_in_every_run'])

    def test_one_changed_detection_is_unstable(self):
        good = self.analyze(self.fresh())
        reviews = self.fresh(); p = self.positive(reviews); p['issues'] = []; p['risk'] = 'GREEN'
        missed = self.analyze(reviews)
        rows = lab.consistency_rows([good, missed, good], self.cases, self.policy['rules'])
        positive = next(r for r in rows if r['reference_positive'])
        self.assertTrue(positive['unstable_supported_detection'])
        self.assertFalse(positive['presence_agreement'])

    def test_consistency_includes_negative_opportunities(self):
        good = self.analyze(self.fresh())
        rows = lab.consistency_rows([good, good, good], self.cases, self.policy['rules'])
        self.assertEqual(len(rows), 2 * 15)
        self.assertEqual(sum(not r['reference_positive'] for r in rows), 29)

    def test_severity_mismatch_is_reported_separately(self):
        reviews = self.fresh(); p = self.positive(reviews); p['issues'][0]['severity'] = 'RED'; p['risk'] = 'RED'
        totals = self.analyze(reviews)[0]
        self.assertEqual(totals['tp'], 1)
        self.assertEqual(totals['severity_differences'], 1)
        self.assertEqual(totals['reference_route_differences'], 1)
        self.assertEqual(totals['internal_route_errors'], 0)

    def test_highest_severity_route_is_checked(self):
        reviews = self.fresh(); self.positive(reviews)['risk'] = 'GREEN'
        self.assertEqual(self.analyze(reviews)[0]['internal_route_errors'], 1)

    def test_source_request_status_is_checked(self):
        cases = {c['document_id']: c for c in self.labels['cases'] if c['document_id'] == 'NDA-18'}
        reviews = [r for r in lab.read_json(lab.ROOT / 'repeatability/runs/run_a.json') if r['document_id'] in cases]
        reviews[0]['review_status'] = 'REVIEW_READY'
        totals = self.analyze(reviews, cases)[0]
        self.assertEqual(totals['internal_status_errors'], 1)
        self.assertEqual(totals['reference_status_differences'], 1)

    def test_unknown_schema_keyword_cannot_be_silently_ignored(self):
        schema = copy.deepcopy(self.schema); schema['not'] = {}
        with self.assertRaisesRegex(lab.LabError, 'Unsupported schema'):
            lab.validate_schema(self.reviews[0], schema)

if __name__ == '__main__':
    unittest.main(verbosity=2)
