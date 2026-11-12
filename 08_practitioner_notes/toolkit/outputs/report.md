# Reproducible demonstration results

Independent legal technology work sample. All records and candidate outputs are deliberately authored synthetic fixtures. No model calls or employer data.

Fixed simulation clock: 2026-11-10T12:00:00Z

## Executed checks

| Check group | Cases | Matched expected outcome |
| --- | ---: | ---: |
| Output gate fixtures | 16 | 16 |
| Workflow scenarios | 12 | 12 |

Output gate counts: BLOCKED=12, MANUAL_REVIEW=1, READY_FOR_HUMAN_REVIEW=3.

The deliberately unsound interpretation in Q16 passed the mechanical gate and remains in the human-review queue. Its REJECT_BY_DESIGN label is an authored answer key, not an independent human adjudication or a measured model error.

## Synthetic case states

| State | Count |
| --- | ---: |
| assigned | 3 |
| blocked | 7 |
| closed | 2 |

Total cases: 12. Overdue nonclosed cases at the fixed clock: 1.

## Cases by operational owner

| Owner | Cases | Open cases |
| --- | ---: | ---: |
| UNASSIGNED | 1 | 1 |
| contract_operations | 8 | 7 |
| user_operations | 3 | 2 |

## Overdue cases

| Case | Due at UTC | Synthetic age in hours |
| --- | --- | ---: |
| CASE-W12 | 2026-11-07T10:00:00Z | 122.0 |

## Ongoing preservation commitments

| Case | Case state | Preservation | Custodian | Accepted | Next review UTC |
| --- | --- | --- | --- | --- | --- |
| CASE-W06 | blocked | pending | Unassigned | 0 | Not set |
| CASE-W07 | blocked | active | records_custodian | 0 | 2026-11-17T12:00:00Z |
| CASE-W08 | closed | active | records_custodian | 1 | 2026-11-17T12:00:00Z |

Closing CASE-W08 leaves its accepted preservation commitment active. Nothing in this prototype destroys or releases evidence.

## Interpretation limits

These checks establish only that this implementation behaves as authored on this small fixture set. They do not measure LLM accuracy, hallucination rates, semantic correctness, production reliability, prompt-injection immunity, enterprise identity controls, user adoption, human response time, legal compliance, or ROI. Illustrative case review/completion targets and synthetic ages are not legal deadlines or observed service levels.
