"""Behavior tests for the local synthetic metadata reconciliation example."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from migration_demo import normalize_source, normalized_money, read_json, valid_date, validate_migration, write_reports

HERE = Path(__file__).resolve().parent


class MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = normalize_source(HERE / 'fixtures/source_contracts.xml', HERE / 'field_mapping.json')
        cls.corrected = read_json(HERE / 'fixtures/target_corrected.json')
        cls.flawed = read_json(HERE / 'fixtures/target_flawed.json')

    def report(self, rows):
        return validate_migration(self.source, rows, 'test')

    def codes(self, rows):
        return [issue['code'] for issue in self.report(rows)['exceptions']]

    def test_source_and_destination_counts(self):
        self.assertEqual((len(self.source), len(self.corrected), len(self.flawed)), (8, 8, 8))

    def test_xml_mapping_preserves_all_fields(self):
        self.assertEqual(self.source, self.corrected)
        self.assertEqual(self.source[2]['value_usd'], '48000.50')

    def test_exact_four_seeded_defects(self):
        self.assertCountEqual(self.codes(self.flawed), [
            'REQUIRED_METADATA', 'DUPLICATE_REPOSITORY_ID', 'INVALID_DATE', 'SOURCE_REVISION_MISMATCH'])

    def test_corrected_data_has_no_exceptions(self):
        report = self.report(self.corrected)
        self.assertEqual(report['exceptions'], [])
        self.assertTrue(report['validation_gate_passed'])
        self.assertEqual(report['release_status'], 'READY_FOR_OWNER_SIGNOFF')
        self.assertFalse(report['release_approved'])

    def test_missing_record_is_not_silently_accepted(self):
        self.assertIn('SOURCE_RECONCILIATION', self.codes(self.corrected[:-1]))

    def test_repeated_source_record_is_detected(self):
        self.assertIn('SOURCE_RECONCILIATION', self.codes(self.corrected + [self.corrected[0]]))

    def test_unknown_source_id_is_quarantined(self):
        rows = copy.deepcopy(self.corrected)
        rows[0]['source_record_id'] = 'UNKNOWN-001'
        self.assertIn('UNKNOWN_SOURCE_ID', self.codes(rows))
        self.assertIn('SOURCE_RECONCILIATION', self.codes(rows))

    def test_zero_value_is_retained(self):
        self.assertEqual(self.corrected[1]['value_usd'], '0.00')
        self.assertNotIn('INVALID_VALUE', self.codes(self.corrected))

    def test_blank_value_is_not_zero(self):
        rows = copy.deepcopy(self.corrected)
        rows[1]['value_usd'] = ''
        self.assertIn('INVALID_VALUE', self.codes(rows))

    def test_ambiguous_or_impossible_dates_are_rejected(self):
        for value in ['11/10/2026', '2027-02-30', '2026-1-1', '', None]:
            with self.subTest(value=value):
                self.assertFalse(valid_date(value))
        self.assertTrue(valid_date('2028-02-29'))

    def test_nonfinite_negative_and_subcent_values_rejected(self):
        for value in ['NaN', 'Infinity', '-1', '1.001']:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalized_money(value)

    def test_permissions_metadata_mismatch_is_visible(self):
        rows = copy.deepcopy(self.corrected)
        rows[0]['access_group'] = 'Everyone'
        self.assertIn('FIELD_MISMATCH', self.codes(rows))

    def test_identity_collision_does_not_delete_a_source(self):
        report = self.report(self.flawed)
        self.assertEqual(report['source_records'], report['destination_records'])
        self.assertEqual((report['clean_records'], report['held_records']), (3, 5))
        self.assertTrue(report['counts_reconcile'])
        duplicate = next(x for x in report['exceptions'] if x['code'] == 'DUPLICATE_REPOSITORY_ID')
        self.assertEqual(duplicate['source_record_id'], 'LEG-001, LEG-003')

    def test_case_insensitive_destination_collision_is_held(self):
        rows = copy.deepcopy(self.corrected)
        rows[2]['repository_record_id'] = ' rep-001 '
        report = self.report(rows)
        self.assertIn('DUPLICATE_REPOSITORY_ID', [i['code'] for i in report['exceptions']])
        self.assertEqual((report['clean_records'], report['held_records']), (6, 2))

    def test_unknown_amount_stays_null_and_zero_stays_known(self):
        self.assertIsNone(self.source[6]['value_usd'])
        self.assertIsNone(self.corrected[6]['value_usd'])
        self.assertEqual(self.source[1]['value_usd'], '0.00')
        self.assertEqual(self.report(self.corrected)['source_records_with_unknown_value'], 1)

    def test_unknown_source_amount_cannot_become_zero(self):
        rows = copy.deepcopy(self.corrected)
        rows[6]['value_usd'] = '0.00'
        self.assertIn('FIELD_MISMATCH', self.codes(rows))

    def test_independent_target_edit_is_detected(self):
        rows = copy.deepcopy(self.corrected)
        rows[0]['value_usd'] = '120001.00'
        rows[0]['counterparty'] = 'A different fictional company'
        self.assertEqual(sum(x == 'FIELD_MISMATCH' for x in self.codes(rows)), 2)

    def test_boolean_revision_cannot_masquerade_as_integer(self):
        rows = copy.deepcopy(self.corrected)
        rows[2]['source_revision'] = True
        self.assertIn('SOURCE_REVISION_MISMATCH', self.codes(rows))

    def test_source_reconciliation_fails_even_if_counts_match(self):
        rows = copy.deepcopy(self.corrected)
        rows[-1]['source_record_id'] = rows[0]['source_record_id']
        report = self.report(rows)
        self.assertEqual(report['source_records'], report['destination_records'])
        self.assertFalse(report['source_identity_reconciled'])
        self.assertFalse(report['counts_reconcile'])

    def assert_source_rejected(self, raw):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'source.xml'
            path.write_bytes(raw if isinstance(raw, bytes) else raw.encode('utf-8'))
            with self.assertRaises(ValueError):
                normalize_source(path, HERE / 'field_mapping.json')

    def test_dtd_and_entity_declarations_rejected_before_mapping(self):
        self.assert_source_rejected('<!DOCTYPE contracts [<!ENTITY x "payload">]><contracts fictional="true"/>')
        self.assert_source_rejected('<!DOCTYPE contracts SYSTEM "file:///etc/passwd"><contracts fictional="true"/>')

    def test_utf16_cannot_bypass_xml_preflight(self):
        self.assert_source_rejected('<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE contracts><contracts fictional="true"/>'.encode('utf-16'))

    def test_repeated_mapped_source_field_rejected(self):
        raw = (HERE / 'fixtures/source_contracts.xml').read_text()
        self.assert_source_rejected(raw.replace('<owner>Maya Chen</owner>', '<owner>Maya Chen</owner><owner>Other owner</owner>', 1))

    def test_unexpected_source_record_not_silently_ignored(self):
        raw = (HERE / 'fixtures/source_contracts.xml').read_text()
        self.assert_source_rejected(raw.replace('</contracts>', '<unmapped_contract id="LEG-009"/></contracts>'))

    def test_unapproved_source_access_group_is_rejected(self):
        raw = (HERE / 'fixtures/source_contracts.xml').read_text()
        self.assert_source_rejected(raw.replace('<visibility_group>Legal</visibility_group>', '<visibility_group>Everyone</visibility_group>', 1))

    def test_malformed_destination_identity_does_not_crash_checker(self):
        rows = copy.deepcopy(self.corrected)
        rows[0]['source_record_id'] = ['LEG-001']
        report = self.report(rows)
        self.assertFalse(report['validation_gate_passed'])
        self.assertEqual(report['held_records'], 1)

    def test_xml_serialization_roundtrip(self):
        tree = ET.parse(HERE / 'fixtures/source_contracts.xml')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'roundtrip.xml'
            tree.write(path, encoding='utf-8', xml_declaration=True)
            actual = normalize_source(path, HERE / 'field_mapping.json')
        self.assertEqual(actual, self.source)

    def test_json_serialization_roundtrip(self):
        self.assertEqual(json.loads(json.dumps(self.corrected)), self.corrected)

    def test_failed_gate_never_grants_release(self):
        report = self.report(self.flawed)
        self.assertFalse(report['validation_gate_passed'])
        self.assertFalse(report['release_approved'])
        self.assertEqual(report['release_status'], 'HOLD_FOR_CORRECTION')

    def test_repeatable_output(self):
        self.assertEqual(self.report(self.flawed), self.report(self.flawed))

    def test_reports_are_json_csv_and_markdown(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            report = self.report(self.flawed)
            write_reports(report, directory)
            self.assertEqual(read_json(directory / 'test_report.json'), report)
            csv_text = (directory / 'test_exceptions.csv').read_text()
            markdown = (directory / 'test_summary.md').read_text()
            self.assertEqual(csv_text.count('\n'), 5)
            self.assertIn('Exception groups: **4**', markdown)
            self.assertIn('HOLD_FOR_CORRECTION', markdown)


if __name__ == '__main__':
    unittest.main(verbosity=2)
