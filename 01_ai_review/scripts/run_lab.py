#!/usr/bin/env python3
"""Offline validation and repeated-review scoring. Never calls a model."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_IDS = ("run_a", "run_b", "run_c")
SCHEMA_KEYS = {"$schema", "title", "type", "additionalProperties", "required", "properties", "pattern", "const", "enum", "items", "minLength"}

class LabError(ValueError):
    pass

def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise LabError(f"Cannot read JSON: {Path(path).name}: {exc}") from exc

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def ratio(numerator, denominator):
    return None if denominator == 0 else numerator / denominator

def validate_schema(value, schema, path="$", errors=None):
    """Validate every keyword used by the bundled schema; reject unknown keywords."""
    errors = [] if errors is None else errors
    unknown = set(schema) - SCHEMA_KEYS
    if unknown:
        raise LabError(f"Unsupported schema keywords at {path}: {sorted(unknown)}")
    kind = schema.get("type")
    types = {"object": dict, "array": list, "string": str}
    if kind is not None and (kind not in types or not isinstance(value, types[kind])):
        errors.append(f"{path}: expected {kind}")
        return errors
    if "const" in schema and (value != schema["const"] or type(value) is not type(schema["const"])):
        errors.append(f"{path}: const differs")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: not an allowed enum value")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: empty or too short")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: pattern mismatch")
    if isinstance(value, dict):
        for field in schema.get("required", []):
            if field not in value:
                errors.append(f"{path}: missing {field}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for field in sorted(set(value) - set(properties)):
                errors.append(f"{path}: unexpected {field}")
        for field, sub in properties.items():
            if field in value:
                validate_schema(value[field], sub, f"{path}.{field}", errors)
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            validate_schema(item, schema["items"], f"{path}[{index}]", errors)
    return errors

def sections(source):
    return {f"Section {m.group(1)}": m.group(2) for m in re.finditer(r"^Section (\d+)\. (.*?)(?=^Section \d+\.|\Z)", source, re.M | re.S)}

def validate_batch_structure(reviews, cases, schema, policy_id, rules):
    if not isinstance(reviews, list):
        raise LabError("Batch must be a JSON array")
    seen = set()
    for index, review in enumerate(reviews):
        errors = validate_schema(review, schema)
        if errors:
            raise LabError(f"Review {index}: " + "; ".join(errors))
        doc_id = review["document_id"]
        if doc_id in seen:
            raise LabError(f"Duplicate document: {doc_id}")
        seen.add(doc_id)
        if review["policy_id"] != policy_id:
            raise LabError(f"Wrong policy: {doc_id}")
        ids = [issue["rule_id"] for issue in review["issues"]]
        if len(ids) != len(set(ids)):
            raise LabError(f"Duplicate document-rule finding: {doc_id}")
        if not set(ids) <= set(rules):
            raise LabError(f"Unknown rule: {doc_id}")
    if seen != set(cases):
        raise LabError(f"Batch document set differs; missing={sorted(set(cases)-seen)}, unexpected={sorted(seen-set(cases))}")

def route(issues):
    return "RED" if any(i["severity"] == "RED" for i in issues) else "YELLOW" if issues else "GREEN"

def analyze_batch(reviews, cases, sources, schema, policy_id, rules):
    validate_batch_structure(reviews, cases, schema, policy_id, rules)
    document_rows = []
    issue_evidence = {}
    findings_by_doc = {}
    for review in reviews:
        doc = review["document_id"]
        expected = {issue["rule_id"]: issue for issue in cases[doc]["expected"]}
        flags = {issue["rule_id"]: issue for issue in review["issues"]}
        findings_by_doc[doc] = flags
        section_map = sections(sources[doc])
        supported = set()
        unsupported_quotes = wrong_locations = severity_differences = reference_locator_differences = 0
        for rule_id, issue in flags.items():
            quote_ok = bool(issue["source_quote"]) and issue["source_quote"] in sources[doc]
            locator_ok = issue["source_quote"] in section_map.get(issue["source_locator"], "") and issue["source_locator"] in section_map
            if quote_ok and locator_ok:
                supported.add(rule_id)
            unsupported_quotes += not quote_ok
            wrong_locations += not locator_ok
            severity_differences += rule_id in expected and issue["severity"] != expected[rule_id]["severity"]
            reference_locator_differences += rule_id in expected and issue["source_locator"] != expected[rule_id]["source_locator"]
            issue_evidence[(doc, rule_id)] = {"present": True, "source_supported": quote_ok and locator_ok, "severity": issue["severity"], "source_locator": issue["source_locator"]}
        matched = set(expected) & supported
        tp, fp, fn = len(matched), len(flags) - len(matched), len(set(expected) - matched)
        reference_status = "NEED_SOURCE" if "SOURCE_COMPLETENESS" in expected else "REVIEW_READY"
        own_status = "NEED_SOURCE" if "SOURCE_COMPLETENESS" in flags else "REVIEW_READY"
        document_rows.append({
            "document_id": doc, "reference_issues": len(expected), "returned_findings": len(flags),
            "tp": tp, "fp": fp, "fn": fn, "presence_tp": len(set(expected) & set(flags)),
            "unsupported_quotes": unsupported_quotes, "wrong_locations": wrong_locations,
            "severity_differences": severity_differences, "reference_locator_differences": reference_locator_differences,
            "reference_route_differences": int(review["risk"] != route(list(expected.values()))),
            "internal_route_errors": int(review["risk"] != route(review["issues"])),
            "reference_status_differences": int(review["review_status"] != reference_status),
            "internal_status_errors": int(review["review_status"] != own_status),
        })
    document_rows.sort(key=lambda row: row["document_id"])
    numeric = [key for key in document_rows[0] if key != "document_id"] if document_rows else []
    summary = {key: sum(row[key] for row in document_rows) for key in numeric}
    summary.update({"documents": len(document_rows), "precision": ratio(summary.get("tp", 0), summary.get("tp", 0) + summary.get("fp", 0)), "recall": ratio(summary.get("tp", 0), summary.get("tp", 0) + summary.get("fn", 0))})
    return summary, document_rows, issue_evidence, findings_by_doc

def consistency_rows(analyses, cases, rules):
    rows = []
    for doc in sorted(cases):
        expected = {i["rule_id"] for i in cases[doc]["expected"]}
        for rule in sorted(rules):
            found = [int((doc, rule) in result[2]) for result in analyses]
            supported = [int(result[2].get((doc, rule), {}).get("source_supported", False)) for result in analyses]
            signatures = [None if (doc, rule) not in result[2] else (result[2][(doc, rule)]["severity"], result[2][(doc, rule)]["source_locator"]) for result in analyses]
            row = {"document_id": doc, "rule_id": rule, "reference_positive": rule in expected}
            for index, run in enumerate(RUN_IDS):
                row[f"{run}_present"] = found[index]
                row[f"{run}_supported"] = supported[index]
            row.update({"presence_agreement": len(set(found)) == 1, "supported_detection_agreement": len(set(supported)) == 1,
                        "severity_locator_agreement": len(set(signatures)) == 1,
                        "found_in_every_run": all(found), "supported_in_every_run": all(supported),
                        "missed_in_every_run": rule in expected and not any(supported),
                        "unstable_supported_detection": len(set(supported)) != 1})
            rows.append(row)
    return rows

def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def write_csv(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)

def load_inputs(root):
    labels = read_json(root / "evaluation/reference_labels.json")
    policy = read_json(root / "policy/nda_demo_policy.json")
    schema = read_json(root / "review_output.schema.json")
    sources = {}
    for case in labels["cases"]:
        path = root / case["input_path"]
        if sha256(path) != case["sha256"]:
            raise LabError(f"Source hash differs: {case['document_id']}")
        sources[case["document_id"]] = path.read_text(encoding="utf-8")
    return labels, policy, schema, sources

def validate_frozen_request(root, labels, policy, schema, sources):
    path = root / "repeatability/frozen_review_request.json"
    request = read_json(path)
    manifest = read_json(root / "repeatability/request_manifest.json")
    if sha256(path) != manifest["request_sha256"]:
        raise LabError("Frozen request hash differs")
    if request["prompt"] != (root / "prompts/review_v2.md").read_text(encoding="utf-8"):
        raise LabError("Prompt differs from frozen request")
    if request["policy"] != policy or request["output_schema"] != schema:
        raise LabError("Policy/schema differs from frozen request")
    heldout = {c["document_id"]: c for c in labels["cases"] if c["split"] == "heldout"}
    documents = {d["document_id"]: d for d in request["documents"]}
    if len(documents) != len(request["documents"]) or set(documents) != set(heldout):
        raise LabError("Frozen request document set differs")
    for doc, data in documents.items():
        if data["text"] != sources[doc] or hashlib.sha256(data["text"].encode()).hexdigest() != data["sha256"] or data["sha256"] != heldout[doc]["sha256"]:
            raise LabError(f"Frozen request input differs: {doc}")
    if any(k in request for k in ["reference_labels", "expected", "scores"]):
        raise LabError("Reference data present in frozen request")
    return heldout, manifest

def make_report(summary):
    rows = summary["runs"]
    fmt = lambda value: "undefined" if value is None else f"{100*value:.1f}%"
    text = ["# NDA repeatability: three independent agent batches", "", "**Scope.** The same frozen prompt, policy and 15 synthetic agreements were supplied to three independent reviewer agents. The request excludes the reference labels. Each agent returned one batch: 45 document reviews in total. This is an agent-session study; model snapshot and sampling settings are not exposed. It is not a fixed-version API experiment.", "", "| Batch | TP | FP | FN | Precision | Recall |", "|---|---:|---:|---:|---:|---:|"]
    text += [f"| {r['run_id']} | {r['tp']} | {r['fp']} | {r['fn']} | {fmt(r['precision'])} | {fmt(r['recall'])} |" for r in rows]
    c = summary["consistency"]
    text += ["", f"**Consistency.** {c['positive_issues_supported_in_every_run']} of {c['positive_reference_issues']} reference issue instances had a source-supported finding in all three batches. {c['unstable_positive_issue_detections']} positive issue detections changed across batches; {c['positive_issues_missed_in_every_run']} were missed in every batch. Across all {c['document_rule_opportunities']} document–rule opportunities ({c['negative_opportunities']} reference negatives), {c['presence_agreement_count']} had the same flag-presence decision in every batch.", "", "**Scoring.** A true positive requires a matching document/rule pair plus an exact quote in its stated Section. An unsupported returned finding counts as FP and leaves an expected issue as FN. Precision = TP/(TP+FP); recall = TP/(TP+FN). An empty denominator is undefined, not 100%. Severity, route and source-status differences are reported separately.", "", "**Interpretation.** Agreement measures repeatability, not correctness: three identical misses are stable but wrong. These are synthetic, policy-bound examples; no new-contract, deployment or production-performance claim follows. Inspect per_issue_consistency.csv for all 16 positive instances and 209 negative opportunities, and per_document_checks.csv for evidence and routing differences.", "", "**Next controlled study.** Use a pinned API model ID, record endpoint and sampling settings, submit each document independently three times, preserve raw responses and request IDs, and score without changing the frozen prompt or reference key. The present saved agent batches must remain a separate cohort.", ""]
    return "\n".join(text)

def score_repeats(root, labels, policy, schema, sources):
    cases, manifest = validate_frozen_request(root, labels, policy, schema, sources)
    rep = root / "repeatability"
    analyses = []
    for run in RUN_IDS:
        path = rep / "runs" / f"{run}.json"
        if not path.is_file():
            raise LabError(f"Missing independent batch: {path.name}")
        analyses.append(analyze_batch(read_json(path), cases, sources, schema, policy["policy_id"], policy["rules"]))
    hashes = {"frozen_request": sha256(rep / "frozen_review_request.json"), "reference_labels": sha256(root / "evaluation/reference_labels.json"), "policy": sha256(root / "policy/nda_demo_policy.json"), "schema": sha256(root / "review_output.schema.json"), "prompt": sha256(root / "prompts/review_v2.md"), "runs": {run: sha256(rep / "runs" / f"{run}.json") for run in RUN_IDS}}
    provenance = {"scope": "Inputs and unmodified saved outputs used for this local scoring cohort.", "hashes": hashes, "execution_mode": manifest["execution_mode"], "model_id": manifest["model_id"], "model_snapshot": manifest["model_snapshot"], "temperature": manifest["temperature"], "configuration_note": manifest["configuration_note"]}
    provenance_path = rep / "scored_cohort_manifest.json"
    if provenance_path.exists() and read_json(provenance_path) != provenance:
        raise LabError("Scored cohort bytes changed; preserve this cohort and create a separately named study")
    consistency = consistency_rows(analyses, cases, policy["rules"])
    positives = [r for r in consistency if r["reference_positive"]]
    negatives = [r for r in consistency if not r["reference_positive"]]
    summary = {"study": "Three independent agent-batch reviews", "documents_per_batch": len(cases), "independent_agent_batches": len(RUN_IDS), "document_reviews": len(cases)*len(RUN_IDS), "rule_types": len(policy["rules"]), "reference_issue_instances_per_batch": sum(len(c["expected"]) for c in cases.values()), "matching_unit": "document_id + rule_id; primary TP requires exact quote in stated Section", "denominator_policy": "Zero denominator -> null (undefined)", "execution": {k: provenance[k] for k in ["execution_mode", "model_id", "model_snapshot", "temperature", "configuration_note"]}, "runs": [{"run_id": run, **analysis[0]} for run, analysis in zip(RUN_IDS, analyses)], "consistency": {"document_rule_opportunities": len(consistency), "positive_reference_issues": len(positives), "negative_opportunities": len(negatives), "positive_issues_supported_in_every_run": sum(r["supported_in_every_run"] for r in positives), "positive_issues_missed_in_every_run": sum(r["missed_in_every_run"] for r in positives), "unstable_positive_issue_detections": sum(r["unstable_supported_detection"] for r in positives), "presence_agreement_count": sum(r["presence_agreement"] for r in consistency), "supported_detection_agreement_count": sum(r["supported_detection_agreement"] for r in consistency), "false_positive_opportunities_in_any_run": sum(any(r[f"{run}_present"] for run in RUN_IDS) for r in negatives)}, "limits": ["Synthetic fixed set; 16 issue instances are not 16 distinct issue types", "No model snapshot or sampling controls are exposed; not controlled API inference", "Three independent agent batches, not 45 independently logged API requests", "Stable detections or misses are not by themselves evidence of legal correctness", "The previously used held-out split is reused; this study is not a new unseen validation set"]}
    write_json(provenance_path, provenance)
    write_json(rep / "results_summary.json", summary)
    write_csv(rep / "per_run_metrics.csv", summary["runs"])
    write_csv(rep / "per_issue_consistency.csv", consistency)
    write_csv(rep / "per_document_checks.csv", [{"run_id": run, **row} for run, analysis in zip(RUN_IDS, analyses) for row in analysis[1]])
    (rep / "Repeatability_Report.md").write_text(make_report(summary), encoding="utf-8")
    return summary

def check(root, require_repeats=False):
    labels, policy, schema, sources = load_inputs(root)
    archived = []
    for filename, split in [("v1_development", "development"), ("v2_development", "development"), ("v2_heldout", "heldout")]:
        cases = {c["document_id"]: c for c in labels["cases"] if c["split"] == split}
        analysis = analyze_batch(read_json(root / f"evaluation/saved_reviews/{filename}.json"), cases, sources, schema, policy["policy_id"], policy["rules"])
        archived.append({"batch": filename, **analysis[0]})
    validate_frozen_request(root, labels, policy, schema, sources)
    found = [(root / "repeatability/runs" / f"{run}.json").exists() for run in RUN_IDS]
    repeated = score_repeats(root, labels, policy, schema, sources) if all(found) else None
    if require_repeats and repeated is None:
        raise LabError("Three independent batches are required; not all are saved yet")
    checks = ["20 source hashes", "supplied output-schema subset", "complete unique document sets", "unique document-rule findings", "policy/rule identifiers", "exact source quotes", "quotes in cited Sections", "highest-severity internal routes", "source-request internal statuses", "human-review gate", "frozen prompt/policy/schema/request identity"]
    report = {"status": "PASS", "checks": checks, "archived_batches": archived, "repeated_batches_available": sum(found), "repeatability_scored": repeated is not None, "repeatability": repeated}
    for batch in archived + (repeated["runs"] if repeated else []):
        if any(batch[field] for field in ["unsupported_quotes", "wrong_locations", "internal_route_errors", "internal_status_errors"]):
            report["status"] = "FAIL"
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "score", "export-request"])
    parser.add_argument("--require-repeats", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit JSON (the default); stable flag for the local UI")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        if args.command == "export-request":
            labels, policy, schema, sources = load_inputs(args.root)
            validate_frozen_request(args.root, labels, policy, schema, sources)
            print((args.root / "repeatability/frozen_review_request.json").read_text(), end="")
            return 0
        if args.command == "score":
            result = score_repeats(args.root, *load_inputs(args.root))
        else:
            result = check(args.root, args.require_repeats)
        print(json.dumps(result, indent=2))
        return int(result.get("status") == "FAIL")
    except LabError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
