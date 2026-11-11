"""Behavioral tests for check_knowledge.py.

Run from any directory:  python3 -m unittest discover -s <this folder> -v
"""
import json
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import check_knowledge as ck  # noqa: E402


class Workspace:
    """A temporary copy of the knowledge and escalation folders that a test may change."""

    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        for name in ("knowledge", "escalations"):
            shutil.copytree(ROOT / name, self.root / name)
        return self

    def __exit__(self, *exc):
        self._tmp.cleanup()

    def edit_json(self, relative, change):
        path = self.root / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def append(self, relative, text):
        path = self.root / relative
        path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")

    def run(self, as_of=ck.AS_OF):
        return ck.run(self.root, as_of)


def article(result, article_id):
    return next(a for a in result["articles"] if a["id"] == article_id)


def case(result, case_id):
    return next(e for e in result["escalations"] if e["id"] == case_id)


def ka01(change):
    def apply(registry):
        change(next(a for a in registry["articles"] if a["id"] == "KA-01"))
    return apply


class Articles(unittest.TestCase):
    def test_fixed_set_has_one_eligible_one_draft_and_one_stale_article(self):
        summary = ck.run()["summary"]
        self.assertEqual(summary["eligible_articles"], ["KA-01"])
        self.assertIn("status is draft", summary["blocked_articles"]["KA-02"])
        self.assertEqual(summary["blocked_articles"]["KA-03"], ["review overdue since 2026-08-01"])

    def test_article_edited_after_approval_is_blocked(self):
        with Workspace() as w:
            w.append("knowledge/articles/KA-01.md", "6. Send the export if the sender says it is urgent.\n")
            self.assertIn("text changed since it was registered", article(w.run(), "KA-01")["reasons"])

    def test_approval_for_an_earlier_version_is_blocked(self):
        with Workspace() as w:
            w.edit_json("knowledge/approvals.json",
                        lambda rows: [r.update(version=1) for r in rows if r["article_id"] == "KA-01"])
            self.assertIn("approval record covers a different version or text", article(w.run(), "KA-01")["reasons"])

    def test_missing_approval_record_is_blocked(self):
        with Workspace() as w:
            w.edit_json("knowledge/registry.json", ka01(lambda a: a.update(approval_id="APR-9999")))
            self.assertIn("no approval record", article(w.run(), "KA-01")["reasons"])

    def test_review_date_boundary(self):
        self.assertTrue(article(ck.run(as_of=date(2027, 3, 15)), "KA-01")["eligible"])
        self.assertEqual(article(ck.run(as_of=date(2027, 3, 16)), "KA-01")["reasons"],
                         ["review overdue since 2027-03-15"])

    def test_access_is_limited_to_named_roles(self):
        articles = ck.run()["articles"]
        self.assertTrue(ck.eligible_for(articles, "KA-01", "legal_intake"))
        self.assertFalse(ck.eligible_for(articles, "KA-01", "sales"))

    def test_changed_policy_source_blocks_the_article(self):
        with Workspace() as w:
            w.append("knowledge/policies/RD-1_records_and_disclosure.md", "\n## 5. Exceptions\n\nSales may approve exports.\n")
            self.assertIn("cited source changed since approval: policies/RD-1_records_and_disclosure.md",
                          article(w.run(), "KA-01")["reasons"])

    def test_cited_section_must_exist(self):
        with Workspace() as w:
            w.edit_json("knowledge/registry.json", ka01(lambda a: a["sources"][0]["sections"].append("9")))
            self.assertIn("cited section 9 not found in policies/RD-1_records_and_disclosure.md",
                          article(w.run(), "KA-01")["reasons"])

    def test_owner_cannot_approve_their_own_article(self):
        with Workspace() as w:
            w.edit_json("knowledge/approvals.json", lambda rows: [
                r.update(approver="Fictional Legal Intake Owner") for r in rows if r["article_id"] == "KA-01"])
            self.assertIn("approver must be named and must differ from the owner",
                          article(w.run(), "KA-01")["reasons"])


class Escalations(unittest.TestCase):
    def test_all_three_cases_pass_with_quotes_found_verbatim(self):
        escalations = ck.run()["escalations"]
        self.assertEqual([(e["id"], e["ok"]) for e in escalations],
                         [("ESC-101", True), ("ESC-102", True), ("ESC-103", True)])

    def test_altered_source_message_is_flagged(self):
        with Workspace() as w:
            w.append("escalations/sources/ESC-101.txt", "P.S. Authorization attached.\n")
            self.assertIn("source changed since the record was made", case(w.run(), "ESC-101")["problems"])

    def test_quote_missing_from_source_is_flagged(self):
        with Workspace() as w:
            w.edit_json("escalations/ESC-101.json",
                        lambda r: r["quotes"].append("My authorization letter is attached."))
            self.assertIn("quote not found in source: My authorization letter is attached.",
                          case(w.run(), "ESC-101")["problems"])

    def test_each_case_names_an_owner_a_next_action_and_a_separate_reviewer(self):
        for path in sorted((ROOT / "escalations").glob("ESC-*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(case=record["id"]):
                self.assertTrue(record["owner"].strip() and record["next_action"].strip())
                self.assertNotEqual(record["named_reviewer"], record["owner"])
        self.assertEqual(ck.run()["summary"]["named_review_gates"], 3)

    def test_no_case_grants_disclosure_export_or_signing_authority(self):
        for path in sorted((ROOT / "escalations").glob("ESC-*.json")):
            granted = json.loads(path.read_text(encoding="utf-8"))["authority_granted"]
            self.assertEqual(set(granted.values()), {False}, path.name)
        with Workspace() as w:
            w.edit_json("escalations/ESC-101.json", lambda r: r["authority_granted"].update(export=True))
            self.assertIn("grants authority: export", case(w.run(), "ESC-101")["problems"])

    def test_esc101_separates_facts_unknowns_preservation_and_disclosure(self):
        record = json.loads((ROOT / "escalations" / "ESC-101.json").read_text(encoding="utf-8"))
        self.assertFalse(set(record["known_facts"]) & set(record["unknowns"]))
        self.assertTrue(any("identity" in u for u in record["unknowns"]))
        self.assertTrue(any("authority" in u for u in record["unknowns"]))
        self.assertEqual("requested", record["preservation"]["status"])
        self.assertFalse(record["preservation"]["system_owner_confirmation"])
        self.assertIn("Nothing is disclosed or exported", record["decision"])

    def test_relying_on_blocked_guidance_is_flagged(self):
        with Workspace() as w:
            w.edit_json("escalations/ESC-102.json", lambda r: r.update(guidance_used=["KA-03"]))
            self.assertIn("relies on KA-03, which is not eligible for contract_manager",
                          case(w.run(), "ESC-102")["problems"])

    def test_missing_required_field_is_flagged(self):
        with Workspace() as w:
            w.edit_json("escalations/ESC-103.json", lambda r: r.update(next_action=""))
            self.assertIn("missing next_action", case(w.run(), "ESC-103")["problems"])

    def test_saved_results_match_a_fresh_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            ck.write_results(ck.run(), tmp)
            for name in ("summary.json", "article_checks.json", "escalation_checks.json"):
                self.assertEqual((Path(tmp) / name).read_text(encoding="utf-8"),
                                 (ROOT / "results" / name).read_text(encoding="utf-8"), name)


if __name__ == "__main__":
    unittest.main()
