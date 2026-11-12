# Saved synthetic NDA review: evidence and counting conventions

This folder preserves one Codex delegated-agent review of eight fictional NDA fragments, identified as **A01–A08**. It is separate from the authored software fixtures in `../toolkit` and the original 20-NDA evaluation in the repository's `01_ai_review` folder.

## Results at a glance

| Measure | Saved result | Unit |
| --- | ---: | --- |
| Documents reviewed | 8 | A01–A08, one saved batch |
| Finding rows | 8 | Document-and-rule labels |
| Source metadata and exact quotations matching | 8 of 8 each | Mechanical evidence checks |
| Original provisional reference pairs present | 6 of 6 | Preserved pre-run key |
| Revised source-supported reference matches | 8 of 8 | Adopted document-and-rule convention |
| Actionable issue groups | 6 | Overlapping PURPOSE and RESIDUALS labels grouped by clause |

The revised document-and-rule scorer returns eight supported true positives, no false positives and no false negatives. The revised key was adjudicated after inspecting the saved response; the original pre-run six-pair key is retained. This changes reference counting, not the model output or model behavior. Precision and recall are each 8/8 **for agreement with this revised toy key on this saved batch**. These counts are not a population legal-accuracy estimate. No additional model review was run.

## Resolution of the two overlapping labels

`adjudication_v1_1.json` records the adopted counting convention and the reasons for both changes. `provisional_answer_key.json` preserves the original six-pair key unchanged. `adjudicated_answer_key.json` adds PURPOSE on A04 and A06, producing eight document-and-rule reference pairs.

Both memory-use clauses permit unrestricted use beyond evaluating Project Atlas. They therefore support PURPOSE and the more specific RESIDUALS label. The revised key retains both labels. An action-oriented summary groups them into one residual-use issue for each clause, with **RESIDUALS as the primary rule**; this yields six independently actionable issue groups. Priority affects aggregation, not whether a supported rule label is retained. The source quotation, original response, original key and decision rationale remain inspectable.

The record documents a policy-based classification under the convention adopted for this revision. It does not record independent human or attorney validation. A different sponsor policy or evaluation unit would require a separately documented decision.

## Execution record

- Original run date: November 10, 2026.
- Recorded interface: Codex collaboration delegated agent, task `exploratory_nda_review`, with `fork_turns="none"`.
- Parent model identified in that session: `gpt-6.1-sol`. An immutable provider snapshot, sampling settings and seed were not exposed.
- The original reviewer was instructed to read `documents.json` and `toy_policy.json`. Its task did not supply the provisional answer key.
- One response was collected and later saved without a second review.
- Full surrounding platform/system instructions were not exported. The record does not establish exact inference reproducibility or a controlled provider-version benchmark.

## Re-score and test

From the collection folder, using Python 3.10+:

```sh
python3 experimental_llm/evaluate_exploration.py
python3 -m unittest discover -s experimental_llm -p test_exploration.py -v
```

The scorer performs no inference and makes no network requests. It verifies the frozen input hashes, document coverage, source metadata, exact quotations and reference locators, then writes `finding_evidence.csv`, `actionable_issue_groups.json` and `exploration_metrics.json`. The 18 tests include wrong quotes, correct quotes at wrong locators, stale versions, missing and duplicate reviews, unexpected labels, overlap grouping and preservation of the original records.

## Files

- `documents.json`, `toy_policy.json`, `prompt.txt`: the original sources, sponsor instructions and task.
- `raw_model_response.json`: the unchanged saved response.
- `provisional_answer_key.json`: the unchanged pre-run key.
- `adjudication_v1_1.json`: rationale, counting units and hashes of preserved inputs.
- `adjudicated_answer_key.json`: the revised eight-pair key and six issue groups.
- `evaluate_exploration.py`, `test_exploration.py`: scorer and regression checks.
- `finding_evidence.csv`, `actionable_issue_groups.json`, `exploration_metrics.json`: regenerated results.

The fragments intentionally simplify complete agreements. The study does not measure production security, OCR, reviewer time, adoption, ROI or realized savings. Simulated inputs and exact quotation matches remain separate from substantive legal correctness.
