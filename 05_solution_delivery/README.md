# Migration quality: make the release decision inspectable

Ingrid Kao

At Lawsnote, I validated more than 10,000 contract records through field mapping and import checks. This local sample applies that method to eight fictional records. It compares an XML source with an independently supplied JSON destination export.

## The decision in one minute

| Batch | Source / destination | Clean | Held | Exception types | Next action |
|---|---:|---:|---:|---:|---|
| Flawed | 8 / 8 | 3 | 5 | 4 | Correct and retest |
| Corrected | 8 / 8 | 8 | 0 | 0 | Obtain record-owner signoff |

The four planted defects are a missing owner, a shared destination ID affecting two source records, an impossible date and a stale revision. Every exception identifies the source record, field, expected and actual values, owner and next action. The corrected batch clears these metadata checks; it does not authorize release.

**Inspect:** [flawed report](results/flawed_summary.md) · [corrected report](results/corrected_summary.md) · [pilot decision](Pilot_Decision_Brief.md) · [machine-readable results](results/demo_facts.json)

## Run it

Python 3.10 or later; standard library only. No credentials or installation are needed.

```sh
python3 migration_demo.py
python3 test_migration.py
python3 verify_demo.py
```

These commands also work by absolute path from another directory. `--output /your/local/folder` writes reports somewhere else. The checker does not modify source or destination fixtures.

The 30 executed tests cover record identity as well as counts, independently changed target values, case-insensitive destination collisions, owner and access metadata, real dates, revisions, exact decimals, null versus zero and unsafe XML. These are seeded examples and control tests, not estimates of production accuracy.

## What is checked

| Source | Destination | Decision rule |
|---|---|---|
| `@id` / `@revision` | `source_record_id` / `source_revision` | Every source appears once; revision matches |
| Source-to-destination crosswalk | `repository_record_id` | Unique after trimming and case folding |
| `owner` | `business_owner` | Required, named and unchanged |
| `signed_on` / `expires_on` | `signed_date` / `expiry_date` | Real ISO dates, correct order and exact source match |
| `amount_usd` | `value_usd` | Exact decimal string; unknown stays null; zero stays known |
| `visibility_group` | `access_group` | Approved group and exact source match |

The source parser accepts UTF-8 XML only and rejects DTD/entity declarations, repeated mapped fields and unexpected records. Metadata access checks do not test the destination platform's actual permissions.

## Evidence and files

- [field_mapping.json](field_mapping.json): mapping, nullable amount policy and approved access groups.
- [fixtures/source_contracts.xml](fixtures/source_contracts.xml): authoritative source snapshot.
- [fixtures/target_flawed.json](fixtures/target_flawed.json) and [fixtures/target_corrected.json](fixtures/target_corrected.json): independent destination snapshots.
- [migration_demo.py](migration_demo.py): comparison and JSON/CSV/Markdown reporting.
- [test_migration.py](test_migration.py): executable control tests.
- [results/](results/): source normalization, exception records and before/after decisions.

The fictional source contains seven stated amounts totaling USD 622,000.50 and one unknown amount. That is a source-register total, not a transaction outcome or a savings claim. Actual document completeness, permissions, retention and production change approval remain separate release gates.
