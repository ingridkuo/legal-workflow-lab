# Legal AI Output Gates and Escalation Workflow

Ingrid Kao | Legal technology and operations study.

This small Python and SQLite implementation makes two kinds of control inspectable: whether a proposed review output has the required fields and links to its cited source, and whether a legal-program case has the records needed for closure. It is an executable demonstration, not a description of a deployed employer system.

## Scope and evidence status

All candidate outputs, contract clauses, requests, identities, evidence references, timestamps and decisions are deliberately authored synthetic fixtures. No client or employer records appear in this package. No model was called. The candidate-output fixtures are test inputs written to exercise known behaviors, not sampled AI responses.

The included run uses 16 output fixtures on one fictional source document containing four numbered clauses, plus 12 workflow scenarios. A matched expected outcome is a software-control check. It is not model accuracy, legal accuracy, a measured reduction in hallucinations, an operational service-level result or evidence of production adoption.

The program uses Python's standard library only. It sends no email, makes no network or model calls, and does not delete, release or disclose evidence. Role names passed to methods simulate authority boundaries. They do not authenticate people and are not enterprise access controls.

## Run the demonstration

Use Python 3.10 or later. No installation or account is required.

    cd toolkit
    python3 run.py

The runner reads the checked-in configuration, mapping, source document and fixture files. It recreates its own outputs/operations.db and writes eight output artifacts. Any mismatch against a fixture's expected gate or workflow behavior raises an exception and returns a nonzero exit status.

For a repeatability check:

    python3 run.py --regression

This runs twice in fresh temporary directories and compares all eight generated artifacts byte for byte in that runtime. It does not overwrite the normal outputs directory. Cross-version SQLite database byte identity is not promised.

To write another output directory:

    python3 run.py --output-dir /tmp/legal-demo-output

To regenerate the same deliberately authored fixtures from their source script:

    python3 make_fixtures.py
    python3 run.py

Review fixture changes before changing expected outcomes. A changed answer key is not itself a successful repair.

## Package contents

| File | Purpose |
| --- | --- |
| run.py | Gate implementation, SQLite workflow, scenario checks and report generator |
| config.json | Allowed review rules and severity values, routing choices, quote limit and illustrative case review/completion target hours |
| canonical_field_mapping.json | Explicit external JSON field names mapped to canonical case fields |
| reporting.sql | The actual queries read and executed by the report generator |
| make_fixtures.py | Reconstructs the deliberately authored fictional fixture files |
| fixtures/source_documents.json | One versioned four-clause source, canonical text and SHA-256 |
| fixtures/output_cases.json | Sixteen candidate-output cases and expected mechanical gates |
| fixtures/external_intake.json | Twelve fictional intake payloads in the external field format |
| fixtures/workflow_scenarios.json | Twelve named workflow scenarios |
| outputs/validation_results.csv | One observed result per output fixture |
| outputs/workflow_results.csv | One observed result per workflow scenario |
| outputs/metrics.json | Computed counts, scope labels and explicit nulls for unmeasured outcomes |
| outputs/operations.db | Case register and audit-event table |
| outputs/operations_report.json | Structured SQL-derived state, owner, overdue and preservation reports |
| outputs/report.md | Readable results and limitations |
| outputs/fixture_manifest.json | SHA-256 values for configuration, mapping and the four fixture files |
| outputs/execution_manifest.json | SHA-256 values for the runner, SQL and fixture manifest |

## Output gate

The gate expects exactly these string fields:

    document_id
    source_version
    source_sha256
    rule_id
    severity
    clause_id
    quote
    proposed_action

It rejects missing or additional fields, incorrect field types, unknown rules, unknown severity values, a missing source, a mismatched version or source hash, an empty or oversized quotation, and a quotation absent from the cited clause. The source-document index is checked against its canonical text before cases run. Source hashing identifies the pinned input; it does not prove the source is legally authoritative, complete or appropriate to the task.

The quote limit of 180 characters is a demonstration setting. The rules NDA_SCOPE, RETENTION and SOURCE_INSTRUCTION are illustrative review categories, not approved negotiation positions. Each rule has HUMAN as its configured decision authority.

| Gate | Meaning |
| --- | --- |
| BLOCKED | The output fails a mechanical gate. It cannot enter the proposed review queue as a validated record. |
| MANUAL_REVIEW | The specific synthetic refusal envelope supplies no analysis; route the work to a person. |
| READY_FOR_HUMAN_REVIEW | Required fields and source-linkage checks pass. A person must still assess interpretation and action. |

The refusal envelope is a local demonstration adapter, not a claim about any vendor's wire format. A real integration would need to map the chosen API's response, refusal, transport-error and timeout states.

Q02 quotes instruction-like language from the fictional source. The gate only treats it as a string; it never sends a message or executes a command. This demonstrates inert handling in this code path. It is not a general prompt-injection defense or a test of how a language model would react.

Q16 is the essential negative semantic control. Its authentic quotation permits disclosure to advisers for a stated purpose, while the proposed interpretation treats it as an absolute ban. The record passes the mechanical gate and enters human review. Its REJECT_BY_DESIGN label is an authored answer key. No independent human adjudication was performed, and no substantive accuracy percentage is reported.

