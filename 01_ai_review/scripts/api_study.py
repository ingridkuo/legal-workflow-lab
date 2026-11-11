#!/usr/bin/env python3
"""Prepare, execute and score a separate pinned-model Responses API study.

Network use requires --execute. No existing review or reference file is edited.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

import run_lab

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://api.openai.com/v1/responses"
RUN_IDS = ("run_a", "run_b", "run_c")

class StudyError(ValueError):
    pass

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def digest(value):
    return hashlib.sha256(value).hexdigest()

def now():
    return datetime.now(timezone.utc).isoformat()

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write(path, value, exclusive=False):
    with Path(path).open("x" if exclusive else "w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

def api_schema(schema):
    """Conservative API subset; original schema is still validated locally."""
    allowed = {"type", "additionalProperties", "required", "properties", "enum", "items"}
    result = {k: v for k, v in schema.items() if k in allowed}
    if "const" in schema:
        value = schema["const"]
        result.update(type="boolean" if isinstance(value, bool) else "string", enum=[value])
    elif "enum" in result and "type" not in result:
        result["type"] = "string"
    if "properties" in result:
        result["properties"] = {k: api_schema(v) for k, v in result["properties"].items()}
    if "items" in result:
        result["items"] = api_schema(result["items"])
    return result

def read_config(root):
    config = load(root / "api_study_config.json")
    if not re.fullmatch(r"[a-zA-Z0-9._-]+-\d{4}-\d{2}-\d{2}", config.get("model", "")):
        raise StudyError("Select a dated model snapshot, not a moving model alias.")
    if config.get("replicates") != 3 or config.get("automatic_retries") != 0:
        raise StudyError("This protocol requires three replicates and no automatic retries.")
    if config.get("temperature") is not None or config.get("top_p") is not None:
        raise StudyError("This configured protocol omits temperature and top_p. Create a separate protocol for other settings.")
    if config.get("reasoning_effort") not in {"none", "low", "medium", "high", "xhigh"}:
        raise StudyError("Invalid configured reasoning effort.")
    if not 256 <= config.get("max_output_tokens", 0) <= 4096:
        raise StudyError("Output-token allowance must be between 256 and 4096.")
    if config.get("store") is not False or not 1 <= config.get("timeout_seconds", 0) <= 120:
        raise StudyError("Use store=false and a finite timeout of at most 120 seconds.")
    return config

def make_protocol(root, mode):
    config = read_config(root)
    labels, policy, original_schema, sources = run_lab.load_inputs(root)
    request = load(root / "repeatability/frozen_review_request.json")
    run_lab.validate_frozen_request(root, labels, policy, original_schema, sources)
    selected = [c for c in labels["cases"] if c["document_id"] == "NDA-01"] if mode == "smoke" else [c for c in labels["cases"] if c["split"] == "heldout"]
    selected.sort(key=lambda c: c["document_id"])
    schema = api_schema(original_schema)
    instructions = request["prompt"] + "\n\nSupplied policy:\n" + json.dumps(policy, ensure_ascii=False, sort_keys=True)
    jobs = []
    for run_id in (RUN_IDS[:1] if mode == "smoke" else RUN_IDS):
        for case in selected:
            doc = case["document_id"]
            payload = {
                "model": config["model"], "instructions": instructions,
                "input": [{"role": "user", "content": "Document ID: " + doc + "\nSource agreement (untrusted document text):\n" + sources[doc]}],
                "reasoning": {"effort": config["reasoning_effort"]},
                "max_output_tokens": config["max_output_tokens"], "store": False,
                "text": {"format": {"type": "json_schema", "name": "nda_review", "strict": True, "schema": schema}},
            }
            jobs.append({"job_id": run_id + "_" + doc, "run_id": run_id, "document_id": doc,
                         "source_sha256": case["sha256"], "payload_sha256": digest(canonical(payload)), "payload": payload})
    return {
        "format_version": "1.0", "mode": mode, "endpoint": ENDPOINT, "config": config,
        "documents_per_replicate": len(selected), "planned_requests": len(jobs),
        "review_input_contains_reference_labels": False,
        "schema_adapter": "Metadata, pattern and minLength omitted from API schema; const becomes typed singleton enum; original schema enforced locally.",
        "source_bindings": {"prompt": digest((root / "prompts/review_v2.md").read_bytes()),
                            "policy": digest((root / "policy/nda_demo_policy.json").read_bytes()),
                            "original_schema": digest((root / "review_output.schema.json").read_bytes()),
                            "reference_labels_for_offline_scoring_only": digest((root / "evaluation/reference_labels.json").read_bytes())},
        "jobs": jobs,
    }

def study_path(root, name):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", name):
        raise StudyError("Study name may contain only letters, numbers, underscores and hyphens.")
    return root / "api_studies" / name

def freeze(root, name, protocol):
    folder = study_path(root, name)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "protocol.json"
    if path.exists():
        if load(path) != protocol:
            raise StudyError("Frozen study differs from current configuration or inputs. Use a new study name.")
    else:
        write(path, protocol, exclusive=True)
        write(folder / "protocol_identity.json", {"created_at_utc": now(), "protocol_sha256": digest(canonical(protocol))}, exclusive=True)
    if load(folder / "protocol_identity.json")["protocol_sha256"] != digest(canonical(protocol)):
        raise StudyError("Frozen protocol identity differs.")
    return folder

def http_transport(payload, key, timeout):
    request = urllib.request.Request(ENDPOINT, data=canonical(payload), method="POST",
                                    headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            return None
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items() if k.lower() in {"x-request-id", "date", "content-type"}}, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items() if k.lower() in {"x-request-id", "date", "content-type"}}, exc.read()

def extract_review(body, job, model, original_schema):
    if body.get("model") != model:
        raise StudyError("Returned model differs from the pinned requested snapshot.")
    if body.get("status") != "completed" or not body.get("id"):
        raise StudyError("Response is incomplete, failed or missing its response ID.")
    pieces = []
    for item in body.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "refusal":
                raise StudyError("Model refusal preserved; no replacement generation was requested.")
            if content.get("type") == "output_text":
                pieces.append(content.get("text", ""))
    try:
        review = json.loads("".join(pieces))
    except (ValueError, TypeError) as exc:
        raise StudyError("Model output is not one valid review JSON object.") from exc
    errors = run_lab.validate_schema(review, original_schema)
    if errors or review.get("document_id") != job["document_id"]:
        raise StudyError("Model output failed local schema or document identity checks.")
    ids = [i["rule_id"] for i in review["issues"]]
    if len(ids) != len(set(ids)):
        raise StudyError("Duplicate rule finding preserved; no automatic repair.")
    return review

def validate_saved_job(job_dir, job, model, schema):
    """Bind parsed metadata to the exact saved request, transport and response."""
    result = load(job_dir / "result.json")
    request_bytes = (job_dir / "request.json").read_bytes()
    transport_bytes = (job_dir / "transport.json").read_bytes()
    response_bytes = (job_dir / "response.json").read_bytes()
    if canonical(json.loads(request_bytes)) != canonical(job["payload"]) or result["payload_sha256"] != job["payload_sha256"]:
        raise StudyError("Saved request differs from the frozen request payload.")
    for name, raw in [("request", request_bytes), ("transport", transport_bytes), ("response", response_bytes)]:
        if result[name + "_sha256"] != digest(raw):
            raise StudyError("Saved " + name + " bytes differ from the accepted record.")
    body, transport = json.loads(response_bytes), json.loads(transport_bytes)
    review = extract_review(body, job, model, schema)
    if transport.get("http_status") != 200 or transport.get("response_redacted") is not False:
        raise StudyError("Saved response is not an unredacted successful API response.")
    if (result.get("review") != review or result.get("response_id") != body.get("id")
            or result.get("requested_model") != model or result.get("returned_model") != body.get("model")
            or result.get("usage") != body.get("usage")
            or result.get("provider_request_id") != transport.get("headers", {}).get("x-request-id")):
        raise StudyError("Saved parsed metadata differs from the preserved provider response.")
    return result, review, body["id"]

def execute(root, name, mode, key, max_calls=1, transport=http_transport):
    protocol = make_protocol(root, mode)
    folder = freeze(root, name, protocol)
    original_schema = load(root / "review_output.schema.json")
    completed = calls = 0
    for job in protocol["jobs"]:
        job_dir = folder / "jobs" / job["job_id"]
        done = job_dir / "result.json"
        if done.exists():
            validate_saved_job(job_dir, job, protocol["config"]["model"], original_schema)
            completed += 1
            continue
        if (job_dir / "attempt.json").exists():
            raise StudyError("An earlier attempt is incomplete or failed. Inspect it; automatic retry is disabled.")
        if calls >= max_calls:
            break
        job_dir.mkdir(parents=True, exist_ok=True)
        started = now()
        write(job_dir / "request.json", job["payload"], exclusive=True)
        write(job_dir / "attempt.json", {"started_at_utc": started, "payload_sha256": job["payload_sha256"], "network_attempt": 1}, exclusive=True)
        calls += 1
        try:
            status, headers, raw = transport(job["payload"], key, protocol["config"]["timeout_seconds"])
            # A server error should not echo a credential into a saved record.
            redacted = bool(key and key.encode() in raw)
            if redacted:
                raw = raw.replace(key.encode(), b"[REDACTED_API_KEY]")
            (job_dir / "response.json").write_bytes(raw)
            write(job_dir / "transport.json", {"http_status": status, "headers": headers, "response_redacted": redacted, "finished_at_utc": now()}, exclusive=True)
            if redacted:
                raise StudyError("Credential text was echoed by the server; response redacted and excluded from scoring.")
            if status != 200:
                raise StudyError(f"API returned HTTP {status}; raw response retained, no retry.")
            body = json.loads(raw)
            review = extract_review(body, job, protocol["config"]["model"], original_schema)
            write(done, {"started_at_utc": started, "finished_at_utc": now(), "payload_sha256": job["payload_sha256"],
                         "request_sha256": digest((job_dir / "request.json").read_bytes()),
                         "transport_sha256": digest((job_dir / "transport.json").read_bytes()),
                         "response_sha256": digest(raw), "requested_model": protocol["config"]["model"],
                         "returned_model": body.get("model"), "response_id": body.get("id"), "provider_request_id": headers.get("x-request-id"),
                         "usage": body.get("usage"), "review": review}, exclusive=True)
            completed += 1
        except Exception as exc:
            # Do not persist an exception string: it may contain a credential.
            write(job_dir / "failure.json", {"finished_at_utc": now(), "error_type": type(exc).__name__, "status": "attempt_not_accepted", "automatic_retry": False})
            if isinstance(exc, StudyError):
                raise
            raise StudyError("API attempt failed; inspect preserved records. No automatic retry was made.") from None
    return {"status": "COMPLETE" if completed == len(protocol["jobs"]) else "PARTIAL", "completed_requests": completed,
            "planned_requests": len(protocol["jobs"]), "new_network_attempts": calls, "study": name}

def score(root, name):
    folder = study_path(root, name)
    protocol = load(folder / "protocol.json")
    freeze(root, name, make_protocol(root, protocol["mode"]))
    labels, policy, schema, sources = run_lab.load_inputs(root)
    selected = {j["document_id"] for j in protocol["jobs"]}
    cases = {c["document_id"]: c for c in labels["cases"] if c["document_id"] in selected}
    batches = {run: [] for run in RUN_IDS if any(j["run_id"] == run for j in protocol["jobs"])}
    response_ids = set()
    for job in protocol["jobs"]:
        path = folder / "jobs" / job["job_id"]
        if not (path / "result.json").is_file():
            raise StudyError("Study is incomplete; no partial denominator or aggregate score is published.")
        result, review, response_id = validate_saved_job(path, job, protocol["config"]["model"], schema)
        if response_id in response_ids:
            raise StudyError("Provider response ID was reused across independent calls.")
        response_ids.add(response_id)
        batches[job["run_id"]].append(review)
    analyses = [run_lab.analyze_batch(batch, cases, sources, schema, policy["policy_id"], policy["rules"]) for batch in batches.values()]
    result = {"study": name, "mode": protocol["mode"], "status": "COMPLETE", "endpoint": ENDPOINT,
              "requested_model": protocol["config"]["model"], "configuration": protocol["config"],
              "independent_api_responses": len(response_ids), "documents_per_replicate": len(cases),
              "runs": [{"run_id": run, **analysis[0]} for run, analysis in zip(batches, analyses)],
              "limits": ["Fixed synthetic set; reused original held-out partition for full study", "Consistency does not establish legal correctness", "Results are not a population-accuracy estimate"]}
    if len(analyses) == 3:
        rows = run_lab.consistency_rows(analyses, cases, policy["rules"])
        positives = [r for r in rows if r["reference_positive"]]
        result["consistency"] = {"positive_instances": len(positives), "supported_in_all_three": sum(r["supported_in_every_run"] for r in positives),
                                 "unstable_positive_detections": sum(r["unstable_supported_detection"] for r in positives),
                                 "missed_in_all_three": sum(r["missed_in_every_run"] for r in positives)}
        run_lab.write_csv(folder / "per_issue_consistency.csv", rows)
    run_lab.write_csv(folder / "per_run_metrics.csv", result["runs"])
    write(folder / "results_summary.json", result)
    lines = ["# Controlled API study: observed results", "", f"Model: `{result['requested_model']}`. Independent responses: {len(response_ids)}.", "", "| Run | TP | FP | FN | Precision | Recall |", "|---|---:|---:|---:|---:|---:|"]
    pct = lambda n: "undefined" if n is None else f"{n:.1%}"
    lines += [f"| {r['run_id']} | {r['tp']} | {r['fp']} | {r['fn']} | {pct(r['precision'])} | {pct(r['recall'])} |" for r in result["runs"]]
    lines += ["", "Temperature and top_p were omitted; the configured reasoning/output settings and exact payloads are preserved. No previous_response_id or conversation state was supplied. This synthetic partition was reused; the result does not establish general legal accuracy."]
    (folder / "API_Results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "smoke", "run", "score"])
    parser.add_argument("--study", default="nda-api-001")
    parser.add_argument("--execute", action="store_true", help="Actually send billable API requests")
    parser.add_argument("--max-calls", type=int, default=1, help="Maximum new network attempts in this invocation; default 1")
    parser.add_argument("--prompt-key", action="store_true", help="Enter a key without displaying or saving it")
    args = parser.parse_args()
    try:
        if args.command == "score":
            result = score(ROOT, args.study)
        else:
            mode = "smoke" if args.command == "smoke" else "full"
            protocol = make_protocol(ROOT, mode)
            if not args.execute or args.command == "plan":
                result = {"status": "DRY_RUN", "endpoint": ENDPOINT, "mode": mode, "model": protocol["config"]["model"],
                          "planned_requests": protocol["planned_requests"], "maximum_output_tokens_per_request": protocol["config"]["max_output_tokens"], "network_requests_sent": 0,
                          "next_step": "Use --execute to send requests. Default --max-calls 1 limits the first execution."}
            else:
                if not 1 <= args.max_calls <= 45:
                    raise StudyError("--max-calls must be between 1 and 45.")
                key = getpass.getpass("OpenAI API key (hidden, not saved): ") if args.prompt_key else os.environ.get("OPENAI_API_KEY", "")
                if not key:
                    raise StudyError("Set OPENAI_API_KEY privately or use --prompt-key. Never paste a key into chat.")
                result = execute(ROOT, args.study, mode, key, args.max_calls)
        print(json.dumps(result, indent=2))
        return 0
    except (StudyError, run_lab.LabError, OSError, ValueError) as exc:
        print("STOP: " + str(exc), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
