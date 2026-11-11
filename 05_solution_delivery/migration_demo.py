#!/usr/bin/env python3
"""Compare fictional XML source metadata with a local JSON destination export."""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
AS_OF = "2026-11-10"
SCHEMA = "CONTRACT-MIGRATION-DEMO-1.1"
APPROVED_ACCESS_GROUPS = ("Legal", "Legal-Finance", "Restricted")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def valid_date(value) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def normalized_money(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d+(?:\.\d{1,2})?", value):
        raise ValueError("USD value must be a nonnegative plain decimal with at most two places")
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid source USD value") from exc
    if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
        raise ValueError("USD value must be nonnegative with at most two decimal places")
    # String formatting avoids binary float and Decimal context rounding for large values.
    whole, _, fraction = value.partition(".")
    return f"{int(whole)}.{fraction.ljust(2, '0')}"


def normalize_source(xml_path: Path, mapping_path: Path) -> list[dict]:
    mapping = read_json(mapping_path)
    # This fixture's export contract is UTF-8 XML. Decode before scanning so UTF-16
    # cannot conceal a DTD/entity declaration behind interleaved zero bytes.
    try:
        raw = xml_path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Expected UTF-8 XML") from exc
    if "\x00" in raw or re.search(r"<!\s*(?:DOCTYPE|ENTITY)", raw, re.IGNORECASE):
        raise ValueError("DTD/entity declarations and non-UTF-8 XML are not accepted")
    encoding = re.search(r"<\?xml[^>]*encoding\s*=\s*['\"]([^'\"]+)", raw, re.IGNORECASE)
    if encoding and encoding.group(1).lower() not in ("utf-8", "utf8"):
        raise ValueError("Expected UTF-8 XML")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError("Source XML is not well-formed") from exc
    if root.tag != "contracts" or root.get("fictional") != "true":
        raise ValueError("Expected the fictional contracts export")
    if any(child.tag != "contract" for child in root):
        raise ValueError("Unexpected source record element")
    rows = []
    for index, node in enumerate(root.findall("contract"), start=1):
        allowed = [f["xml_source"] for f in mapping["fields"] if not f["xml_source"].startswith("@")]
        tags = [child.tag for child in node]
        if (any(tag not in allowed for tag in tags) or len(tags) != len(set(tags))
                or any(list(child) for child in node)):
            raise ValueError("Unexpected or repeated mapped source field")
        row = {"repository_record_id": f"REP-{index:03d}"}
        for field in mapping["fields"]:
            source = field["xml_source"]
            raw = node.get(source[1:]) if source.startswith("@") else node.findtext(source)
            if raw is None or not raw.strip():
                if field.get("nullable"):
                    row[field["target_field"]] = None
                    continue
                raise ValueError(f"Required source field missing: {source}")
            raw = raw.strip()
            if field["transform"] == "integer":
                if not re.fullmatch(r"[1-9]\d*", raw):
                    raise ValueError("Source revision must be a positive integer")
                value = int(raw)
            elif field["transform"] == "usd_decimal_string":
                value = normalized_money(raw)
            elif field["transform"] == "iso_date":
                if not valid_date(raw):
                    raise ValueError("Source has an invalid ISO date")
                value = raw
            elif field["transform"] == "text":
                value = raw
            else:
                raise ValueError(f"Unsupported mapping transform: {field['transform']}")
            row[field["target_field"]] = value
        if date.fromisoformat(row["signed_date"]) > date.fromisoformat(row["expiry_date"]):
            raise ValueError("Source expiry precedes signature")
        if row["access_group"] not in mapping["approved_access_groups"]:
            raise ValueError("Source access group is not approved")
        rows.append(row)
    source_ids = [row["source_record_id"] for row in rows]
    if not rows:
        raise ValueError("Source export contains no contracts")
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Source export has duplicate source IDs")
    return rows


def validate_migration(source: list[dict], target: list[dict], scenario: str) -> dict:
    if not isinstance(target, list) or any(not isinstance(row, dict) for row in target):
        raise ValueError("Destination must be a JSON array of records")
    expected = {row["source_record_id"]: row for row in source}
    issues = []

    def issue(code, source_id, field, expected_value, actual_value, action):
        issues.append({"issue_id": f"EX-{len(issues)+1:03d}", "code": code,
                       "source_record_id": source_id, "field": field,
                       "expected": expected_value, "actual": actual_value,
                       "owner": "Legal operations / data steward", "action": action})

    target_ids = [r.get("repository_record_id").strip().casefold()
                  if isinstance(r.get("repository_record_id"), str) else None for r in target]
    for repo_id, count in sorted(Counter(v for v in target_ids if isinstance(v, str) and v.strip()).items()):
        if count > 1:
            affected = sorted(str(r.get("source_record_id")) for r in target
                              if isinstance(r.get("repository_record_id"), str)
                              and r["repository_record_id"].strip().casefold() == repo_id)
            issue("DUPLICATE_REPOSITORY_ID", ", ".join(affected), "repository_record_id",
                  "unique destination identifier", repo_id,
                  "Resolve the collision against the source-to-destination crosswalk; retain both source records.")
    source_counts = Counter(r.get("source_record_id") for r in target if isinstance(r.get("source_record_id"), str))
    for sid in sorted(expected):
        count = source_counts.get(sid, 0)
        if count != 1:
            issue("SOURCE_RECONCILIATION", sid, "source_record_id", 1, count,
                  "Reconcile missing or repeated source records before release.")
    text_fields = ["repository_record_id", "source_record_id", "contract_number", "counterparty",
                   "agreement_type", "business_owner", "access_group"]
    compared_fields = ["contract_number", "counterparty", "agreement_type", "business_owner", "access_group"]
    for row_index, row in enumerate(target, start=1):
        sid = row.get("source_record_id")
        label = sid if isinstance(sid, str) and sid else f"destination row {row_index}"
        missing = {field for field in text_fields if not isinstance(row.get(field), str) or not row[field].strip()}
        for field in sorted(missing):
            issue("REQUIRED_METADATA", label, field, "nonempty text", row.get(field),
                  "Obtain the value from the source and record owner; do not fill it by guesswork.")
        if not isinstance(sid, str) or sid not in expected:
            if isinstance(sid, str) and sid:
                issue("UNKNOWN_SOURCE_ID", label, "source_record_id", "ID in source export", sid,
                      "Identify the source record or quarantine this destination record.")
            continue
        original = expected[sid]
        revision = row.get("source_revision")
        if type(revision) is not int or revision != original["source_revision"]:
            issue("SOURCE_REVISION_MISMATCH", sid, "source_revision", original["source_revision"], revision,
                  "Replace the stale destination revision after verifying the source version.")
        for field in compared_fields:
            if field not in missing and row[field] != original[field]:
                issue("FIELD_MISMATCH", sid, field, original[field], row[field],
                      "Reconcile the mapped value to the source export and retain the decision.")
        if "access_group" not in missing and row["access_group"] not in APPROVED_ACCESS_GROUPS:
            issue("UNAPPROVED_ACCESS_GROUP", sid, "access_group", list(APPROVED_ACCESS_GROUPS), row["access_group"],
                  "Quarantine the record; obtain an approved group from the system owner.")
        valid_dates = {}
        for field in ["signed_date", "expiry_date"]:
            value = row.get(field)
            valid_dates[field] = valid_date(value)
            if not valid_dates[field]:
                issue("INVALID_DATE", sid, field, "valid YYYY-MM-DD date", value,
                      "Verify the source date; reject impossible or ambiguous date values.")
            elif value != original[field]:
                issue("FIELD_MISMATCH", sid, field, original[field], value,
                      "Resolve the date difference against the source before release.")
        if all(valid_dates.values()) and row["signed_date"] > row["expiry_date"]:
            issue("DATE_ORDER", sid, "expiry_date", "not earlier than signature", row["expiry_date"],
                  "Verify the contractual date fields and the mapping.")
        money = row.get("value_usd")
        if original["value_usd"] is None:
            if "value_usd" not in row or money is not None:
                issue("FIELD_MISMATCH", sid, "value_usd", None,
                      money if "value_usd" in row else "<missing field>",
                      "Preserve the unknown source amount as null; do not replace it with zero or a blank string.")
            continue
        try:
            normalized = normalized_money(money) if isinstance(money, str) else None
        except ValueError:
            normalized = None
        if normalized is None:
            issue("INVALID_VALUE", sid, "value_usd", "nonnegative decimal string", money,
                  "Resolve the value and currency from the source; do not convert missing amounts to zero.")
        elif normalized != original["value_usd"]:
            issue("FIELD_MISMATCH", sid, "value_usd", original["value_usd"], money,
                  "Reconcile the contract value against the source export.")
    gate = not issues
    affected = {sid for item in issues for sid in str(item["source_record_id"]).split(", ")}
    held = sum(1 for index, row in enumerate(target, start=1)
               if (row.get("source_record_id") if isinstance(row.get("source_record_id"), str)
                   and row["source_record_id"] else f"destination row {index}") in affected)
    identity_reconciled = (set(source_counts) == set(expected)
                           and all(source_counts.get(sid) == 1 for sid in expected)
                           and len(source) == len(target))
    known = [Decimal(row["value_usd"]) for row in source if row["value_usd"] is not None]
    with localcontext() as ctx:
        ctx.prec = max((len(value.as_tuple().digits) for value in known), default=1) + len(str(len(known))) + 2
        known_total = format(sum(known, Decimal("0")), ".2f")
    return {"schema": SCHEMA, "scenario": scenario, "as_of_date": AS_OF,
            "data_classification": "synthetic demonstration", "source_records": len(source),
            "destination_records": len(target), "exception_groups": len({item['code'] for item in issues}),
            "exception_count": len(issues), "exception_types": sorted({item['code'] for item in issues}),
            "clean_records": len(target) - held, "held_records": held,
            "source_identity_reconciled": identity_reconciled,
            "counts_reconcile": identity_reconciled and len(target) == held + (len(target) - held),
            "source_known_value_usd": known_total,
            "source_records_with_unknown_value": sum(row["value_usd"] is None for row in source),
            "validation_gate_passed": gate,
            "release_status": "READY_FOR_OWNER_SIGNOFF" if gate else "HOLD_FOR_CORRECTION",
            "release_approved": False, "exceptions": issues}


def write_reports(report: dict, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    stem = report["scenario"]
    (destination / f"{stem}_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    columns = ["issue_id", "code", "source_record_id", "field", "expected", "actual", "owner", "action"]
    with (destination / f"{stem}_exceptions.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for issue in report["exceptions"]:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in issue.items()})
    lines = ["# Contract metadata migration check", "", "Synthetic demonstration", "",
             f"Scenario: **{stem}**. Source: **{report['source_records']} records**. Destination: **{report['destination_records']} records**.",
             f"Clean: **{report['clean_records']}**. Held: **{report['held_records']}**. Source identities reconcile: **{report['source_identity_reconciled']}**.",
             f"Exception groups: **{report['exception_groups']}**. Release status: **{report['release_status']}**.",
             "", "Validation does not authorize release. The record owner decides after resolving exceptions and checking documents and permissions.", "",
             "| Issue | Source record | Field | Action |", "|---|---|---|---|"]
    for issue in report["exceptions"]:
        lines.append(f"| {issue['code']} | {issue['source_record_id']} | {issue['field']} | {issue['action']} |")
    if not report["exceptions"]:
        lines.append("| None detected | All eight records | In-scope metadata | Obtain owner signoff. |")
    (destination / f"{stem}_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=["flawed", "corrected", "both"], default="both")
    parser.add_argument("--output", type=Path, default=BASE / "results")
    args = parser.parse_args()
    source = normalize_source(BASE / "fixtures/source_contracts.xml", BASE / "field_mapping.json")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "normalized_source.json").write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
    scenarios = ["flawed", "corrected"] if args.case == "both" else [args.case]
    for scenario in scenarios:
        target = read_json(BASE / f"fixtures/target_{scenario}.json")
        report = validate_migration(source, target, scenario)
        write_reports(report, args.output)
        print(f"{scenario}: {report['exception_groups']} exception groups; {report['release_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
