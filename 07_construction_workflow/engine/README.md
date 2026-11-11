# Subcontract Workflow — Local Prototype

Independent legal-operations work sample. All projects, companies, people, amounts and decisions are fictional. The policy is a configurable example and does not establish company approval authority or an operating policy.

This is a working rule-based Python command-line prototype, using only the Python standard library. It validates intake, routes sequential reviews, records demonstration signatures, prevents invalid transitions, retains a local event history, and exports a weekly report. No external account is needed; no Slack, Make, contract platform or eSignature integration is built or called.

## Quick start

Requires Python 3.10+ on native Windows, Linux or macOS, with no extra packages. Run these commands from this `engine` folder. On Windows, use `py` wherever the examples show `python` if that is your installed launcher:

```bash
python workflow.py verify
python workflow.py list
python workflow.py report --as-of 2026-11-11 --out-dir exports
python -m unittest -v test_workflow.py
```

The included `demo_events.jsonl` already contains ten synthetic cases. To build a separate fresh copy, choose an unused file:

```bash
python workflow.py --db practice_events.jsonl demo
python workflow.py --db practice_events.jsonl show SC-006
python workflow.py --db practice_events.jsonl history SC-006
```

`demo` refuses to overwrite any nonempty store. The default deterministic report date is 11 November 2026; specify another `--as-of` date to reconstruct the available history at that date. Mutation commands use the current UTC time unless given `--at`.

## Intake form and JSON import

A guided form prompts for each field, including yes/no required-document flags. A JSON object or list can also be imported. Both create **Intake** records; an explicit `start` begins Legal Review. Importing a final register does not import its approval/signature/status fields: state always starts fresh.

```bash
python workflow.py --db intake_practice.jsonl intake --actor demo_loader
python workflow.py --db imported_intakes.jsonl import example_intakes.json --actor demo_loader
python workflow.py --db imported_intakes.jsonl start SC-001 --actor requester_001 --at 2026-11-09T10:00:00Z
```

Use a different unused database file for each independent exercise. IDs are unique within a store. Duplicate-ID or invalid-field imports write no partial batch.

| Field | Format / check |
|---|---|
| `id`, `project_name`, `subcontractor_name`, `scope` | Required nonblank text |
| `requestor_id`, `subcontractor_signatory_id` | Required local demonstration identities; the two signature parties must differ |
| `amount_usd` | Positive decimal with at most two decimal places; boundary calculations use `Decimal` |
| `currency` | USD only; defaults to USD |
| `submitted_at` | Explicit UTC ISO timestamp, e.g. `2026-11-09T09:00:00Z` |
| `needed_by_date` | Required YYYY-MM-DD; used for overdue reporting |
| `planned_start_date`, `contract_expiry_date` | Required YYYY-MM-DD; contract expiry cannot precede planned start |
| `exceptional_terms` | Strict JSON boolean; true requires nonblank `exception_notes` |
| `guarantee_required`, `insurance_required` | Strict JSON booleans |
| `guarantee_reference`, `guarantee_expiry_date` | Reference text and YYYY-MM-DD; may be blank at intake |
| `insurance_reference`, `insurance_expiry_date` | Reference text and YYYY-MM-DD; may be blank at intake |

The examples use synthetic document references rather than actual attachments. Presence and date checks do not establish document authenticity, coverage adequacy or legal enforceability.

## Fictional policy and states

The route is **Legal → Senior Legal if nonstandard terms → Project Manager → Finance when required → Executive when required**. Legal review applies at every value. The two business threshold tests are strictly `> 50,000` and `> 250,000`.

| Amount in USD | Business approval sequence after Legal / any Senior Legal |
|---|---|
| ≤ $50,000.00 | Project Manager |
| $50,000.01–$250,000.00 | Project Manager → Finance |
| ≥ $250,000.01 | Project Manager → Finance → Executive |

`approval_rules.json` defines the thresholds, route, local owner IDs and authorized company signatory. Each new record stores its required route and owner assignments, so later rule edits do not silently rewrite existing records. A deliberate `assign` command can change a pending reviewer, with an audit event.

The finite states are **Intake, Legal Review, Business Approval, Ready for Signature, Counterparty Signed, Executed, Rejected and Hold**. Reviews must follow the stored order. The actor must match the next assigned reviewer, and the requester cannot approve or reject their own request. Decisions require a note.

Missing or expired required guarantees/insurance do not prevent intake or review; they place the record on Hold at review completion. Document checks also run before each signature. An attempted signature by the correct signatory with invalid coverage records a `signature_blocked` event, sets Hold and records no signature. A required document expires after the date stated; it is considered current on that date. Dates are illustrative checks, not a determination of actual coverage.

Both signature steps occur only after all required approvals. The subcontractor signs first, followed by the configured authorized company signatory. Each is a local **demonstration record only**, with actor and UTC timestamp; no binding electronic signature is created. Executed records have an execution date. Executed and Rejected are terminal: create a new intake for new work.

### A safe local exercise

The following commands operate on `practice_events.jsonl`, created by the fresh-demo command above. SC-006 is held for a missing guarantee. Supply it, then record the two demonstration signatures:

