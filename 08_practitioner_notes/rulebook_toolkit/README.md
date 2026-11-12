# Versioned Legal Review Rulebook

Ingrid Kao | Independent implementation sample. It makes the effect of a changed review instruction inspectable, using original fictional source clauses, deliberately authored fact annotations and two versioned sponsor policies.

The program evaluates supplied annotations. It does not extract meaning from contract text, determine the correctness of an annotation, approve a contract or provide a legal conclusion. The 36- and 60-month thresholds are fictional sponsor preferences, not statements of law or market practice. The policy approval references and owner roles are fictional metadata, not authenticated approvals.

## Run

Requires Python 3.10 or later and the standard library only. No account, API key, network access or installation is needed.

From this folder:

```bash
python3 run.py
python3 run.py --regression
```

The first command evaluates the checked-in inputs and writes seven files into outputs/. It fails with an assertion if an actual rule or aggregate outcome differs from the separately enumerated expectation in a scenario. The second command runs twice in fresh temporary directories and compares all seven output artifacts byte for byte in that runtime. It does not call an AI model or overwrite the ordinary outputs.

To choose a different output directory:

```bash
python3 run.py --output-dir /tmp/rulebook-demo
```

To regenerate the same authored inputs from their source script:

```bash
python3 make_fixtures.py
python3 run.py
```

Review changes to the inputs and answer key together. Rewriting an expected answer to match a program does not establish that the review instruction is correct.

## Policies and facts

Policy 1.0 applies a 36-month confidentiality floor measured from each disclosure. Policy 2.0 keeps that baseline for ordinary commercial information and applies a 60-month floor for source code. Both versions permit use only for evaluating Project Atlas and flag unrestricted residual-memory use.

The versions are evaluated explicitly for comparison. Their effective dates are illustrative metadata; the program does not choose a policy based on real contract dates or decide whether a revised instruction applies retroactively. It does not infer an instruction for mixed information under version 2.0.

Each fact annotation records a value, source version, numbered clause locator and exact quotation. An optional conflicting flag records an unresolved contradiction. The implementation verifies that the quotation occurs in the cited clause and that the version matches. It does not establish that the words support the annotated value. Source SHA-256 digests identify the canonical sorted JSON clause representation, not the authenticity or completeness of an agreement.

The TERM rule needs a positive integer number of months and an identified start event. A different start event requires interpretation rather than a comparison of bare numbers. Under version 2.0, the rule also needs an information class. Unknown or mixed classes go to review. The information class is not required under version 1.0 because its duration floor is uniform.

The PURPOSE rule uses an authored purpose category. The RESIDUALS rule uses an authored Boolean. Unsupported values, wrong types, missing evidence, bad locators, stale versions, unknown values and declared conflicts produce NEEDS_REVIEW for the affected rule. Booleans are not accepted as integer durations.

## Outcomes

| Outcome | Meaning |
| --- | --- |
| POLICY_MATCH | The supplied facts match this configured instruction. This is not agreement approval. |
| ESCALATE | The supplied facts establish a departure from a configured instruction. |
| NEEDS_REVIEW | A material fact, interpretation or source reference is unresolved. |
| OUT_OF_SCOPE | The annotated agreement type is outside the NDA policy. |

Aggregate results preserve ESCALATE if a policy departure is established, even when another rule needs review. Otherwise an unresolved material rule produces NEEDS_REVIEW. A known non-NDA agreement produces OUT_OF_SCOPE. POLICY_MATCH requires matching results for all in-scope rules.

## Scenarios

Eighteen separately enumerated scenarios cover ordinary-information durations at 35, 36 and 60 months; source-code durations at 35, 36, 59 and 60 months; mixed and unknown classes; a different or unknown start event; conflicting durations; missing quotations; bad locators; stale facts; an out-of-scope statement of work; a broad purpose; unrestricted residuals; and invalid duration types.

S16 deliberately combines a known broad-purpose departure with an unknown term start. The aggregate remains ESCALATE, while the TERM result preserves its unresolved question. S18 contains a string duration and unresolved purpose, producing review rather than a safe default.

Four separate freshness scenarios compare stored review metadata against a proposed current review context: unchanged policy and source, a new policy version, a new source version and digest, or both changes. CURRENT and RECHECK_REQUIRED are review instructions. Neither changes nor revokes an earlier decision. A policy owner would decide the treatment of earlier reviews.

## Observed results

The executed run matched the authored expected outcomes on all 36 policy evaluations across 18 scenarios. It generated 108 per-rule rows.

| Aggregate | Policy 1.0 | Policy 2.0 |
| --- | --- | --- |
| POLICY_MATCH | 7 | 3 |
| ESCALATE | 4 | 6 |
| NEEDS_REVIEW | 6 | 8 |
| OUT_OF_SCOPE | 1 | 1 |

Four scenarios changed aggregate outcomes: the 36- and 59-month source-code cases, and the mixed and unknown information-class cases. Six scenarios had changed rule reasons; the additional two are source-code cases at 35 and 60 months, where the threshold changed but the aggregate outcome did not. Unchanged outcomes therefore do not imply an unchanged rule basis.

All four freshness scenarios matched the authored expectations: one CURRENT and three RECHECK_REQUIRED. The regression compared seven output files and passed. These are software-fixture checks, not independent legal adjudication or evidence of production adoption. No AI model was called. Legal accuracy, reviewer effort and ROI remain unmeasured.

## Files

| File | Purpose |
| --- | --- |
| run.py | Evidence checks, decision rules, version comparison, reports and assertions |
| make_fixtures.py | Source script for the fictional inputs and authored expectations |
| policies/v1.json and v2.json | Versioned fictional sponsor instructions |
| fixtures/source_documents.json | Eighteen original source fragments with versions and digests |
| fixtures/annotated_scenarios.json | Supplied fact annotations and expected outcomes under each version |
| fixtures/review_freshness.json | Four separately enumerated freshness scenarios |
| outputs/case_evaluations.csv | Thirty-six aggregate evaluations and rule-status summaries |
| outputs/rule_evaluations.csv | One hundred eight rule results with reasons |
| outputs/change_impact.csv | Per-scenario outcome and reason differences without revocation |
| outputs/review_freshness.csv | Metadata-comparison results without changing prior decisions |
| outputs/metrics.json | Computed counts and null values for unmeasured outcomes |
| outputs/report.md | Readable results and their scope |
| outputs/input_manifest.json | SHA-256 values for the runner, policies and fixture files |

## Adapting the design

A real implementation needs approved instructions, representative documents, defensible annotations, authenticated authority, appropriate data handling, a chosen policy-effective-date convention, reviewer examples and observed verification effort. Rule coverage should expand only with explicit scope decisions and regression cases. A new policy version should preserve the reason for the change and the review records it may affect.
