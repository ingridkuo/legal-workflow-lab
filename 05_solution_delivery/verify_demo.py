#!/usr/bin/env python3
"""Run the control tests and verify archived reports before recording demo facts."""
from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest

from migration_demo import normalize_source, read_json, validate_migration, write_reports
from test_migration import MigrationTests

HERE = Path(__file__).resolve().parent


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MigrationTests)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=1).run(suite)
    if not result.wasSuccessful():
        print(log.getvalue())
        return 1
    source = normalize_source(HERE / 'fixtures/source_contracts.xml', HERE / 'field_mapping.json')
    reports = {}
    with tempfile.TemporaryDirectory() as temp:
        out = Path(temp)
        for scenario in ('flawed', 'corrected'):
            target = read_json(HERE / f'fixtures/target_{scenario}.json')
            report = validate_migration(source, target, scenario)
            write_reports(report, out)
            reports[scenario] = report
        (out / 'normalized_source.json').write_text(json.dumps(source, indent=2) + '\n', encoding='utf-8')
        compared = []
        for file in sorted(out.iterdir()):
            if file.read_bytes() != (HERE / 'results' / file.name).read_bytes():
                raise SystemExit(f'Archived report differs: {file.name}')
            compared.append(file.name)
    facts = {
        'schema': 'MIGRATION-DEMO-FACTS-1.0',
        'data_classification': 'eight fictional contracts; seeded defects',
        'test_count': result.testsRun,
        'tests_passed': result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
        'failures': len(result.failures),
        'errors': len(result.errors),
        'archived_reports_match_fresh_run': True,
        'verified_report_files': compared,
        'scenarios': {
            name: {key: report[key] for key in (
                'source_records', 'destination_records', 'clean_records', 'held_records',
                'exception_groups', 'exception_count', 'exception_types',
                'source_identity_reconciled', 'counts_reconcile', 'release_status',
                'release_approved', 'source_known_value_usd', 'source_records_with_unknown_value'
            )}
            for name, report in reports.items()
        },
        'test_command': 'python3 test_migration.py',
        'reproduce_command': 'python3 migration_demo.py',
        'verification_command': 'python3 verify_demo.py',
        'release_decision': 'Metadata checks never authorize release. Record-owner signoff and platform checks remain required.'
    }
    (HERE / 'results/demo_facts.json').write_text(json.dumps(facts, indent=2) + '\n', encoding='utf-8')
    print(f"{facts['tests_passed']}/{facts['test_count']} tests pass; {len(compared)} archived reports match a fresh run.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
