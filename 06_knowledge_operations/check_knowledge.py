#!/usr/bin/env python3
"""Inspect local synthetic knowledge and escalation records; never execute actions.

Python 3.10+, standard library only. Runs from any working directory.
    python3 check_knowledge.py
    python3 check_knowledge.py --as-of 2027-03-16
Default run rewrites results/. An alternate date only prints results.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
AS_OF = date(2026, 11, 10)
REQUIRED = ("id", "received", "channel", "source", "quotes", "known_facts", "fact_support",
            "unknowns", "owner", "owner_role", "next_action", "named_reviewer", "decision")
AUTHORITY_KEYS = {"disclosure", "export", "approval_to_sign"}
NOTE = ("Synthetic records and simulated approvals. Checks verify recorded evidence, not legal "
        "correctness or real identity. No disclosure, export, signing or preservation action is executed.")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def local_file(root, relative):
    """Reject absolute paths, traversal and symlinks that leave the trusted folder."""
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("invalid local reference")
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("reference leaves its folder")
    return path


def safe_file(root, relative):
    try:
        path = local_file(root, relative)
        return path if path.is_file() else None
    except (ValueError, OSError):
        return None


def parse_date(value):
    if not isinstance(value, str):
        raise ValueError("date must be an ISO string")
    return date.fromisoformat(value)


def check_articles(knowledge_dir, as_of=AS_OF):
    """Return eligibility and specific reasons. Trusted catalog/approval fixtures are inputs."""
    knowledge = Path(knowledge_dir)
    approval_rows = load_json(knowledge / "approvals.json")
    approvals = {a["approval_id"]: a for a in approval_rows}
    duplicate_approvals = {a["approval_id"] for a in approval_rows
                           if sum(x["approval_id"] == a["approval_id"] for x in approval_rows) != 1}
    results = []
    for entry in load_json(knowledge / "registry.json")["articles"]:
        reasons = []
        article = safe_file(knowledge, entry.get("path"))
        if article is None:
            reasons.append("article file missing or unsafe path")
        elif sha256(article) != entry.get("sha256"):
            reasons.append("text changed since it was registered")
        if entry.get("status") != "approved":
            reasons.append(f"status is {entry.get('status') or 'missing'}")
        owner = (entry.get("owner") or "").strip()
        if not owner:
            reasons.append("no named owner")
        approval_id = entry.get("approval_id") or ""
        approval = approvals.get(approval_id)
        if approval_id in duplicate_approvals:
            reasons.append("approval id is not unique")
        if approval is None:
            reasons.append("no approval record")
        else:
            if (approval.get("article_id"), approval.get("version"), approval.get("article_sha256")) != \
                    (entry.get("id"), entry.get("version"), entry.get("sha256")):
                reasons.append("approval record covers a different version or text")
            if approval.get("source_snapshots") != entry.get("sources"):
                reasons.append("approval record covers different source references")
            approver = (approval.get("approver") or "").strip()
            if not approver or approver.casefold() == owner.casefold():
                reasons.append("approver must be named and must differ from the owner")
        due = None
        if not entry.get("next_review_due"):
            reasons.append("no review date")
        else:
            try:
                due = parse_date(entry["next_review_due"])
                if due < as_of:
                    reasons.append(f"review overdue since {entry['next_review_due']}")
            except ValueError:
                reasons.append("invalid review date")
        try:
            reviewed = parse_date(entry.get("reviewed_on"))
            approved = parse_date((approval or {}).get("approved_on"))
            if reviewed > as_of or approved > as_of:
                reasons.append("future review or approval")
            if reviewed > approved or (due is not None and approved > due):
                reasons.append("invalid review and approval window")
        except ValueError:
            reasons.append("missing or invalid review/approval date")
        if not entry.get("sources"):
            reasons.append("no cited source")
        for source in entry.get("sources", []):
            policy = safe_file(knowledge, source.get("path"))
            if policy is None:
                reasons.append(f"cited source missing or unsafe path: {source.get('path')}")
                continue
            if sha256(policy) != source.get("sha256"):
                reasons.append(f"cited source changed since approval: {source['path']}")
            text = policy.read_text(encoding="utf-8")
            if not source.get("version") or not re.search(
                    rf"\bVersion {re.escape(str(source['version']))}\.", text):
                reasons.append(f"cited source version mismatch: {source['path']}")
            if not source.get("sections"):
                reasons.append(f"no cited sections: {source['path']}")
            for section in source.get("sections", []):
                if not re.search(rf"^## {re.escape(str(section))}\. ", text, re.MULTILINE):
                    reasons.append(f"cited section {section} not found in {source['path']}")
        roles = entry.get("access_roles")
        if not isinstance(roles, list) or not roles or any(not isinstance(x, str) or not x.strip() for x in roles):
            reasons.append("no valid access roles")
        results.append({"id": entry["id"], "title": entry["title"], "version": entry["version"],
                        "status": entry.get("status"), "eligible": not reasons,
                        "access_roles": roles if isinstance(roles, list) else [], "reasons": reasons})
    return results


def eligible_for(article_results, article_id, role):
    return any(r["id"] == article_id and r["eligible"] and role in r["access_roles"] for r in article_results)


def check_escalations(escalations_dir, article_results):
    """Check packet integrity, source quotation and guidance; never grant authority."""
    folder = Path(escalations_dir)
    results = []
    for path in sorted(folder.glob("ESC-*.json")):
        record = load_json(path)
        problems = [f"missing {field}" for field in REQUIRED if not record.get(field)]
        source = record.get("source") or {}
        message = safe_file(folder, source.get("path"))
        text = ""
        if message is None:
            problems.append("source file missing or unsafe path")
        else:
            if sha256(message) != source.get("sha256"):
                problems.append("source changed since the record was made")
            text = message.read_text(encoding="utf-8")
            for quote in record.get("quotes", []):
                if not isinstance(quote, str) or not quote or quote not in text:
                    problems.append(f"quote not found in source: {quote}")
        supports = record.get("fact_support", [])
        for fact in record.get("known_facts", []):
            matches = [s for s in supports if s.get("fact") == fact]
            if len(matches) != 1 or not matches[0].get("quote") or matches[0]["quote"] not in text \
                    or matches[0]["quote"] not in record.get("quotes", []):
                problems.append(f"fact lacks one exact registered source quote: {fact}")
        owner = (record.get("owner") or "").strip()
        reviewer = (record.get("named_reviewer") or "").strip()
        distinct_reviewer = bool(owner and reviewer and reviewer.casefold() != owner.casefold())
        if not distinct_reviewer:
            problems.append("the named reviewer must differ from the owner")
        authority = record.get("authority_granted")
        if not isinstance(authority, dict) or set(authority) != AUTHORITY_KEYS:
            problems.append("authority schema incomplete or contains unknown permissions")
        if isinstance(authority, dict):
            granted = sorted(k for k, v in authority.items() if v is not False)
            if granted:
                problems.append("grants authority: " + ", ".join(granted))
        if set(record.get("known_facts", [])) & set(record.get("unknowns", [])):
            problems.append("a statement is listed as both known and unknown")
        for article_id in record.get("guidance_used", []):
            if not eligible_for(article_results, article_id, record.get("owner_role")):
                problems.append(f"relies on {article_id}, which is not eligible for {record.get('owner_role')}")
        preservation = record.get("preservation")
        if preservation:
            if preservation.get("status") == "confirmed" and preservation.get("system_owner_confirmation") is not True:
                problems.append("preservation completion lacks system-owner confirmation")
            if preservation.get("legal_duty_determined") is not False:
                problems.append("intake must not determine the legal preservation duty")
        results.append({"id": record.get("id") or path.stem, "ok": not problems,
                        "named_review_gate": distinct_reviewer,
                        "guidance_used": record.get("guidance_used", []), "problems": problems,
                        "preservation_status": (preservation or {}).get("status"),
                        "action_authorized": False})
    return results


def run(root=HERE, as_of=AS_OF):
    articles = check_articles(Path(root) / "knowledge", as_of)
    escalations = check_escalations(Path(root) / "escalations", articles)
    summary = {"as_of": as_of.isoformat(), "articles_checked": len(articles),
               "eligible_articles": [a["id"] for a in articles if a["eligible"]],
               "blocked_articles": {a["id"]: a["reasons"] for a in articles if not a["eligible"]},
               "escalations_checked": len(escalations),
               "escalations_passing": sum(e["ok"] for e in escalations),
               "named_review_gates": sum(e["named_review_gate"] for e in escalations), "note": NOTE}
    return {"summary": summary, "articles": articles, "escalations": escalations}


def write_results(result, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, key in (("summary.json", "summary"), ("article_checks.json", "articles"),
                      ("escalation_checks.json", "escalations")):
        (out / name).write_text(json.dumps(result[key], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv):
    try:
        if len(argv) == 1:
            as_of = AS_OF
        elif len(argv) == 3 and argv[1] == "--as-of":
            as_of = parse_date(argv[2])
        else:
            raise ValueError("expected --as-of YYYY-MM-DD")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    result = run(HERE, as_of)
    if as_of == AS_OF:
        write_results(result, HERE / "results")
    s = result["summary"]
    print(f"as of {s['as_of']}: eligible articles {', '.join(s['eligible_articles']) or 'none'}")
    for article_id, reasons in s["blocked_articles"].items():
        print(f"  blocked {article_id}: {'; '.join(reasons)}")
    print(f"escalations: {s['escalations_passing']} of {s['escalations_checked']} pass; "
          f"{s['named_review_gates']} keep a named review gate")
    return 0 if s["escalations_passing"] == s["escalations_checked"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
