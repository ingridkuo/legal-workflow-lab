# Contract metadata migration check

Synthetic demonstration

Scenario: **flawed**. Source: **8 records**. Destination: **8 records**.
Clean: **3**. Held: **5**. Source identities reconcile: **True**.
Exception groups: **4**. Release status: **HOLD_FOR_CORRECTION**.

Validation does not authorize release. The record owner decides after resolving exceptions and checking documents and permissions.

| Issue | Source record | Field | Action |
|---|---|---|---|
| DUPLICATE_REPOSITORY_ID | LEG-001, LEG-003 | repository_record_id | Resolve the collision against the source-to-destination crosswalk; retain both source records. |
| REQUIRED_METADATA | LEG-002 | business_owner | Obtain the value from the source and record owner; do not fill it by guesswork. |
| INVALID_DATE | LEG-006 | expiry_date | Verify the source date; reject impossible or ambiguous date values. |
| SOURCE_REVISION_MISMATCH | LEG-008 | source_revision | Replace the stale destination revision after verifying the source version. |
