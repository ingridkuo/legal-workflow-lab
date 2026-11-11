# Contract metadata pilot: proceed to signoff, hold release

Ingrid Kao | Fictional demonstration

**Recommendation:** send the corrected batch to the record owner for signoff. Hold production release until documents, access, retention and change approval have been checked in the chosen system.

## Confirmed in the executed example

| Check | Flawed export | Corrected export |
|---|---:|---:|
| Source / destination records | 8 / 8 | 8 / 8 |
| Clean / held records | 3 / 5 | 8 / 0 |
| Exception types | 4 | 0 |
| Release authorized by validator | No | No |

The four seeded defects are a missing owner, a destination ID collision, an impossible date and a stale revision. Counts and source identities reconcile in both fixtures. A count match alone would not detect a missing record replaced by a duplicate; the checker tests identity separately.

Thirty behavioral tests pass, including independent target edits, null versus zero and rejection of DTD/entity XML. The results support a demonstration of these controls on the supplied fixtures. They do not measure production error rates or financial savings.

## Decision rights

| Gate | Evidence | Owner |
|---|---|---|
| Source coverage and mapping | Every expected source ID appears once; fields and current revisions reconcile | Data steward |
| Exception disposition | Each discrepancy has a named owner, correction and retest result | Legal operations |
| Document usability | Correct signed file opens; attachments are complete | Record owner |
| Access and retention | Authorized access works; unauthorized access fails; retention is configured | System owner and Legal |
| Release | All acceptance evidence is recorded and the owner signs off | Project owner |

The local validator covers source coverage and metadata quality. An exported `access_group` value is evidence of metadata fidelity, not proof that access restrictions work.

## Proposed pilot measures

Record unresolved exceptions by owner and age, recurrence after correction, user task completion, and observed review/correction minutes. Collect a defined baseline and comparable pilot data before calculating time savings, percentages or a staffing business case.

**Next action:** the project owner records a signoff decision after the remaining gates are complete. Preserve the source snapshot, corrected destination export and exception history together.