```bash
python workflow.py --db practice_events.jsonl documents SC-006 --actor requester_006 --at 2026-11-11T10:00:00Z --file guarantee_update_example.json
python workflow.py --db practice_events.jsonl sign SC-006 --actor sub_signatory_006 --at 2026-11-11T11:00:00Z
python workflow.py --db practice_events.jsonl sign SC-006 --actor company_signatory_001 --at 2026-11-11T12:00:00Z
python workflow.py --db practice_events.jsonl history SC-006
```

A rejected transition exits with code 2 and a specific reason. `check-docs` can explicitly re-evaluate coverage and place a ready/counterparty-signed record on Hold. Updating valid coverage releases Hold to the correct signature stage while preserving a previously recorded subcontractor signature.

To review SC-001 and demonstrate business routing:

```bash
python workflow.py --db practice_events.jsonl approve SC-001 --actor legal_001 --at 2026-11-11T13:00:00Z --note "Synthetic Legal review complete"
python workflow.py --db practice_events.jsonl approve SC-001 --actor pm_001 --at 2026-11-11T14:00:00Z --note "Synthetic project approval complete"
```

To reassign a pending reviewer, use the configured workflow admin and an independent reviewer ID:

```bash
python workflow.py --db practice_events.jsonl assign SC-005 --actor ops_001 --at 2026-11-11T15:00:00Z --role senior_legal --reviewer-id senior_legal_backup
```

## Weekly report and local exports

```bash
python workflow.py report --as-of 2026-11-11 --out-dir exports
python workflow.py export-register --as-of 2026-11-11 --file live_register.json
```

`report` writes `weekly_report.json`, `weekly_register.csv` and `slack_ready.txt`. The Slack-ready text is a local copy/paste draft; no message is sent. `export-register` produces a flat JSON register comparable to `sample_register.json`.

For the included fixture as of 11 November 2026:

| Metric | Result |
|---|---:|
| Total cases | 10 |
| Open queue (excludes Executed and Rejected) | 8 |
| Submitted this week, 9–11 November | 2 |
| Executed this week, 9–11 November | 1 |
| Active overdue cases | 3 |
| Guarantee expiry within 30 days | 2 |
| Missing required guarantee | 1 |

Definitions:

- The report week starts Monday and ends on the selected as-of date, inclusive, in UTC. Historical snapshots exclude future events rather than applying current state to earlier dates.
- Volume counts submitted/executed dates within that interval. Queue counts show all active records as of the date, grouped by stage and current owner.
- Aging is calendar days since intake for active cases. Overdue means the needed-by date is before as-of; due today is not overdue. Executed and Rejected are excluded.
- Execution turnaround is elapsed UTC days from intake to company signature. Review turnaround is elapsed UTC days from intake to the final required approval, only where all required reviews are complete. Means include all available completed cases as of the date, not only this week's cases, and display their sample sizes. The fixture has one completed execution (12.125 elapsed days) and four completed review sequences (2.625 elapsed days mean); rounded display is 12.12 and 2.62 respectively. The workbook may separately use calendar-date turnaround.
- Guarantee alerts include required guarantees on non-rejected contracts whose contract end has not passed, including active Executed contracts. Missing reference/date takes priority; expired is before as-of; due within 30 days includes today through `as_of + 30` days. For 11 November, SC-003 and SC-008 are due; SC-006 is missing.
- No saved-time or productivity outcome has been measured.

## Audit and operating limits

Every successful mutation appends a UTC-timestamped event with actor, action, record snapshot, sequence number and SHA-256 link to the previous event. The CLI has no edit/delete-history command. `verify` checks sequence and hash-chain integrity before reporting success; reads/mutations also validate the chain. Invalid transitions do not alter history. File writes are locally locked and flushed. A portable exclusive `<database filename>.lock` file prevents overlapping writers; contention fails clearly rather than waiting. The lock is removed automatically after success or a handled failure. An interrupted or forcibly terminated process may leave a stale lock. Confirm that no workflow process is running before manually deleting that `.lock` file, then retry. Do not delete an active writer’s lock.

This is not a production authorization system. Actor IDs are typed by the operator; identities, permissions, signatory authority, attachments and consent are not authenticated. The chain detects edits without recomputed hashes, but does not prevent an operator with filesystem access from truncating or rebuilding the complete file; no external audit anchor exists. No production deployment, secure storage, notification delivery, retention program or account integration is supplied.

## Validation

`python -m unittest -v test_workflow.py` passed **38 tests**, including portable-locking and UTF-8 checks. Coverage includes threshold boundaries, exception escalation, required fields and UTC dates, self-approval, order/actor checks, premature signatures, document Hold/release, expiry between the two signatures, immutable terminal states, audit integrity, portable lock contention/release, UTF-8 audit round trips, atomic duplicate import, historical snapshots, guarantee date boundaries, and reconciled weekly counts. No external network or service is used by tests.

`make_sample.py` regenerates the fictional input/final-register JSON fixtures; it does not build the audited event store. `demo` builds the event store through workflow transitions. Keep fixtures unchanged when comparing the included workbook and report.

## Display terminology and schema compatibility

The visible terms are **Requester**, **nonstandard terms** and **Request ID**. The existing JSON keys `requestor_id`, `exceptional_terms`, `id` and `ageing_days` are retained for schema compatibility; they represent Requester ID, the nonstandard-terms flag, Request ID and aging in days. Synthetic actor identifiers use `requester_001` naming.
