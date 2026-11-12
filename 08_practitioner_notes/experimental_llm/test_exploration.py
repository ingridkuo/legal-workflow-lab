"""Regression and adverse-input checks for the saved-response scorer."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import evaluate_exploration as evaluation

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text())


class SavedReviewScoringTests(unittest.TestCase):
    def setUp(self):
        self.documents = load('documents.json')
        self.original = load('provisional_answer_key.json')
        self.key = load('adjudicated_answer_key.json')
        self.response = load('raw_model_response.json')

    def score(self):
        return evaluation.score_reviews(self.documents, self.original, self.key, self.response)

    def test_saved_batch_has_eight_supported_pairs_and_six_issue_groups(self):
        metrics, rows, groups = self.score()
        self.assertEqual((metrics['review_documents'], metrics['finding_rows']), (8, 8))
        self.assertEqual((metrics['supported_true_positives'], metrics['false_positives'], metrics['false_negatives']), (8, 0, 0))
        self.assertEqual((metrics['adjudicated_precision'], metrics['adjudicated_recall']), (1.0, 1.0))
        self.assertEqual((metrics['actionable_issue_groups'], metrics['supported_actionable_issue_groups']), (6, 6))
        self.assertEqual(metrics['issue_groups_with_all_labels_supported'], 6)
        self.assertTrue(all(row['source_metadata_matches'] and row['quote_matches_cited_clause'] for row in rows))
        self.assertTrue(all(group['group_supported'] for group in groups))
        self.assertIsNone(metrics['model_accuracy'])
        self.assertIsNone(metrics['human_review_time_minutes'])

    def test_original_six_pair_denominator_remains_visible(self):
        metrics, rows, _ = self.score()
        self.assertEqual(metrics['provisional_key_pairs'], 6)
        self.assertEqual(metrics['provisional_key_pairs_present'], 6)
        extra = {(x['document_id'], x['rule_id']) for x in metrics['additional_label_pairs']}
        self.assertEqual(extra, {('A04', 'PURPOSE'), ('A06', 'PURPOSE')})
        self.assertEqual(sum(row['provisional_key_status'] == 'additional_label_accepted_by_adjudication' for row in rows), 2)
        self.assertEqual(metrics['unresolved_label_adjudications'], 0)

    def test_original_inputs_have_the_preserved_hashes(self):
        evaluation.check_frozen_inputs(ROOT, load('adjudication_v1_1.json'))
        self.assertEqual(hashlib.sha256((ROOT / 'provisional_answer_key.json').read_bytes()).hexdigest(),
                         '1f6ab18d6d20f9810bc24dd1be2543f495939638a6e2675af5a2dd89c3bea6c4')
        self.assertEqual(hashlib.sha256((ROOT / 'raw_model_response.json').read_bytes()).hexdigest(),
                         '7726316b42f0918888ea798d8460516999e85ed523764fa38f3b7a6cc61afb9d')

    def test_changed_original_key_is_rejected_by_integrity_check(self):
        record = load('adjudication_v1_1.json')
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            for name in record['preserved_inputs_sha256']:
                (base / name).write_bytes((ROOT / name).read_bytes())
            (base / 'provisional_answer_key.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Frozen input changed'):
                evaluation.check_frozen_inputs(base, record)

    def test_residuals_remains_primary_but_both_labels_are_retained(self):
        _, rows, groups = self.score()
        for doc_id in ['A04', 'A06']:
            group = next(g for g in groups if g['document_id'] == doc_id and g['primary_rule_id'] == 'RESIDUALS')
            self.assertEqual(group['supported_rule_ids'], ['PURPOSE', 'RESIDUALS'])
            matching = [row for row in rows if row['issue_group_id'] == group['issue_group_id']]
            self.assertEqual({row['rule_id'] for row in matching}, {'PURPOSE', 'RESIDUALS'})
            self.assertEqual({row['primary_rule_id'] for row in matching}, {'RESIDUALS'})

    def test_wrong_quote_counts_as_unsupported_finding_and_missed_reference(self):
        self.response['reviews'][1]['findings'][0]['quote'] = 'This quotation is not in the source.'
        metrics, _, _ = self.score()
        self.assertEqual((metrics['supported_true_positives'], metrics['false_positives'], metrics['false_negatives']), (7, 1, 1))
        self.assertEqual((metrics['adjudicated_precision'], metrics['adjudicated_recall']), (7 / 8, 7 / 8))

    def test_real_quote_in_wrong_clause_does_not_match_reference(self):
        finding = self.response['reviews'][1]['findings'][0]
        finding['clause_id'] = '1'
        finding['quote'] = self.documents[1]['clauses']['1']
        metrics, rows, _ = self.score()
        row = next(row for row in rows if row['document_id'] == 'A02')
        self.assertTrue(row['quote_matches_cited_clause'])
        self.assertFalse(row['reference_locator_matches'])
        self.assertEqual((metrics['false_positives'], metrics['false_negatives']), (1, 1))

    def test_stale_document_version_invalidates_every_finding_in_document(self):
        self.response['reviews'][5]['source_version'] = 'stale'
        metrics, _, _ = self.score()
        self.assertEqual(metrics['source_metadata_matches'], 7)
        self.assertEqual((metrics['supported_true_positives'], metrics['false_positives'], metrics['false_negatives']), (5, 3, 3))

    def test_missing_one_overlap_label_preserves_group_but_reduces_rule_recall(self):
        self.response['reviews'][3]['findings'] = [f for f in self.response['reviews'][3]['findings'] if f['rule_id'] != 'RESIDUALS']
        metrics, _, _ = self.score()
        self.assertEqual((metrics['supported_true_positives'], metrics['false_positives'], metrics['false_negatives']), (7, 0, 1))
        self.assertEqual(metrics['supported_actionable_issue_groups'], 6)
        self.assertEqual(metrics['issue_groups_with_all_labels_supported'], 5)

    def test_additional_unexpected_pair_is_not_accepted_by_quote_match_alone(self):
        self.response['reviews'][0]['findings'].append({
            'rule_id': 'PURPOSE', 'clause_id': '1', 'quote': self.documents[0]['clauses']['1'],
            'reason': 'Counterexample with an unsupported policy interpretation.', 'proposed_action': 'ESCALATE_TO_COUNSEL'})
        metrics, _, _ = self.score()
        self.assertEqual((metrics['supported_true_positives'], metrics['false_positives'], metrics['false_negatives']), (8, 1, 0))
        self.assertEqual(metrics['unresolved_label_adjudications'], 1)

    def test_duplicate_pair_is_rejected_instead_of_inflating_counts(self):
        self.response['reviews'][1]['findings'].append(copy.deepcopy(self.response['reviews'][1]['findings'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate document-and-rule'):
            self.score()

    def test_missing_document_review_is_rejected(self):
        self.response['reviews'].pop()
        with self.assertRaisesRegex(ValueError, 'every source document'):
            self.score()

    def test_duplicate_review_cannot_replace_an_empty_findings_document(self):
        self.response['reviews'][0] = copy.deepcopy(self.response['reviews'][1])
        with self.assertRaisesRegex(ValueError, 'duplicate reviewed document'):
            self.score()

    def test_extra_schema_field_is_rejected(self):
        self.response['reviews'][1]['findings'][0]['auto_approve'] = True
        with self.assertRaisesRegex(ValueError, 'Invalid finding fields'):
            self.score()

    def test_no_predictions_has_undefined_precision_and_zero_recall(self):
        for review in self.response['reviews']:
            review['findings'] = []
        metrics, rows, _ = self.score()
        self.assertIsNone(metrics['adjudicated_precision'])
        self.assertEqual(metrics['adjudicated_recall'], 0.0)
        self.assertEqual(metrics['false_negatives'], 8)
        self.assertEqual(metrics['supported_actionable_issue_groups'], 0)
        self.assertEqual(rows, [])

    def test_grouping_cannot_suppress_specific_residuals_priority(self):
        group = next(g for g in self.key['issue_groups'] if g['document_id'] == 'A04')
        group['primary_rule_id'] = 'PURPOSE'
        with self.assertRaisesRegex(ValueError, 'specific RESIDUALS'):
            self.score()

    def test_reference_group_coverage_must_be_complete(self):
        self.key['issue_groups'].pop()
        with self.assertRaisesRegex(ValueError, 'cover every reference pair'):
            self.score()

    def test_reference_locator_must_exist_in_source(self):
        self.key['expected_clause_ids']['A02']['TERM'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'does not exist in source'):
            self.score()


if __name__ == '__main__':
    unittest.main()
