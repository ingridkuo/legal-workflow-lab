#!/usr/bin/env python3
"""Build the contract operations sample database and six query exports."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys


HERE = Path(__file__).resolve().parent
CONTRACT_COLUMNS = [
    "contract_id", "contract_type", "counterparty", "business_owner", "value_usd",
    "risk_trigger", "stage", "next_action", "approval_due", "target_signature",
    "actual_signature", "renewal_date", "notice_days", "notice_basis",
    "notice_method", "notice_source_verified", "coi_required", "coi_expiry",
    "coi_evidence", "entity_verified", "signature_authority", "template_unchanged",
    "personal_data", "controlled_technology", "other_red_flag", "reviewer_check",
    "source_locator", "review_notes", "expected_rag",
]
OBLIGATION_COLUMNS = [
    "obligation_id", "contract_id", "milestone", "description", "owner",
    "planned_date", "actual_date", "budget_usd", "committed_usd", "actual_cost_usd",
    "invoice_number", "invoiced_usd", "paid_usd", "acceptance_required",
    "acceptance_evidence", "reviewer_check", "source_locator",
]
CALENDAR_COLUMNS = [
    "compliance_id", "entity", "jurisdiction", "obligation", "owner", "planned_due",
    "completed_date", "source", "reviewer_check",
]
MONEY_FIELDS = {
    "value_usd", "budget_usd", "committed_usd", "actual_cost_usd",
    "invoiced_usd", "paid_usd",
}
DATE_FIELDS = {
    "approval_due", "target_signature", "actual_signature", "renewal_date",
    "coi_expiry", "planned_date", "actual_date", "planned_due", "completed_date",
}
NULL_CSV = "\\N"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_source(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    data = json.loads(raw)
    required = {"metadata", "contracts", "obligations", "compliance_calendar"}
    if set(data) != required:
        raise ValueError(f"Source top-level keys must be {sorted(required)}")
    meta = data["metadata"]
    if meta.get("fictional") is not True:
        raise ValueError("This public demo builder accepts only explicitly fictional datasets.")
    if meta.get("currency") != "USD":
        raise ValueError("The demonstration uses USD only; no exchange rate is inferred.")
    for section in ("contracts", "obligations", "compliance_calendar"):
        if not isinstance(data[section], list):
            raise ValueError(f"{section} must be a list")
        for row in data[section]:
            for key, value in row.items():
                if key in DATE_FIELDS and value is not None:
                    if not isinstance(value, str) or dt.date.fromisoformat(value).isoformat() != value:
                        raise ValueError(f"Invalid ISO date in {section}.{key}: {value!r}")
                if key in MONEY_FIELDS and value is not None:
                    if isinstance(value, bool) or not isinstance(value, (int, float)):
                        raise ValueError(f"Money must be a JSON number or null, not {value!r}")
    return data, sha256_bytes(raw)


def insert_rows(connection: sqlite3.Connection, table: str, columns: list[str], rows: list[dict]) -> None:
    # Names come only from the fixed schema mapping above, never arbitrary JSON.
    placeholders = ",".join("?" for _ in columns)
    sql = f'INSERT INTO "{table}" ({",".join(columns)}) VALUES ({placeholders})'
    prepared = []
    for row in rows:
        mapped = dict(row)
        if table == "contracts":
            mapped["contract_type"] = mapped.pop("type")
        if set(mapped) != set(columns):
            raise ValueError(f"Unexpected or missing columns for {table}: {set(mapped) ^ set(columns)}")
        prepared.append(tuple(mapped[column] for column in columns))
    connection.executemany(sql, prepared)


def named_queries(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^-- name: ([A-Za-z0-9_]+)\s*$", text)
    queries = []
    for index in range(1, len(blocks), 2):
        name, statement = blocks[index], blocks[index + 1].strip()
        if not statement or not re.match(r"^(SELECT|WITH)\b", statement, re.IGNORECASE):
            raise ValueError(f"Named query {name} is not a read-only SELECT/WITH statement")
        queries.append((name, statement))
    if len(queries) != 6 or len({name for name, _ in queries}) != 6:
        raise ValueError("Exactly six uniquely named queries are required")
    return queries


def run_queries(connection: sqlite3.Connection, output: Path, queries: list[tuple[str, str]]) -> dict:
    results = {}
    for name, sql in queries:
        cursor = connection.execute(sql)
        columns = [column[0] for column in cursor.description]
        records = [dict(row) for row in cursor.fetchall()]
        target = output / f"{name}.csv"
        with target.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(columns)
            for row in records:
                writer.writerow([NULL_CSV if row[column] is None else row[column] for column in columns])
        results[name] = {"columns": columns, "rows": records, "export": target.name}
    return results


def verify(connection: sqlite3.Connection, data: dict, results: dict, frozen_checks: bool, as_of: str) -> dict:
    checks = []

    def check(name: str, condition: bool, actual, expected) -> None:
        checks.append({"name": name, "passed": bool(condition), "actual": actual, "expected": expected})

    counts = {
        table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        for table in ("contracts", "obligations", "compliance_calendar")
    }
    for table in counts:
        check(f"source_row_count_{table}", counts[table] == len(data[table]), counts[table], len(data[table]))
    fk = [tuple(row) for row in connection.execute("PRAGMA foreign_key_check")]
    check("foreign_key_integrity", not fk, fk, [])
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    check("sqlite_integrity", integrity == "ok", integrity, "ok")

    # Verify the exact imported values, including None versus empty string.
    for table, cols, key in [
        ("contracts", CONTRACT_COLUMNS, "contract_id"),
        ("obligations", OBLIGATION_COLUMNS, "obligation_id"),
        ("compliance_calendar", CALENDAR_COLUMNS, "compliance_id"),
    ]:
        actual_rows = {row[key]: dict(row) for row in connection.execute(f"SELECT * FROM {table}")}
        expected_rows = {}
        for raw in data[table]:
            mapped = dict(raw)
            if table == "contracts":
                mapped["contract_type"] = mapped.pop("type")
            expected_rows[mapped[key]] = mapped
        check(f"exact_source_values_{table}", actual_rows == expected_rows,
              "all source values preserved" if actual_rows == expected_rows else "mismatch", "all source values preserved")

    computed_counts = dict(connection.execute("SELECT computed_rag, count(*) FROM v_contract_risk GROUP BY computed_rag"))
    mismatches = [dict(row) for row in connection.execute(
        "SELECT contract_id, computed_rag, expected_rag FROM v_contract_risk WHERE computed_rag <> expected_rag"
    )]
    check("computed_rag_matches_reference_labels", not mismatches, mismatches, [])
    values = dict(connection.execute(
        "SELECT sum(value_usd) AS known_sum_usd, count(value_usd) AS known_values, "
        "sum(CASE WHEN value_usd IS NULL THEN 1 ELSE 0 END) AS missing_values FROM contracts"
    ).fetchone())
    known_amounts = [row["value_usd"] for row in data["contracts"] if row["value_usd"] is not None]
    expected_known_sum = sum(known_amounts) if known_amounts else None
    check("known_value_sum_matches_source", values["known_sum_usd"] == expected_known_sum,
          values["known_sum_usd"], expected_known_sum)

    if frozen_checks:
        for table, expected in [("contracts",24),("obligations",48),("compliance_calendar",12)]:
            check(f"frozen_fixture_count_{table}", counts[table] == expected, counts[table], expected)
        expected_counts = {"GREEN":6,"YELLOW":10,"RED":7,"NEEDS INPUT":1}
        check("frozen_fixture_rag_counts", computed_counts == expected_counts, computed_counts, expected_counts)
        check("frozen_fixture_known_sum", values["known_sum_usd"] == 2141498, values["known_sum_usd"], 2141498)
        check("frozen_fixture_missing_value_count", values["missing_values"] == 1, values["missing_values"], 1)
        for contract_id, expected_rag in [("C003","GREEN"),("C004","YELLOW"),("C005","YELLOW"),("C006","RED"),("C023","NEEDS INPUT")]:
            actual = connection.execute("SELECT computed_rag FROM v_contract_risk WHERE contract_id = ?",(contract_id,)).fetchone()[0]
            check(f"risk_boundary_{contract_id}", actual == expected_rag, actual, expected_rag)
        null_rows = connection.execute(
            "SELECT count(*) FROM obligations WHERE contract_id='C023' AND budget_usd IS NULL "
            "AND committed_usd IS NULL AND actual_cost_usd IS NULL AND invoiced_usd IS NULL AND paid_usd IS NULL"
        ).fetchone()[0]
        check("null_money_preserved_for_C023_obligations", null_rows == 2, null_rows, 2)
        null_sum = connection.execute("SELECT sum(value_usd) FROM contracts WHERE contract_id='C023'").fetchone()[0]
        check("all_null_sum_remains_null", null_sum is None, null_sum, None)
        unknown_results = [row for row in results["q06_budget_invoice_exceptions"]["rows"] if row["contract_id"] == "C023"]
        check("null_financial_inputs_require_review", len(unknown_results) == 2 and all(
            row["financial_status"] == "NEEDS INPUT"
            and row["actual_over_budget_usd"] is None
            and row["invoiced_less_paid_usd"] is None for row in unknown_results
        ), [{k: r[k] for k in ("obligation_id","financial_status","actual_over_budget_usd","invoiced_less_paid_usd")} for r in unknown_results],
            "two C023 rows needing input with null calculations")
        for contract_id in ("C004","C009","C013","C015","C019"):
            row = dict(connection.execute("SELECT * FROM v_notice_review WHERE contract_id=?",(contract_id,)).fetchone())
            check(f"manual_notice_gate_{contract_id}", row["calculated_notice_date"] is None and row["notice_gate"].startswith("MANUAL REVIEW"),
                  {"calculated_notice_date":row["calculated_notice_date"],"notice_gate":row["notice_gate"]}, "NULL and manual review")
        deadline = connection.execute("SELECT calculated_notice_date FROM v_notice_review WHERE contract_id='C001'").fetchone()[0]
        check("calendar_notice_subtraction", deadline == "2026-11-10", deadline, "2026-11-10")
        if as_of == "2026-11-10":
            expiring = {row["contract_id"] for row in results["q01_expiring_within_90_days"]["rows"]}
            check("expiry_includes_today", "C007" in expiring, "C007" in expiring, True)
            check("expiry_includes_day_90", "C005" in expiring, "C005" in expiring, True)
            check("expiry_excludes_past_and_day_111", "C018" not in expiring and "C006" not in expiring,
                  {"past_included":"C018" in expiring,"beyond90_included":"C006" in expiring}, {"past_included":False,"beyond90_included":False})
            coi = {row["contract_id"] for row in results["q03_coi_missing_or_expired"]["rows"]}
            check("coi_missing_and_unverified_are_flagged", {"C007","C014"}.issubset(coi), sorted(coi), "includes C007 missing and C014 unverified")
            check("coi_expired_dates_are_flagged", {"C009","C023"}.issubset(coi), sorted(coi), "includes C009 and C023")
            check("coi_expiry_today_not_mislabeled_expired", "C003" not in coi, "C003" in coi, False)

        # Actual transaction-scoped edge checks; roll back so delivered rows stay exact.
        connection.execute("SAVEPOINT null_gate_check")
        try:
            connection.execute("UPDATE contracts SET controlled_technology=NULL WHERE contract_id='C001'")
            missing_control = connection.execute("SELECT computed_rag FROM v_contract_risk WHERE contract_id='C001'").fetchone()[0]
            check("missing_control_answer_not_green", missing_control == "NEEDS INPUT", missing_control, "NEEDS INPUT")
            connection.execute("UPDATE contracts SET controlled_technology='Yes' WHERE contract_id='C023'")
            risk_over_unknown_value = connection.execute("SELECT computed_rag FROM v_contract_risk WHERE contract_id='C023'").fetchone()[0]
            check("red_trigger_wins_over_unknown_value", risk_over_unknown_value == "RED", risk_over_unknown_value, "RED")
        finally:
            connection.execute("ROLLBACK TO null_gate_check")
            connection.execute("RELEASE null_gate_check")

    overdue = results["q04_overdue_acceptance_payment_milestones"]["rows"]
    check("overdue_rows_use_unconfirmed_actual_completion", all(
        row["actual_date"] is None and row["planned_date"] < as_of and row["milestone"] in {"Acceptance","Payment"}
        for row in overdue
    ), len(overdue), "all selected rows have past due date and no recorded completion")
    manual_rows = [row for row in results["q05_nonrenewal_notice_review"]["rows"] if row["notice_basis"] != "Calendar"]
    check("noncalendar_dates_not_automatically_subtracted", all(row["calculated_notice_date"] is None for row in manual_rows),
          [{"contract_id":row["contract_id"],"date":row["calculated_notice_date"]} for row in manual_rows], "all NULL")

    # Data consistency and input-gate regressions remain executable on rebuild.
    if frozen_checks:
        renamed_count=connection.execute("SELECT count(*) FROM contracts WHERE counterparty=?",("Briar Glen Field Services Ltd.",)).fetchone()[0]
        check("sample_counterparty_count",renamed_count==4,renamed_count,4)
    blank_names=connection.execute("SELECT count(*) FROM contracts WHERE trim(counterparty)='' ").fetchone()[0]
    check("counterparty_names_complete",blank_names==0,blank_names,0)
    edge_cases = [
        ("missing_amount_personal_data", {"value_usd":None,"personal_data":"Yes"},"RED"),
        ("missing_amount_controlled", {"value_usd":None,"controlled_technology":"Yes"},"RED"),
        ("missing_amount_residuals", {"value_usd":None,"risk_trigger":"Residuals"},"RED"),
        ("missing_critical", {"personal_data":None},"NEEDS INPUT"),
        ("unknown_critical", {"controlled_technology":"Unknown"},"NEEDS INPUT"),
        ("missing_entity", {"entity_verified":None},"NEEDS INPUT"),
        ("missing_authority", {"signature_authority":None},"NEEDS INPUT"),
        ("unknown_risk", {"risk_trigger":"Unclassified"},"NEEDS INPUT"),
        ("numeric_risk", {"risk_trigger":0},"NEEDS INPUT"),
        ("zero_is_valid", {"value_usd":0},"GREEN"),
        ("threshold_yellow", {"value_usd":100000},"YELLOW"),
        ("threshold_red_missing", {"value_usd":250000,"personal_data":None},"RED"),
        ("known_no_entity", {"entity_verified":"No"},"YELLOW"),
        ("pending_review", {"reviewer_check":"Pending"},"YELLOW"),
    ]
    for name, edits, expected in edge_cases:
        connection.execute("SAVEPOINT edge_case")
        try:
            statement="UPDATE contracts SET "+", ".join(k+"=?" for k in edits)+" WHERE contract_id='C001'"
            connection.execute(statement,tuple(edits.values()))
            actual=connection.execute("SELECT computed_rag FROM v_contract_risk WHERE contract_id='C001'").fetchone()[0]
            check(name,actual==expected,actual,expected)
        finally:
            connection.execute("ROLLBACK TO edge_case")
            connection.execute("RELEASE edge_case")
    return {
        "all_passed": all(check["passed"] for check in checks),
        "source_counts": counts,
        "computed_rag_counts": computed_counts,
        "known_value_summary": values,
        "query_row_counts": {name:len(value["rows"]) for name,value in results.items()},
        "frozen_fixture_checks_enabled": frozen_checks,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=HERE.parent/"synthetic_data.json")
    parser.add_argument("--output-dir",type=Path,default=HERE)
    parser.add_argument("--as-of",default=None,help="ISO reporting date; defaults to source metadata")
    parser.add_argument("--audit-dir",type=Path,default=None,help="Optional directory for verification details")
    parser.add_argument("--accept-custom-dataset",action="store_true",help="Do not enforce frozen fixture counts and boundary records")
    args = parser.parse_args()
    source = args.input.expanduser().resolve()
    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True,exist_ok=True)
    data, source_hash = load_source(source)
    metadata = data["metadata"]
    as_of = args.as_of or metadata["as_of"]
    if dt.date.fromisoformat(as_of).isoformat() != as_of:
        raise ValueError("--as-of must be YYYY-MM-DD")
    db = output / "contracts_demo.sqlite"
    temporary = output / "contracts_demo.sqlite.tmp"
    temporary.unlink(missing_ok=True)
    connection = sqlite3.connect(temporary)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        connection.executescript((HERE/"schema.sql").read_text(encoding="utf-8"))
        connection.execute(
            "INSERT INTO dataset_settings VALUES (1,?,?,?,?,?,?,?,?,?,?)",
            (as_of, metadata["currency"], 1, metadata["policy_id"], metadata["threshold_yellow_usd"],
             metadata["threshold_red_usd"], metadata["near_term_days"], source_hash, metadata["notes"],
             json.dumps(metadata,sort_keys=True,ensure_ascii=False)),
        )
        insert_rows(connection,"contracts",CONTRACT_COLUMNS,data["contracts"])
        insert_rows(connection,"obligations",OBLIGATION_COLUMNS,data["obligations"])
        insert_rows(connection,"compliance_calendar",CALENDAR_COLUMNS,data["compliance_calendar"])
        connection.commit()
        queries = named_queries(HERE/"queries.sql")
        results = run_queries(connection,output,queries)
        verification = verify(connection,data,results,not args.accept_custom_dataset,as_of)
        verification.update({
            "as_of_date":as_of,"source_sha256":source_hash,"sqlite_version":sqlite3.sqlite_version,
            "executed_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "null_csv_sentinel":NULL_CSV,
        })
        if args.audit_dir:
            args.audit_dir.mkdir(parents=True,exist_ok=True)
            (args.audit_dir/"verification_results.json").write_text(json.dumps(verification,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        if not verification["all_passed"]:
            raise AssertionError("Database checks failed")
        connection.commit()
    finally:
        connection.close()
    temporary.replace(db)
    print(json.dumps({"database":str(db),"counts":verification["source_counts"],
        "rag":verification["computed_rag_counts"],"known_value":verification["known_value_summary"],
        "query_rows":verification["query_row_counts"],"checks_passed":len(verification["checks"])},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
