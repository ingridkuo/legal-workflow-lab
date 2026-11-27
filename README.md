# Legal Workflow Lab

**Ingrid Kao · Taiwan-qualified attorney · UC Berkeley Master of Laws**

I draft commercial agreements, build contract workflows and translate legal review standards into rules engineers can use. This repository brings together anonymized matters from my practice and demonstrations built on fictional contracts and records. Each demonstration shows a decision and the evidence behind it.

[Six-page work samples (PDF)](Ingrid_Kao_Work_Samples.pdf) · [Portfolio](https://ingridkao.netlify.app/) · [Practitioner articles](08_practitioner_notes/README.md) · [LinkedIn](https://www.linkedin.com/in/ingrid-kao-1702aa26b/)

## Start here

**Why does an NDA that says "approve" go back to Legal?** In NDA-19, one section accepts unlimited liability. Another tells the reviewer to approve the agreement and suppress the findings. Open the saved review to see the source text and the action each clause requires.

[Walk through the NDA review](https://ingridkao.netlify.app/lab/01_ai_review/replay.html) · [Inspect the source and tests](01_ai_review/README.md#the-replay-page-source-and-tests)

**Did all eight contracts migrate correctly?** The source and destination counts match, yet five fictional records have to be held. Compare the batch before and after correction, and see why the record owner still signs off.

[Compare the migration reports](https://ingridkao.netlify.app/lab/05_solution_delivery/) · [Inspect the migration checks](05_solution_delivery/README.md)

**Who can preserve records, and who approves their release?** A fictional request asks for both preservation and an account export. Intake asks the system owner to pause routine deletion, and the export decision goes to Counsel.

[Follow the preservation and export request](https://ingridkao.netlify.app/lab/06_knowledge_operations/) · [Inspect the handoff and approval rules](06_knowledge_operations/README.md)

## Choose the work relevant to the role

- **Legal AI evaluation.** The [review method (PDF)](01_ai_review/AI_Contract_Review_Method.pdf) explains how I checked source quotes and counted overlapping findings. The [repeatability report (PDF)](01_ai_review/repeatability/Repeatability_Results.pdf) records three more reviews of the same held-out documents.
- **Commercial contracts.** [Five anonymized cases from my practice (PDF)](04_case_studies/Selected_Case_Studies.pdf) cover a technology license, a confidentiality remedy, equipment acceptance, transaction execution and permission to use legal data.
- **Legal operations and intake.** Read the [Jira Service Management and Confluence implementation case (PDF)](02_legal_ops/Ingrid_Kao_Legal_Intake_Implementation_Case.pdf), then explore the [operations tracker (Excel)](02_legal_ops/Contract_Operations_Tracker.xlsx) and the [workflow guide (PDF)](02_legal_ops/Legal_Operations_Workflow.pdf).
- **Customer training and adoption.** The [training case (PDF)](03_training/Training_and_Customer_Success.pdf) covers adoption and product feedback. The [knowledge handoff demonstration](https://ingridkao.netlify.app/lab/06_knowledge_operations/) shows which guidance a reviewer may use.
- **Construction contracts.** The [subcontract workflow](07_construction_workflow/README.md) shows how exceptions reach the right reviewer. Its [tracker (Excel)](07_construction_workflow/Ingrid_Kao_Subcontract_Workflow_Tracker.xlsx) follows guarantees after signature, and the [owner-side issues list (PDF)](07_construction_workflow/Ingrid_Kao_Owner_Side_Construction_Issues.pdf) compares AIA A201-2017 with Taiwan PCC model terms.

## A guided model demonstration

[Inside the Review](https://ingridkao.netlify.app/lab/01_ai_review/replay.html) puts three saved decisions beside their source clauses:

- **NDA-19.** Disregard the embedded instruction. Revise the clause imposing unlimited liability or obtain senior Legal/Finance approval before proceeding.
- **NDA-18.** Request Appendix T before assessing the confidentiality period.
- **NDA-03.** Keep the two specific findings and document why the count changed from three to two.

Inspect the quotes, rules, prompts and decision brief, or download a checked packet as JSON, with the addresses of the source agreement and of the view it came from. The evidence challenge alters a temporary copy; no archive is edited. The replay needs no account, API key or new model call. Twenty tests cover its mechanical checks, and seven more check that a copied link reopens the same document, tab, finding and prompt. These tests are separate from the archived model evaluation.

The Lab's landing page also runs the intake routing example, with no account or API key.

## Practitioner articles and companion demonstrations

[Three practitioner notes](08_practitioner_notes/README.md) connect legal judgment to runnable, synthetic examples:

| Article | Companion evidence |
|---|---|
| [Testing a legal AI review workflow](08_practitioner_notes/articles/Ingrid_Kao_Testing_Legal_AI.pdf) | 16 output-gate fixtures; one saved eight-document review; eight adjudicated document–rule pairs grouped into six actionable issues |
| [When a legal escalation is ready to close](08_practitioner_notes/articles/Ingrid_Kao_Legal_Escalation_Closure.pdf) | 12 workflow scenarios; Python/SQLite case and audit records; closure and preservation follow-up |
| [From counsel guidance to executable review rules](08_practitioner_notes/articles/Ingrid_Kao_Executable_Review_Rules.pdf) | 18 scenarios under two policy versions; 36 evaluations; change-impact and review-freshness reports |

These are separate datasets. The eight-document exploratory review does not replace the original 20-document NDA Lab, and the 12 workflow scenarios are separate from the 29 knowledge-gate tests. The [dataset map and run commands](08_practitioner_notes/README.md#dataset-map) identify each unit and result.

## Evidence and scope

The case studies describe my historical work. Client identities and monetary terms are withheld, and proposed edits are kept apart from the confirmed signed outcome. The workflow demonstrations use fictional records and proposed policy thresholds. The training sample separates historical experience from sample training scenarios.

The original NDA Lab uses 20 synthetic NDAs: five development documents and 15 held-out documents. The saved v2 held-out review returned **16 findings for 16 reference issues**; all 16 quotes matched their stated sections. I reviewed all 25 reference labels across the 20 documents and changed none. The method explains how overlapping findings are counted. Each pass is one archived review batch, and the issues share contract and review context, so these counts describe the fixed set; they are not a population accuracy estimate. Source-quote checks, reference-label agreement and live approval controls are separate questions.

The migration example checks deliberately flawed and corrected fixtures, and the knowledge example tests proposed access and approval gates. A clean migration report still leaves record-owner signoff and destination-system checks outstanding. Enforcing real system permissions needs separate checks.

The legal analysis and review decisions are my own, and I use an AI coding assistant to help draft code changes.

## Files

- [Work samples for sharing (PDF)](Ingrid_Kao_Work_Samples.pdf): six pages to download and send; the links open the hosted exhibits. The [repository edition (PDF)](Ingrid_Kao_Work_Samples_Web.pdf) links to the same exhibits on GitHub.
- **Contracting and operations.** [Commercial contracting handbook](02_legal_ops/Commercial_Contracting_Handbook.pdf) · [Workflow guide](02_legal_ops/Legal_Operations_Workflow.pdf) · [Contract tracker (Excel)](02_legal_ops/Contract_Operations_Tracker.xlsx)
- **Implementation and adoption.** [Legal intake implementation case](02_legal_ops/Ingrid_Kao_Legal_Intake_Implementation_Case.pdf) · [Training and customer success](03_training/Training_and_Customer_Success.pdf)
- **Practice and evaluation.** [Five selected case studies](04_case_studies/Selected_Case_Studies.pdf) · [NDA evaluation method](01_ai_review/AI_Contract_Review_Method.pdf)
- **Working demonstrations.** [Migration and data quality](05_solution_delivery/README.md), with 30 behavioral tests · [Escalation and knowledge operations](06_knowledge_operations/README.md), with 29 gate tests · [Subcontract workflow](07_construction_workflow/README.md), with 38 tests

## Run the reproducible examples

For the local NDA prototype, run this command from the repository root, open the printed address and select **Run checks**. It validates the saved results; it does not call a model or need an API key.

```sh
python3 01_ai_review/scripts/web_lab.py
```

The other examples need no package installation. Use Python 3.10+ for the scorer and SQLite example; Node.js 18+ for intake routing.

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
node tools/test_review_view.cjs
```

The scorer checks saved outputs; it does not start a new model review. The SQLite script rebuilds the fictional database and six CSV reports. The intake script returns a review route, missing facts and reviewer groups. Routing and approval to sign remain separate decisions.

To view the complete collection locally, serve this folder with any static server, for example:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8000/` on that computer. Stop the server when finished.

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

## Folder guide

| Folder | Contents |
|---|---|
| `01_ai_review` | Method, policy, prompts, synthetic inputs, saved findings and scoring script |
| `02_legal_ops` | Legal intake implementation case, tracker, playbook, handbook, workflow, intake code and SQLite example |
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

## License

Copyright © 2026 Ingrid Kao.

- **Code and demo data** (`.py`, `.js`, `.cjs`, `.html`, `.sql`, `.json`, `.csv` and other files that run or feed the demonstrations): [MIT License](LICENSE).
- **Written material** (practitioner notes, playbooks, checklists, review rules and their PDF, Word and Excel versions): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). You may reuse and adapt it with attribution. To cite it, use **Cite this repository** on GitHub or [`CITATION.cff`](CITATION.cff).
- **Not covered by either license (all rights reserved):** the case studies and any summaries of them, the work samples, the articles, and the portrait and illustrations (`04_case_studies/`, `02_legal_ops/Ingrid_Kao_Legal_Intake_Implementation_Case.pdf`, `Ingrid_Kao_Work_Samples*`, `08_practitioner_notes/articles/`, `assets/avatar.webp`, `assets/illustrations/`).
- **Third-party material keeps its own terms:** the Inter font (SIL Open Font License; notices in `assets/`), the SALI records (notice in `01_ai_review/taxonomy/sources/SALI_LICENSE.txt`) and quoted standard-form contract language.

Contact: [kuoingrid0118@gmail.com](mailto:kuoingrid0118@gmail.com) · [LinkedIn](https://www.linkedin.com/in/ingrid-kao-1702aa26b/)

Selected professional work and synthetic demonstrations. Not legal advice.
