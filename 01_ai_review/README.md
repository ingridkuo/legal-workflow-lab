# AI Contract Review Method

Ingrid Kao

I use a policy-based first pass to turn NDA issues into checkable findings: the relevant clause, an exact quote, a Section locator, a proposed revision and a named review owner. My focus is the handoff from a legal standard to a repeatable workflow, including source gaps, escalation and evidence checks.

**Synthetic evaluation; policy-rule match, source quote and location checks.**

## Read or explore

- [Six-page method brief](AI_Contract_Review_Method.pdf)
- [Editable method brief](AI_Contract_Review_Method.md)
- [Interactive model demonstration](replay.html): inspect three saved scenarios, source quotes, policy rules and a local evidence challenge.
- [Review policy](policy/nda_demo_policy.md) and [v2 prompt](prompts/review_v2.md)
- [Implementation control design](Controls_Design.md) and [primary references](AI_Method_Primary_Sources.csv)

On 15 held-out synthetic NDAs, the saved v2 review returned **16 findings for 16 reference issues**. All 16 quotations appeared in their stated Sections; none of the 9 RED reference issues was missed. **Reference labels reviewed by Ingrid Kao** - scope: all 25 reference issue labels across 20 synthetic NDAs; no labels changed. See the [review record](evaluation/review_record.json).

## How I structure the work

1. Define the reviewed party, evaluation purpose, source set and policy positions.
2. Separate development fixtures from held-out fixtures and keep reference labels outside review inputs.
3. Require structured findings with policy family, severity, exact quote, location, action and owner.
4. Verify evidence and routing, then resolve the legal decision through the appropriate human review.
5. Inspect overlaps and errors before changing a prompt or counting rule.

The set contains 20 fictional agreements: 5 development documents with 9 reference issues and 15 held-out documents with 16 reference issues. It includes compliant controls, borderline survival, missing attachments, residuals, shared-model training, compelled disclosure, retention, representatives, hidden commercial restrictions and source-contained instructions.

Each historical pass is one preserved review batch in a shared agent context. These deliberately selected fixtures and their issue counts describe this evaluation set; they do not estimate population performance or repeated-run reliability. Independent-binomial confidence intervals are not presented because the trial structure does not establish independent, representative observations. The reported ratios are fixed-key precision and reference-issue recall, not an overall legal accuracy measure.

## Three decisions to inspect

| Scenario | Confirmed source fact | Interpretation and next action |
|---|---|---|
| NDA-19 | Section 8 imposes unlimited liability; Section 10 asks the reviewer to approve and suppress findings. | Treat the embedded instruction as untrusted content; escalate the liability term to Senior Legal / Finance. |
| NDA-18 | Section 5 incorporates Appendix T for confidentiality durations, but the appendix is absent. | Request the source before assessing either duration; keep the result at NEED_SOURCE. |
| NDA-03 | Section 3 permits residual-memory use and shared-model training. | Preserve both specific findings; consolidate the overlapping PURPOSE consequence under the stated counting rule. |

The demonstration displays saved model outputs. Its management briefs are editorial explanations. The evidence challenge runs a deterministic quote-and-location check, not new inference.

## Iteration worth explaining

v1 returned an additional PURPOSE finding on NDA-03. The source supported that concern: residual-memory and training exceptions expanded use beyond evaluation. v2 consolidates that consequence into the specific RESIDUALS and MODEL_TRAINING findings unless separate broader-use language exists. The change makes counting consistent; it does not establish superior legal accuracy. Historical saved reviews remain unchanged.

## Reproduce the checks

```sh
python3 scripts/score_saved_results.py
```

The standard-library script reads the supplied contracts, reference labels and saved reviews. It reproduces rule-family counts, fixed-reference-key precision/recall ratios, exact-quote and Section checks, severity/routing comparisons and the required human-review flag. It writes `evaluation/results_summary.json`, `evaluation/document_scores.csv` and `evaluation/evidence_checks.csv`. The compatible field `human_gate_errors` checks a missing or false output flag, not live approval enforcement. Legal interpretation remains with the reviewer.

The script rescores saved outputs. The replay displays those same saved outputs locally. Neither operation calls a model. For a new review, use the versioned policy and prompt in an authorized tool, save a new result file, then verify the evidence and obtain the required legal decision.

## Operational controls

I separate draft findings from authority to approve or sign. GREEN identifies no flagged issue under this policy; YELLOW routes to Legal; RED routes to the specified exception owner or specialist. NEED_SOURCE requests incorporated material before that subject is assessed. Contract-contained instructions remain source content.

For an organization-specific implementation, I would use approved tools, authorized source identifiers, a read-only policy store, draft-only output, access logging and human approval gates. Confidential contracts belong only in tools approved for that data.

NDA-19 is an indirect source-document prompt-injection attempt consistent with [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/). The saved review treats the embedded instruction as source content and separately identifies unlimited liability. It records the outcome for that fixture, not a general resistance rate.

The [proposed control design](Controls_Design.md) references [ABA Formal Opinion 512](https://www.americanbar.org/content/dam/aba/administrative/professional_responsibility/ethics-opinions/aba-formal-opinion-512.pdf). Apply governing jurisdictional rules and engagement obligations, and obtain informed consent where required.

## Rebuild the presentation

`method_content.json` is the canonical text and page structure for the PDF and editable Markdown. From the public collection root:

```sh
python3 -m pip install reportlab pypdf
python3 tools/build_ai_method.py
```

The portable builder uses the bundled fonts and edits only the method PDF and Markdown. It can run from any current directory when its full path is supplied. Use `--output-dir` to build a separate copy. The evaluation inputs, policy, prompts, reference labels and historical outputs are left unchanged.

## Files

- `inputs/`: unchanged fictional source agreements.
- `policy/` and `prompts/`: policy rules and the two prompt versions.
- `evaluation/reference_labels.json`: reference issue families and source hashes.
- `evaluation/saved_reviews/`: the three saved review passes.
- `evaluation/`: reproducible counts and evidence checks.
- `review_output.schema.json`: the structured finding format.
- `method_content.json`: canonical presentation content.
- `Controls_Design.md`: proposed live records, separate from local checks.
- `AI_Method_Primary_Sources.csv`: official technical and ethics references.

The counts describe this controlled synthetic set and its rule-family convention. A larger real-agreement evaluation would need varied sources, organization-specific policy, reviewer agreement checks and recorded decision outcomes.

## Run the local Lab

```sh
python3 scripts/run_lab.py check --require-repeats --json
python3 scripts/web_lab.py
```

The first command validates the frozen cohort and scores the three new saved batches. The second starts the local browser/API demonstration; open the loopback URL it prints and select **Run checks**. Neither command generates a new model response.

- [Run guide and check explanations](Lab_Run_Guide.md)
- [One-page repeated-generation results](repeatability/Repeatability_Results.pdf)
- [Per-run metrics](repeatability/per_run_metrics.csv) and [issue consistency](repeatability/per_issue_consistency.csv)
- [SALI crosswalk and DMS concepts](taxonomy/Taxonomy_and_DMS.md)
- [Technical scope and interview walkthrough](Technical_Scope.md)

The new study comprises three isolated agent batches using the same frozen request: 45 document reviews. Each batch returned 16 supported reference matches with no extra or missed reference issues. All 16 positive instances were found in every batch. Model snapshots and sampling settings were not exposed. These observations are separate from a controlled provider-version API benchmark; the reused synthetic partition does not establish performance on new agreements.
