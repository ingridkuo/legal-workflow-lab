# Run the Legal Review Lab

Ingrid Kao

Python 3.10 or later; no package installation, account or API key is needed for the local checks.

## 1. Open the local interface

From this folder:

```sh
python3 scripts/web_lab.py
```

Open the loopback URL printed by the command. Select **Run checks**. The browser sends a fixed request to the local Python API; the service validates and scores the preserved results and returns JSON. Stop the server with Ctrl+C.

Opening `web_lab.html` by double-clicking cannot start the Python service. The older `replay.html` remains a separate browser-only exhibit of source clauses and recorded findings.

## 2. Run the same checks in the terminal

```sh
python3 scripts/run_lab.py check --require-repeats --json
python3 scripts/test_run_lab.py
python3 scripts/test_web_lab.py
python3 taxonomy/validate_taxonomy.py
```

The main command checks the three frozen batches and preserves their input/output identity. It does not generate new model responses. The tests deliberately supply invalid data to verify that the controls detect defects.

## 3. Explain the result

- [Every validation check, its purpose and failure behavior](Check_Guide.md)
- [One-page repeated-generation results](repeatability/Repeatability_Results.pdf)
- [Per-run precision and recall](repeatability/per_run_metrics.csv)
- [All 225 document/rule detection decisions](repeatability/per_issue_consistency.csv)
- [SALI mapping and DMS design](taxonomy/Taxonomy_and_DMS.md)
- [Technical scope and a short interview walkthrough](Technical_Scope.md)

The 16 positive reference instances are distributed across 15 documents; the policy has 15 rule types. Three new isolated agent batches reviewed the same frozen sources without reference labels in their inputs. The runtime did not expose model snapshots or sampling settings. Treat the result as a repeated-generation work sample, not a fixed-provider benchmark or production-accuracy estimate.
