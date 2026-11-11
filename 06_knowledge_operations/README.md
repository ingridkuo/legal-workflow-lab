# Knowledge operations: a handoff someone can act on

**Ingrid Kao | Synthetic demonstration | 10 November 2026**

This example turns an intake message into a short decision record: source facts, interpretation, unknowns, immediate next action and a named decision owner. A separate gate checks whether guidance is current and approved before it can be displayed to a permitted role.

Start with [the management handoff](Management_Handoff.md), then inspect [ESC-101](escalations/ESC-101.json) and [the executed results](results/summary.json).

## The decision that matters

The outside sender requests both preservation and an account export. Those requests take different paths under the fictional policy.

| Item | Recorded position |
|---|---|
| Source facts | The sender requests retention and an export; the sender states that no authorization document is attached. |
| Immediate preservation step | Ask the system owner to pause routine deletion for the named account pending Counsel review. Track acknowledgment; do not record the pause as completed without it. |
| Disclosure boundary | No disclosure or export until identity and authority are verified through an approved channel and Counsel approves the scope. |
| Decision owner | Fictional Counsel; Legal Intake owns the evidence packet and follow-up. |

ESC-102 compares a requester's proposed termination/refund conclusion with the supplied clause. ESC-103 routes a changed residuals clause out of the unchanged-template NDA process. Each record keeps exact source quotations next to its factual summary. Interpretations and open questions are separate fields.

## Guidance checked before use

| Article | Fixed result as of 10 November 2026 |
|---|---|
| KA-01: Records retention or export request | Eligible for its permitted roles |
| KA-02: Self-service NDA checklist | Blocked: draft, without approval or review dates |
| KA-03: Notice date calculation | Blocked: review overdue |

The gate checks article and source hashes, version, source sections, approval to that text and source snapshot, a separate approver, review dates, local file boundaries and the requested role. Escalations must use eligible guidance, retain exact source quotes, map every fact to a quote, name a separate reviewer and grant no disclosure, export or signing authority.

The quote check establishes that the cited words exist; a person still decides whether the summary and legal interpretation are correct. Roles and approval records are fixture inputs, not authenticated identities. All requests, policies, people and approvals are fictional. The program executes no preservation, disclosure, export or signing action.

## Reproduce

Python 3.10 or later; standard library only. From this folder:

```sh
python3 check_knowledge.py
python3 -m unittest discover -s tests -v
```

Both commands work from another working directory when their script/folder paths are supplied. The default run rewrites `results/` with the fixed date. `--as-of YYYY-MM-DD` prints a different-date evaluation without overwriting the saved results.

**Executed result:** 29 behavioral tests pass, with zero failures or errors. The fixed run selects one of three articles and validates all three escalation packets. Every packet retains named review; no result grants execution authority. Tests include changed evidence, unauthorized roles, stale and future dates, changed approval/source snapshots, path and symlink escape, unsupported facts, missing permission fields and a claimed preservation completion without acknowledgment.

Inspect [demo facts](results/demo_facts.json), [article checks](results/article_checks.json), [escalation checks](results/escalation_checks.json) and [test results](results/test_results.json).
