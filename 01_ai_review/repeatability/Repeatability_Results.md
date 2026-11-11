# Repeated NDA Review | Observed Results

Ingrid Kao | 11 November 2026

## Same request. Three observed batches.

15 synthetic NDAs reviewed three times; findings checked against source text and reviewed reference labels.

The three isolated agent batches received the same frozen prompt, policy, schema and source documents. Reference labels were excluded from reviewer inputs. Each batch reviewed all 15 documents in a shared context: 45 document reviews in total.

| Batch | TP / FP / FN | Precision | Recall |
| --- | --- | --- | --- |
| A | 16 / 0 / 0 | 100% | 100% |
| B | 16 / 0 / 0 | 100% | 100% |
| C | 16 / 0 / 0 | 100% | 100% |

### Consistency and correctness are separate

All 16 of 16 positive reference issues had supported matches in every batch. Detection decisions agreed across 225 document-rule opportunities: 16 positives and 209 negatives. No unstable positive detection was observed. These are issue instances; the policy has 15 rule types.

### What the scorer verified

A true positive requires the expected document-rule pair and an exact quotation in its stated Section. All 48 finding occurrences passed source and locator checks. No severity, route or source-status differences were observed, and every result retained the required human-review flag. Zero denominators return undefined, rather than a perfect score.

### Execution boundary

The runtime did not expose a model ID, snapshot or sampling settings. These are three isolated Codex agent batches, not 45 separately logged API requests or a fixed-version provider benchmark. The original held-out partition was reused; it is not a new unseen validation set. No population-accuracy estimate or confidence interval is inferred.

Decision: retain the result as a reproducible local demonstration. Before a production pilot, pre-register a fixed provider/model configuration, fresh representative agreements, error thresholds and reviewer decisions. Preserved responses, input hashes, per-run metrics and issue-level consistency are included beside this brief.

