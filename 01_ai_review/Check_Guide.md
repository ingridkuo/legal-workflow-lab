# Run the NDA Lab and explain its checks

This harness is the small program that loads the agreements, validates saved reviews, scores findings and writes a result a reviewer can inspect. It runs locally with Python 3.10 or later and the standard library. No account, network connection or API key is needed for these checks.

From the public portfolio folder:

```sh
python3 01_ai_review/scripts/run_lab.py check --require-repeats --json
python3 01_ai_review/scripts/test_run_lab.py
```

The first command validates the archived reviews and three new independent agent batches, then writes the repeatability tables. The second deliberately introduces failures to test the evaluator. Neither command asks a model to review a contract. Successful local execution does not establish that a model would return the same answer again.

## What each check protects

| Check | What the program does | Why it matters |
|---|---|---|
| Source identity | Compares each of 20 agreement hashes with its reference record. | A score must belong to the document that was actually labeled. |
| Frozen request | Checks the request hash, prompt, policy, output schema and the 15 supplied held-out documents against their recorded versions. | Prompt or input changes must not be disguised as repeats. The request file contains no answer-key field. |
| Output structure | Applies every keyword used by the bundled JSON schema: required fields, types, permitted values, constants, patterns, nonempty strings and extra-field restrictions. An unsupported schema keyword fails explicitly. | Reject malformed or silently expanded outputs before scoring them. This is a validator for this schema's subset, not a general-purpose JSON Schema engine. |
| Document coverage | Requires every expected document exactly once, with no unexpected document. | Dropping a difficult document must not improve the reported result. |
| Rule identity and counting | Requires the correct policy, permitted rule IDs, and one finding per document/rule pair. | Duplicate findings must not create extra true positives. The policy has 15 rule types; the held-out key has 16 positive issue instances. |
| Exact quotation | Looks for each quoted span in the source agreement without fuzzy matching. | An invented quote cannot support a matched issue. This tests textual support, not whether the legal reasoning is sound. |
| Section locator | Requires the same quote in the stated Section. | A real quote attributed to the wrong clause is still defective evidence. |
| Severity and routing | Checks that the returned route equals the highest returned severity. Separately compares issue severity, route and locator with the reference key. | A correct rule flag can still produce the wrong escalation. These differences remain visible rather than being hidden in one accuracy number. |
| Source status | Requires NEED_SOURCE when SOURCE_COMPLETENESS is returned; otherwise REVIEW_READY. Separately compares status with the reference. | A missing appendix must lead to a source request, not an invented conclusion. |
| Human-review gate | Requires human_review_required to be true in every result. | A GREEN route is not signature authority or legal approval. |
| Cohort integrity | Records hashes of the frozen request, key, policy, schema, prompt and all three saved batches. Subsequent scoring rejects changed bytes. | A later edited answer cannot silently replace the measured output. New experiments belong in a separate study. |

## Read the results

- `repeatability/results_summary.json`: batch totals, consistency counts and execution limits.
- `repeatability/per_run_metrics.csv`: TP, FP, FN, precision and recall for each of the three batches. Ratios use 0–1; null/blank means undefined.
- `repeatability/per_issue_consistency.csv`: all 225 document/rule opportunities: 16 reference positives and 209 reference negatives. Each batch has separate presence and source-supported detection columns.
- `repeatability/per_document_checks.csv`: source, Section, severity, route and source-status differences for each document in each batch.
- `repeatability/scored_cohort_manifest.json`: hashes identifying the scored inputs and unmodified batch outputs.
- `repeatability/Repeatability_Report.md`: a short management-facing account of the measured result and its practical limits.

A true positive is a returned document/rule pair matching the key **and** supported by an exact quote in its stated Section. A returned but unsupported finding counts as FP; if the expected issue has no supported match, it also remains FN. A reference-negative flag is FP under this key even when its quote is real; the score alone does not decide whether an attorney might identify a different valid concern.

Precision = TP / (TP + FP). Recall = TP / (TP + FN). No findings means precision is undefined. No reference positives means recall is undefined. Three identical misses count as stable **and** wrong. Presence agreement does not measure identical wording, confidence or legal correctness.

## What was actually repeated

Three independent reviewer agents received the same frozen prompt, policy, schema and 15 synthetic agreements without the reference labels. Each produced one batch of 15 review objects: 45 document reviews. The agents were instructed not to open other files or reference results. The runtime does not expose the model snapshot, temperature, seed, token budget or provider request IDs; those values are not invented. Document review within a batch shares that batch's context.

The existing development/held-out partition was reused; this is not a fresh unseen validation set. For a controlled API study, select and record an explicit model/version and supported settings, submit each document independently three times, preserve raw requests/responses and request IDs, then score a separate cohort against the unchanged key.

## Explain the engineering work accurately

The repository demonstrates executable Python evaluation logic, schema and evidence checks, structured JSON/CSV outputs, failure-oriented tests, and a repeatable local command. The optional local web application adds a browser interface and Python HTTP backend around this harness. Describe that artifact as a **local full-stack prototype** when discussing it. Deployment hardening, production integrations and controlled API inference require separate evidence; this Lab does not establish those claims.
