# Subcontract Workflow and Owner-Side Construction Issues

Ingrid Kao | Independent project | November 11, 2026

## Start here

1. Open `Ingrid_Kao_Subcontract_Workflow_Tracker.xlsx`. Start with **Weekly Report**, then review **Intake Register** and **Approval Rules**.
2. Make a practice copy. Change SC-001's amount from 50,000 to 50,000.01 to add Finance to the approval route. Change **Nonstandard terms** to Yes to require Senior Legal review.
3. Review due dates, guarantee expiry alerts and weekly counts. Yellow cells are editable; calculated fields use formulas.
4. Read the four-page workflow specification and the one-page owner-side construction issues comparison. The comparison cites AIA A201-2017 and the Taiwan PCC construction contract template dated December 30, 2025.

Excel contains editable demonstration records and live formulas. It does not authenticate approvers or create electronic signatures.

## Included files

- `Ingrid_Kao_Subcontract_Workflow_Specification.pdf`: fields, amount thresholds, nonstandard terms routing, signature order, date controls, reporting and connector mapping.
- `Ingrid_Kao_Subcontract_Workflow_Tracker.xlsx`: ten synthetic cases, editable policy controls, approval inputs, calculated next actions and a weekly scorecard.
- `Ingrid_Kao_Owner_Side_Construction_Issues.pdf`: one-page comparison of changes, delay, payment and termination, with proposed owner-side actions and official source links.
- `engine/`: working Python workflow engine, policy configuration, synthetic cases, event history, reports and tests.

## Run the workflow locally

Requires Python 3.10+. No third-party packages or API credentials are needed. On Windows use `py`; on macOS/Linux use `python3` instead.

Open a terminal in the `engine` folder. Create a practice event file so the original examples stay available:

```text
py workflow.py --db practice_events.jsonl demo
py workflow.py --db practice_events.jsonl verify
py workflow.py --db practice_events.jsonl show SC-001
```

Progress SC-001 through two reviews and the ordered demonstration signatures:

```text
py workflow.py --db practice_events.jsonl approve SC-001 --actor legal_001 --note "Terms reviewed" --at 2026-11-11T10:00:00Z
py workflow.py --db practice_events.jsonl approve SC-001 --actor pm_001 --note "Scope and budget confirmed" --at 2026-11-11T11:00:00Z
py workflow.py --db practice_events.jsonl sign SC-001 --actor sub_signatory_001 --at 2026-11-11T12:00:00Z
py workflow.py --db practice_events.jsonl sign SC-001 --actor company_signatory_001 --at 2026-11-11T13:00:00Z
py workflow.py --db practice_events.jsonl report --as-of 2026-11-11 --out-dir practice_exports
```

Try a company signature before the subcontractor signature or use an unassigned reviewer. The engine rejects the transition. See `engine/README.md` for guided intake, document holds, reassignment, event history and tests.

The supplied report uses the unchanged ten-case baseline: 2 received this week, 1 executed this week, 8 open, 3 overdue, 2 guarantees expiring within 30 days and 1 missing required guarantee. Your practice report changes after you approve or sign a record.

## What has been built

- A working local intake and approval state machine with role/order checks, document holds, UTC events and a hash-chain verification command.
- A formula-based Excel register and weekly report using the same starting examples.
- Local CSV/JSON exports and Slack-ready report text.

The workbook and engine share the initial fixture; later edits do not synchronize automatically. Make/Slack wiring, identity authentication, production storage and an eSignature service require connection and deployment in the account where they will be used. No live message has been sent.
