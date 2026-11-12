# Contract operations

I built this sample to connect contract intake with risk routing, delivery, acceptance, invoicing and renewal work. The workbook, database and local intake script use fictional records and proposed thresholds.

My platform experience includes DocuSign CLM and work with Ironclad workflows, approval logic and templates, including test workflows. This collection makes the underlying process decisions inspectable through local examples.

## Legal intake implementation case

Read [Legal Intake Implementation](Ingrid_Kao_Legal_Intake_Implementation_Case.pdf) for my work administering Jira Service Management intake and maintaining Confluence guidance. The second page provides illustrative configuration and acceptance checks.

## Explore the tracker

Open **Contract_Operations_Tracker.xlsx** and start with the Dashboard. Blue text marks editable inputs. Dark text marks calculated results. In Controls, change the As-of date, the review thresholds or the near-term window. Maintain the Contracts, Obligations and Compliance tables as work progresses.

The sample contains 24 contracts, 48 obligations and 12 illustrative calendar tasks. Known contract value totals **$2,141,498**; one contract value remains unknown. Two obligation rows allocate each contract budget 60% / 40%, so budget totals reconcile without double counting.

The proposed risk bands use inclusive thresholds: **$100,000 starts YELLOW** and **$250,000 starts RED**. Known critical risk takes priority over missing facts. Missing or invalid required inputs return NEEDS INPUT. The tracker’s GREEN risk band is separate from the stricter NDA workflow eligibility test in the intake script.

Calendar notice dates calculate only when the source, method and calendar-day basis are verified. Business-day terms require manual review. A COI supports insurance review; confirm the policy and endorsements. The calendar tasks are sample schedules rather than statutory deadline statements.

When adding records, extend the table formulas and the Dashboard’s bounded source ranges. Keep contract IDs stable so related obligations remain connected.

## Run the SQLite example

Python 3.10 or later is sufficient. The script uses only the standard library and runs from any working directory.

```bash
python3 database/build_database.py
```

This rebuilds `database/contracts_demo.sqlite` from `synthetic_data.json` and exports the six queries in `database/queries.sql` to CSV:

| Query | Operating question |
|---|---|
| q01 | Which renewal dates fall within 90 days? |
| q02 | Which values meet the review thresholds? |
| q03 | Which required insurance records need attention? |
| q04 | Which acceptance or payment milestones lack recorded completion? |
| q05 | Which notice dates need action or manual review? |
| q06 | Which budgets, invoices, payments or acceptance records show exceptions? |

Use `--as-of 2026-12-01` to change the reporting date. CSV exports use `\N` for SQL NULL; an empty field preserves an original empty string. Missing money remains unknown rather than becoming zero.

## Run the local intake example

Use Node.js 18 or later. No package installation is needed.

```bash
node automation/run_demo.js
node automation/test_triage.js
```

To route another structured request, copy `automation/demo_request.json`, edit its fields and pass its path:

```bash
node automation/run_demo.js my_request.json
```

`automation/normalize_request.js` converts plain-text input into the typed request accepted by `triage.js`. It rejects ambiguous currency formats rather than guessing. The policy-validation gate comes from explicit configuration, not an incoming answer.

The route reports the reviewer group and missing facts. Every non-NDA goes to Legal review. A routine unchanged NDA can be eligible for an approved workflow only after its policy, identity, authority and risk gates are satisfied. Signing approval remains a separate recorded decision.

The flow diagram shows how intake connects to that review and then to contract obligations. The scripts run locally and make no external service calls.
