# Saved synthetic NDA review: evidence and counting conventions

This folder preserves one Codex delegated-agent review of eight fictional NDA fragments, identified as **A01–A08**. It is separate from the authored software fixtures in `../toolkit` and the original 20-NDA evaluation in the repository’s `01_ai_review` folder.

## Results at a glance

| Measure | Saved result | Unit |
| --- | ---: | --- |
| Documents reviewed | 8 | A01–A08, one saved batch |
| Finding rows | 8 | Document-and-rule labels |
| Source metadata and exact quotations matching | 8 of 8 each | Mechanical evidence checks |
| Original provisional reference pairs present | 6 of 6 | Preserved pre-run key |
| Revised source-supported reference matches | 8 of 8 | Author-adjudicated document-and-rule key |
| Distinct flagged clauses and actionable issue groups | 6 | Overlapping PURPOSE and RESIDUALS labels grouped by clause |

All eight revised reference pairs have matching source evidence, with no unsupported returned pair or missing supported reference pair. Ingrid Kao’s author adjudication was made after reviewing the saved response and is not independent. These agreement counts describe this batch; precision, recall, model accuracy, reviewer time, and population legal accuracy are not reported. The scorer retains explicit null values for those unreported rates and unmeasured outcomes. No additional model review was run.

## Resolution of the two overlapping labels

The supplied [author adjudication record](adjudication_record.json) records the decisions, source quotations, reasons, date, and non-independent review status. The [earlier counting-convention record](adjudication_v1_1.json) remains unchanged, including the hashes of the original inputs. [The provisional key](provisional_answer_key.json) preserves the original six-pair reference unchanged. [The revised key](adjudicated_answer_key.json) retains source locators and issue groups and links the author record, adding PURPOSE on A04 and A06 for eight document-and-rule pairs.

Both memory-use clauses permit unrestricted use beyond evaluating Project Atlas. They therefore support PURPOSE and the more specific RESIDUALS label under the policy as written. The revised key retains both labels. An action-oriented summary groups them into one residual-use issue for each clause, with **RESIDUALS as the primary rule**, yielding six actionable issue groups. Priority affects aggregation, not whether a supported rule label is retained.

The author record proposes that a future policy version make this overlap explicit: RESIDUALS would govern unaided-memory use rights and PURPOSE would cover other use rights. That prospective wording is not applied retrospectively to this saved version-1 response. The source quotations, original response, original key, and both decision records remain inspectable.

The program checks consistency between the supplied adjudication record, revised key, and source clauses. It does not authenticate the adjudicator’s identity or turn this post-run author review into independent validation.

## Execution record

- Original run date: November 10, 2026.
- Recorded interface: Codex collaboration delegated agent, task `exploratory_nda_review`, with `fork_turns="none"`.
- Parent model identified in that session: GPT-6.1 Sol (`gpt-6.1-sol`). An immutable provider snapshot, sampling settings, and seed were not exposed.
- The original reviewer was instructed to read `documents.json` and `toy_policy.json`. Its task did not supply the provisional answer key.
- One response was collected and later saved without a second review.
- Full surrounding platform/system instructions were not exported. The record does not establish exact inference reproducibility or a controlled provider-version benchmark.

## Re-score and test

From the collection folder, using Python 3.10+:

```sh
python3 experimental_llm/evaluate_exploration.py
python3 -m unittest discover -s experimental_llm -p test_exploration.py -v
```

The scorer performs no inference and makes no network requests. It verifies frozen-input hashes, document coverage, source metadata, exact quotations, reference locators, overlap grouping, and the author record’s two additions. It writes `finding_evidence.csv`, `actionable_issue_groups.json`, and `exploration_metrics.json`. The 21 tests include wrong quotes, correct quotes at wrong locators, stale versions, missing and duplicate reviews, unexpected labels, grouping, source preservation, and malformed adjudication evidence or provenance.

## Files

- `documents.json`, `toy_policy.json`, `prompt.txt`: original sources, sponsor instructions, and task.
- `raw_model_response.json`: unchanged saved response.
- `provisional_answer_key.json`: unchanged pre-run key.
- `adjudication_v1_1.json`: preserved initial counting-convention rationale and original-input hashes.
- `adjudication_record.json`: supplied post-run author adjudication, explicitly non-independent.
- `adjudicated_answer_key.json`: revised eight-pair key, source locators, and six issue groups.
- `evaluate_exploration.py`, `test_exploration.py`: scorer and regression checks.
- `finding_evidence.csv`, `actionable_issue_groups.json`, `exploration_metrics.json`: regenerated results.

The fragments intentionally simplify complete agreements. The study does not measure production security, OCR, adoption, ROI, or realized savings. Simulated inputs and exact quotation matches remain separate from substantive legal correctness.
