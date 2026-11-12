# Ingrid Kao | Practitioner Notes and Companion Demonstrations

Three practitioner articles connect legal judgment to inspectable implementation. Each PDF includes a first-page link to its companion evidence. The examples use synthetic records and are separate from the portfolio’s original AI Review Lab and knowledge-operations demonstrations.

## Choose a note

| Article | Best starting point | Companion implementation |
| --- | --- | --- |
| [Testing a Legal AI Review Workflow](articles/Ingrid_Kao_Testing_Legal_AI.pdf) | Legal AI evaluation and evidence checks | [Saved NDA review and adjudication](experimental_llm/README.md); [output gate](toolkit/README.md) |
| [When a Legal Escalation Is Ready to Close](articles/Ingrid_Kao_Legal_Escalation_Closure.pdf) | Legal operations, escalation ownership, and closure | [Workflow, scenarios, and SQL reporting](toolkit/README.md) |
| [From Counsel Guidance to Executable Review Rules](articles/Ingrid_Kao_Executable_Review_Rules.pdf) | Rule design, policy changes, and review freshness | [Versioned rulebook](rulebook_toolkit/README.md) |

## Testing a Legal AI Review Workflow

The [article](articles/Ingrid_Kao_Testing_Legal_AI.pdf) separates authored software fixtures from a recorded model-review exercise:

- **Software gate:** 16 authored output fixtures; 12 blocked, one refusal routed to manual review, and three outputs routed to human review.
- **Recorded model exercise:** eight synthetic NDA fragments (A01–A08), one saved Codex agent batch, and eight source-supported document–rule findings.
- **Adjudication:** the original six-pair provisional key is retained. A documented post-run revision accepts PURPOSE for A04 and A06 alongside RESIDUALS, producing eight reference pairs. Grouping those overlaps under the more specific RESIDUALS rule yields six actionable issue groups.
- **Result:** the saved response matches all eight revised reference pairs and six issue groups. This resolves classification and counting; the model response is unchanged. The small, post-run-adjudicated set is not an independent population benchmark.

Inspect the [sources](experimental_llm/documents.json), [policy](experimental_llm/toy_policy.json), [original key](experimental_llm/provisional_answer_key.json), [raw response](experimental_llm/raw_model_response.json), [adjudication ledger](experimental_llm/adjudication_v1_1.json), [revised key](experimental_llm/adjudicated_answer_key.json), and [scorer](experimental_llm/evaluate_exploration.py).

## When a Legal Escalation Is Ready to Close

The [article](articles/Ingrid_Kao_Legal_Escalation_Closure.pdf) defines completion evidence and continuing ownership. Its [Python/SQLite implementation](toolkit/README.md) exercises 12 workflow scenarios and records 62 audit events. The final register has two closed, seven blocked, and three assigned cases; one open case is overdue at the fixed snapshot. A closed case retains an accepted active preservation follow-up.

The 12 scenarios are not the 29 gate tests in the separate `06_knowledge_operations` project. They exercise different code and records. Here, pending preservation review blocks closure; pre-execution preservation enforcement remains a deployment requirement.

## From Counsel Guidance to Executable Review Rules

The [article](articles/Ingrid_Kao_Executable_Review_Rules.pdf) turns a legal instruction into an explicit policy record. Its [rulebook](rulebook_toolkit/README.md) evaluates 18 authored scenarios under two policy versions, producing 36 aggregate evaluations and 108 rule rows. Four cases change outcome; six change reasons. Four review-freshness checks produce one CURRENT and three RECHECK_REQUIRED results.

This deterministic prototype evaluates source-linked annotations. It does not extract meaning from arbitrary contracts or call a model.

## Dataset map

| Project | Inputs or evaluation unit | Reported observation |
| --- | --- | --- |
| Original `01_ai_review` Lab | 20 synthetic NDAs; 15 held-out; 15 rule types | 16 held-out reference issues; three recorded review batches |
| This collection’s `experimental_llm` | Eight NDA fragments; four toy policy rules | Eight revised document–rule pairs; six actionable groups; one saved batch |
| This collection’s `toolkit` | 16 authored output fixtures and 12 workflow scenarios | Gate behavior and workflow transitions |
| Original `06_knowledge_operations` | Separate article/escalation/policy fixtures | 29 gate tests |
| This collection’s `rulebook_toolkit` | 18 annotated scenarios under two policies | 36 evaluations; 108 rule rows; four freshness checks |

Counts use different denominators. They should be interpreted within the named project rather than combined into a single accuracy or test-total claim.

## Run locally

Python 3.10+ and its standard library are sufficient. No API key, package installation, or external connection is needed. From this folder:

```sh
python3 toolkit/run.py
python3 toolkit/run.py --regression
python3 experimental_llm/evaluate_exploration.py
python3 -m unittest discover -s experimental_llm -p test_exploration.py -v
python3 rulebook_toolkit/run.py
python3 rulebook_toolkit/run.py --regression
```

The toolkit and rulebook runners rebuild their own outputs. Regression commands run in fresh directories and compare generated artifacts. The exploratory scorer checks the saved model response; it does not generate a new response.

Editable Word and Markdown sources accompany the PDFs in `articles/`. `MANIFEST.json` records the collection’s file hashes. All operational records, clauses, policies, and examples are synthetic. The original saved response and provisional key remain unchanged for inspection.