## Intake mapping and routing

The external JSON adapter maps nine allowed fields to canonical names. Unexpected or missing input keys are rejected. Input types, category, priority, visibility, time format and the short-summary length are checked. The short-summary field is not a de-identification system: real deployment would need appropriate data access, retention, redaction and incident procedures.

Each accepted request receives a stable case ID. An identical payload under the same idempotency key returns the existing case, without duplicating it or overwriting current work. A changed payload under that key raises IDEMPOTENCY_CONFLICT and records a conflict event. A source update uses a separate explicit method.

Routing configuration suggests an operational owner. The coordinator still assigns that owner, and the named owner accepts the handoff. The program rejects a recorded legal decision until both are present. The case coordinator cannot record a counsel decision by supplying the coordinator role name.

The fixed simulation clock is 2026-11-10T12:00:00Z. Configured 48-hour normal and 12-hour high-priority values are illustrative CASE REVIEW/COMPLETION targets measured from synthetic created_at values. They are not acknowledgment targets, legal deadlines or employer SLAs. No human response or review duration was measured.

## Authority and transition controls

| Action | Simulated authority | Required record or control |
| --- | --- | --- |
| Intake, assignment and closure coordination | program_coordinator | Valid mapped input; explicit owner; closure checks |
| Accept operational handoff | Named action owner | Exact configured owner string |
| Record legal decision | counsel | Accepted operational owner, decision reference and current source version |
| Record execution receipt | Named action owner | Accepted handoff and a current required counsel decision |
| Request preservation review | program_coordinator | Marks a request pending; does not make a legal determination |
| Decide preservation status | counsel | Decision reference; active or released disposition |
| Accept ongoing preservation follow-up | Named preservation custodian | Accepted owner and a future next-review date for closure |

Recorded states are new, assigned, awaiting_counsel, ready_to_execute, pending_confirmation, blocked and closed. A source-version change clears the prior decision and execution receipt and returns the case for counsel review. Ordinary ownership, decision and execution methods reject already-closed cases; an explicit source change can reopen the case for review. Repeating an already-completed close is idempotent.

Closure requires an action owner, accepted handoff, a current required legal decision, and a current execution receipt. Pending preservation review blocks closure. An active preservation commitment does not have to be released to close the operational case, but its custodian must accept ongoing responsibility, its decision must be referenced and its next review must be in the future. The active commitment remains visible in reporting after case closure. No evidence deletion follows closure.

The prototype checks presence and source-version alignment of decision and receipt references. It does not dereference external evidence, authenticate signers, assess whether a decision is legally sound, or verify that an action actually occurred. Those are production integration and review requirements, not demonstrated capabilities.

## Executed workflow scenarios

| Scenario | Control exercised |
| --- | --- |
| W01 valid close | Required handoff, decision and receipt permit closure |
| W02 missing owner | Premature legal decision rejected and closure blocked |
| W03 unaccepted handoff | Premature legal decision rejected and closure blocked |
| W04 missing approval | Coordinator cannot supply a counsel decision; closure blocked |
| W05 missing receipt | A decision alone is not evidence of completion |
| W06 pending preservation | Unresolved preservation review blocks closure |
| W07 active preservation without accepted custodian | Ongoing obligation lacks accepted ownership |
| W08 active preservation with accepted custodian | Case closes while the separate commitment stays active |
| W09 identical duplicate | Existing case reused without duplication |
| W10 conflicting duplicate | Conflicting content rejected and recorded |
| W11 source change | Prior decision and execution receipt invalidated |
| W12 overdue report | Fixed-clock SQL report identifies the overdue open case |

## Reading the observed results

The checked-in run matched expected behavior on 16 of 16 gate fixtures and 12 of 12 workflow scenarios. The gate sent three fixture outputs to human review, one refusal to manual review and blocked twelve. One intentionally unsound interpretation remained among the three queued outputs.

The twelve synthetic cases finish as two closed, seven blocked and three assigned. One nonclosed case is overdue against the illustrative target. One closed case retains an active preservation commitment with an accepted custodian and a future review date. The database contains 62 recorded audit events. Counts are computed from results and database rows, not used as substitute labels for model quality.

The SQL file creates reports by state and owner, lists overdue open cases and exposes pending or active preservation commitments. The synthetic age of an open matter is a difference between authored dates, not observed analyst effort. The owner summary distinguishes open workload from all historical cases.

## Before adapting the pattern

A real pilot would need an approved business purpose and review standard, a representative and appropriately accessible evaluation set, independently adjudicated substantive answers, a model and prompt version, integration/error-path tests, least-privilege enterprise identity controls, configured service targets, user testing and measured verification effort. Costs and benefits would need actual observations before a deployment or ROI claim.

This package demonstrates a narrow, inspectable implementation and its fixture-level behavior. It does not establish production reliability, legal compliance, security certification, end-user adoption, or that any named employer or vendor uses this workflow.
