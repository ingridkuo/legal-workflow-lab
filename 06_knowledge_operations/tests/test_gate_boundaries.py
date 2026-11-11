"""Fail-closed behavior that separates local metadata checks from legal authority."""
import json
from pathlib import Path
import sys
import unittest
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from test_check_knowledge import Workspace, article, case, ka01
import check_knowledge as ck


class GateBoundaries(unittest.TestCase):
    def test_future_approval_cannot_authorize_current_use(self):
        with Workspace() as w:
            w.edit_json('knowledge/approvals.json', lambda rows: [
                a.update(approved_on='2026-11-11') for a in rows if a['article_id']=='KA-01'])
            self.assertIn('future review or approval', article(w.run(),'KA-01')['reasons'])

    def test_invalid_review_date_blocks_instead_of_crashing(self):
        with Workspace() as w:
            w.edit_json('knowledge/registry.json', ka01(lambda a:a.update(next_review_due='2026-02-30')))
            self.assertIn('invalid review date', article(w.run(),'KA-01')['reasons'])

    def test_article_path_cannot_escape_knowledge_folder(self):
        with Workspace() as w:
            w.edit_json('knowledge/registry.json', ka01(lambda a:a.update(path='../outside.md')))
            self.assertIn('article file missing or unsafe path', article(w.run(),'KA-01')['reasons'])

    def test_cited_policy_cannot_escape_knowledge_folder(self):
        with Workspace() as w:
            w.edit_json('knowledge/registry.json', ka01(lambda a:a['sources'][0].update(path='../outside.md')))
            self.assertTrue(any('unsafe path' in x for x in article(w.run(),'KA-01')['reasons']))

    def test_source_symlink_cannot_escape_collection(self):
        with Workspace() as w:
            outside = w.root/'outside.txt'; outside.write_text('Outside the source boundary.\n')
            target = w.root/'escalations/sources/ESC-101.txt'; target.unlink(); target.symlink_to(outside)
            self.assertIn('source file missing or unsafe path', case(w.run(),'ESC-101')['problems'])

    def test_mutating_registered_source_reference_requires_new_approval(self):
        with Workspace() as w:
            w.edit_json('knowledge/registry.json', ka01(lambda a:a['sources'][0]['sections'].append('1')))
            self.assertIn('approval record covers different source references', article(w.run(),'KA-01')['reasons'])

    def test_source_version_must_match_policy_text(self):
        with Workspace() as w:
            w.edit_json('knowledge/registry.json', ka01(lambda a:a['sources'][0].update(version=99)))
            self.assertIn('cited source version mismatch: policies/RD-1_records_and_disclosure.md',
                          article(w.run(),'KA-01')['reasons'])

    def test_missing_authority_field_cannot_default_to_safe(self):
        with Workspace() as w:
            w.edit_json('escalations/ESC-101.json',lambda r:r['authority_granted'].pop('export'))
            self.assertIn('authority schema incomplete or contains unknown permissions',
                          case(w.run(),'ESC-101')['problems'])

    def test_unknown_permission_cannot_bypass_authority_gate(self):
        with Workspace() as w:
            w.edit_json('escalations/ESC-101.json',lambda r:r['authority_granted'].update(delete=True))
            self.assertIn('grants authority: delete',case(w.run(),'ESC-101')['problems'])

    def test_new_fact_requires_its_own_source_quote(self):
        with Workspace() as w:
            w.edit_json('escalations/ESC-101.json',lambda r:r['known_facts'].append('The sender has authority.'))
            self.assertIn('fact lacks one exact registered source quote: The sender has authority.',
                          case(w.run(),'ESC-101')['problems'])

    def test_preservation_completion_needs_acknowledgment(self):
        with Workspace() as w:
            w.edit_json('escalations/ESC-101.json',lambda r:r['preservation'].update(status='confirmed'))
            self.assertIn('preservation completion lacks system-owner confirmation',
                          case(w.run(),'ESC-101')['problems'])


if __name__=='__main__': unittest.main()
