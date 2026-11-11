# NDA repeatability: three independent agent batches

**Scope.** The same frozen prompt, policy and 15 synthetic agreements were supplied to three independent reviewer agents. The request excludes the reference labels. Each agent returned one batch: 45 document reviews in total. This is an agent-session study; model snapshot and sampling settings are not exposed. It is not a fixed-version API experiment.

| Batch | TP | FP | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| run_a | 16 | 0 | 0 | 100.0% | 100.0% |
| run_b | 16 | 0 | 0 | 100.0% | 100.0% |
| run_c | 16 | 0 | 0 | 100.0% | 100.0% |

**Consistency.** 16 of 16 reference issue instances had a source-supported finding in all three batches. 0 positive issue detections changed across batches; 0 were missed in every batch. Across all 225 document–rule opportunities (209 reference negatives), 225 had the same flag-presence decision in every batch.

**Scoring.** A true positive requires a matching document/rule pair plus an exact quote in its stated Section. An unsupported returned finding counts as FP and leaves an expected issue as FN. Precision = TP/(TP+FP); recall = TP/(TP+FN). An empty denominator is undefined, not 100%. Severity, route and source-status differences are reported separately.

**Interpretation.** Agreement measures repeatability, not correctness: three identical misses are stable but wrong. These are synthetic, policy-bound examples; no new-contract, deployment or production-performance claim follows. Inspect per_issue_consistency.csv for all 16 positive instances and 209 negative opportunities, and per_document_checks.csv for evidence and routing differences.

**Next controlled study.** Use a pinned API model ID, record endpoint and sampling settings, submit each document independently three times, preserve raw responses and request IDs, and score without changing the frozen prompt or reference key. The present saved agent batches must remain a separate cohort.
