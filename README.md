# Ingrid Kao / Selected Work

**Commercial contracts · Legal operations · Legal AI**

I am a Taiwan-qualified attorney and Berkeley Law LL.M. graduate. I draft commercial agreements, build contract workflows and translate legal review standards into rules engineers can use. These are selected matters from my practice and working examples of those methods.

## Start here

[Read the six-page Work Samples](Ingrid_Kao_Work_Samples.pdf) · [Practitioner articles](08_practitioner_notes/README.md) · [Browse the portfolio](https://ingridkao.netlify.app/) · [LinkedIn](https://www.linkedin.com/in/ingrid-kao-1702aa26b/)

The examples demonstrate legal rule design, contract judgment, workflow implementation, data reconciliation and evaluation. To run the browser/Python prototype locally:

```sh
python3 01_ai_review/scripts/web_lab.py
```

Open the printed local URL and select **Run checks**. This validates preserved results; it does not call a model or require an API key.

## Practitioner articles and companion demonstrations

[Three practitioner notes](08_practitioner_notes/README.md) connect legal judgment to runnable, synthetic examples:

| Article | Companion evidence |
|---|---|
| [Testing a Legal AI Review Workflow](08_practitioner_notes/articles/Ingrid_Kao_Testing_Legal_AI.pdf) | 16 output-gate fixtures; one saved eight-document review; eight adjudicated document–rule pairs grouped into six actionable issues |
| [When a Legal Escalation Is Ready to Close](08_practitioner_notes/articles/Ingrid_Kao_Legal_Escalation_Closure.pdf) | 12 workflow scenarios; Python/SQLite case and audit records; closure and preservation follow-up |
| [From Counsel Guidance to Executable Review Rules](08_practitioner_notes/articles/Ingrid_Kao_Executable_Review_Rules.pdf) | 18 scenarios under two policy versions; 36 evaluations; change-impact and review-freshness reports |

These are separate datasets. The eight-document exploratory review does not replace the original 20-document `01_ai_review` Lab; the 12 workflow scenarios are separate from the 29 tests in `06_knowledge_operations`. The [dataset map and run commands](08_practitioner_notes/README.md#dataset-map) identify each unit and result.

## Choose the work relevant to the role

| Focus | Start with |
|---|---|
| Legal AI and implementation | [Guided model review](01_ai_review/replay.html), then [method](01_ai_review/AI_Contract_Review_Method.pdf) and [migration](05_solution_delivery/index.html) |
| Commercial contracts and legal operations | [Historical cases](04_case_studies/Selected_Case_Studies.pdf), [tracker](02_legal_ops/Contract_Operations_Tracker.xlsx) and [workflow](02_legal_ops/Legal_Operations_Workflow.pdf) |
| Training and adoption | [Training case](03_training/Training_and_Customer_Success.pdf) and [knowledge handoff](06_knowledge_operations/index.html) |
| Construction contracts and workflow implementation | [Subcontract workflow](07_construction_workflow/README.md), [tracker](07_construction_workflow/Ingrid_Kao_Subcontract_Workflow_Tracker.xlsx) and [owner-side issues](07_construction_workflow/Ingrid_Kao_Owner_Side_Construction_Issues.pdf) |

## Files

- [Application Work Samples](Ingrid_Kao_Work_Samples.pdf): six self-contained pages, with internal page navigation and no relative-file links.
- [Linked portfolio edition](Ingrid_Kao_Work_Samples_Web.pdf): the same six-page content, with links to the companion exhibits.
- [AI contract review method](01_ai_review/AI_Contract_Review_Method.pdf): rubric, fixed tests, evidence checks and error analysis.
- [Contract operations tracker](02_legal_ops/Contract_Operations_Tracker.xlsx): contracts, obligations, milestones and a dashboard.
- [Commercial contracting handbook](02_legal_ops/Commercial_Contracting_Handbook.pdf) and [workflow guide](02_legal_ops/Legal_Operations_Workflow.pdf).
- [Five selected case studies](04_case_studies/Selected_Case_Studies.pdf): anonymized matters from my practice.
- [Training and customer success](03_training/Training_and_Customer_Success.pdf): an additional sample on adoption and product feedback.
- [Migration and data quality](05_solution_delivery/index.html): runnable XML-to-JSON mapping, four seeded defect groups, corrected results and 30 behavioral tests.
- [Escalation and knowledge operations](06_knowledge_operations/index.html): source-backed handoffs, maintained articles and 29 gate tests.

## A guided model demonstration

Open [Inside the Review](01_ai_review/replay.html). Three decisions show the model output and the evidence together:

1. **Document trust:** an instruction embedded in NDA-19 tries to force approval; the saved review flags it and unlimited liability.
2. **Incomplete evidence:** NDA-18 needs a missing appendix before either confidentiality period can be assessed.
3. **Evaluation judgment:** NDA-03 shows how v2 consolidates a source-supported overlap, without claiming improved legal accuracy.

Inspect the source quote, rules, prompts, management brief and fixed-set results. A local challenge changes a temporary copy to demonstrate evidence rejection. Checked packets can be downloaded as JSON. No model is called and no archive is edited.

The landing page also includes working intake routing. Both demonstrations run without an account or API key. The model demonstration has 20 mechanical-check tests; those are distinct from the archived model evaluation.

## Evidence and scope

The case studies describe my historical work. The workflow tools use fictional records and proposed policy thresholds. The training sample distinguishes historical experience from sample training scenarios.

The original AI Review Lab uses 20 synthetic NDAs: 5 development documents and 15 held-out documents. The saved v2 held-out review returned **16 findings for 16 reference issues**; all 16 quotes matched their stated Sections. I reviewed all 25 reference labels across the full 20-document set and changed none. The method explains the rule-family counting convention, including overlapping findings. Each pass is one archived review batch. Issues share contract and review context; these descriptive counts are not a population accuracy estimate. Source-quote checks, reference-label agreement and live approval controls are separate questions.

Historical case summaries omit client identities and monetary terms. Proposed edits are distinguished from the verified signed outcome.

The migration example checks deliberately flawed and corrected fixtures; the knowledge example tests proposed access and approval gates. The results describe those fixed fictional scenarios. Deployment and enforcement of actual system permissions require separate checks.

## Run the reproducible examples

No package installation is required. Use Python 3.10+ for the scorer and SQLite example; Node.js 18+ for intake routing.

```sh
python3 01_ai_review/scripts/run_lab.py check --require-repeats --json
python3 01_ai_review/taxonomy/validate_taxonomy.py
python3 01_ai_review/scripts/score_saved_results.py
python3 02_legal_ops/database/build_database.py
node 02_legal_ops/automation/run_demo.js
node 02_legal_ops/automation/test_triage.js
python3 05_solution_delivery/migration_demo.py
python3 05_solution_delivery/test_migration.py
python3 06_knowledge_operations/check_knowledge.py
python3 -m unittest discover -s 06_knowledge_operations/tests -v
node tools/test_review_demo.cjs
```

The scorer checks saved outputs; it does not start a new model review. The SQLite script rebuilds the fictional database and six CSV reports. The intake script returns a review route, missing facts and reviewer groups. Routing and approval to sign remain separate decisions.

To view the complete collection locally, serve this folder with any static server, for example:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8000/` on that computer. Stop the server when finished.

## Folder guide

| Folder | Contents |
|---|---|
| `01_ai_review` | Method, policy, prompts, synthetic inputs, saved findings and scoring script |
| `02_legal_ops` | Tracker, playbook, handbook, workflow, intake code and SQLite example |
| `03_training` | Training sample, feedback form and fictional feedback queue |
| `04_case_studies` | Five anonymized cases in PDF, text and structured form |
| `05_solution_delivery` | XML/JSON mapping, migration exceptions, correction checks and a pilot decision |
| `06_knowledge_operations` | Synthetic handoff records, source-backed articles and tested knowledge gates |
| `07_construction_workflow` | Subcontract engine, approval policy, 38 tests, Excel tracker and owner-side construction analysis |
| `08_practitioner_notes` | Three articles, output gates, an adjudicated exploratory review, escalation workflow and versioned policy rules |
| `assets` | Bundled fonts and watercolor portrait |
| `tools` | Portable current PDF builders and case-copy synchronization |

## Authoring the current edition

The [current authoring tools](tools/README.md) rebuild the PDFs and case cards from their current sources. The case narratives and featured summaries share one JSON source. Authoring needs ReportLab, Pillow and pypdf; running the demonstrations above needs no extra packages.

Copyright © 2026 Ingrid Kao. Provided for portfolio review. All rights reserved. Inter font license and source notices are in `assets`.

Contact: [kuoingrid0118@gmail.com](mailto:kuoingrid0118@gmail.com) · [LinkedIn](https://www.linkedin.com/in/ingrid-kao-1702aa26b/)

Selected professional work and synthetic demonstrations. For portfolio purposes only; not legal advice.

## Executable review Lab and legal taxonomy

The [local Lab](01_ai_review/Lab_Run_Guide.md) connects a browser interface to a Python API and validation harness. Its **Run checks** action validates preserved outputs; it does not generate a new model response.

The [one-page repeatability report](01_ai_review/repeatability/Repeatability_Results.pdf) records three new isolated agent batches on the same 15 synthetic NDAs: 45 document reviews, with 16 supported reference matches per batch. Exact model settings were not exposed; the original held-out partition was reused. These observations describe the sample rather than production accuracy.

The [SALI crosswalk](01_ai_review/taxonomy/sali_issue_crosswalk.json) maps 15 local rule types and all 16 held-out issue instances to verified source concepts where appropriate. [Mapping notes and DMS metadata](01_ai_review/taxonomy/Taxonomy_and_DMS.md) preserve the gaps and separate content classification from access, retention and approval authority.

The browser/API/harness artifact is a **local full-stack prototype**. It does not establish a deployed production service or enterprise DMS implementation.

## Controlled API study: prepared, not executed

The [API study guide](01_ai_review/API_Study_Guide.md) and [runner](01_ai_review/scripts/api_study.py) define a separate protocol: 15 held-out synthetic NDAs, three requests per document, preserved raw responses and issue-level scoring. No live API responses or results are included in this release. The published three-batch agent results above remain a separate dataset.

Inspect the request plan and offline transport tests without credentials:

```sh
cd 01_ai_review
python3 scripts/api_study.py plan
python3 scripts/test_api_study.py
```
