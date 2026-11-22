# Selected Work

Ingrid Kao

## Skills in practice

*Skills and evidence*

Taiwan-qualified attorney | UC Berkeley Master of Laws (2026)

My work spans law-firm practice, sole in-house counsel work and a legal-tech company. I turn legal requirements into usable clauses, clear review decisions and records that someone else can follow.

| Skill | Evidence to inspect | Page |
| --- | --- | --- |
| **Commercial judgment**<br>Drafting, negotiation, risk allocation | A liability cap that undercut a Taiwan-law penalty clause, a signed technology license and a buyer-side acceptance revision with its fallback. | 02 |
| **Workflow design**<br>Intake, approvals, contract lifecycle | Executable routing with 87 passing tests, a contract tracker and named review and signature gates. | 03 |
| **Data quality**<br>Mapping, migration QA, SQL reporting | An XML-to-JSON migration check with seeded exceptions and correction reports, plus six SQLite reports. | 04 |
| **Legal AI evaluation**<br>Rules, prompts, source verification | Fixed synthetic NDA tests, saved outputs, quote checks, three repeated agent batches and a pilot decision. | 05 |
| **Program and knowledge operations**<br>Handoffs, documentation, adoption | Two completed transaction plans, a source-backed escalation record and guidance checked before use. | 06 |

### What is historical and what runs here

The anonymized matters describe my own work; client names and identifying details are withheld. The demonstrations use fictional records and proposed controls. They were built with AI assistance, and their inputs, code and results are included for inspection. Nothing in this document is legal advice.

- [Companion collection and reproducible examples](./README.md)
- [Contact kuoingrid0118@gmail.com](mailto:kuoingrid0118@gmail.com)
- [LinkedIn profile](https://www.linkedin.com/in/ingrid-kao-1702aa26b)

## Make the decision visible.

*01 / Commercial judgment*

Skills: commercial drafting, negotiation, risk allocation, bilingual clauses and business communication.

### A liability cap that undercut the contract’s own penalty

I reviewed a client’s cloud-hosting and managed-services agreement. The provider’s liability cap, set at 30% of the contract price, came to about a quarter of the contractual penalty that a separate clause set for confidentiality breaches. Taiwan law allows such a penalty, subject to reduction by a court, so the cap could have limited what the client recovered under that clause. I proposed carving the clause out of the cap and widening its trigger from disclosure to any breach of the confidentiality obligations. **The signed agreement raised the cap** and included a six-hour repair commitment and service credits.

### Battery management system licensing

I represented the licensee in a cross-border deal for an exclusive patent and technology license covering a battery management system. When talks stalled over future improvements, I separated two questions. Who would own the improvements, and who could use them? I drafted and negotiated the agreement on that basis, and **both parties signed**.

### Acceptance, from both sides

For a Taiwan manufacturer supplying a U.S. brand, I drafted a bilingual English-Chinese supply agreement with five-day inspection and deemed acceptance. The sample below takes the buyer’s side.

> **Sample clause**
>
> Goods are accepted on delivery. The warranty ends twelve months after shipment.

> **Buyer-side revision**
>
> Goods are accepted only after the Buyer’s written confirmation that the Schedule 2 tests passed. The warranty ends twelve months after written acceptance.

**Fallback if the seller needs certainty:** a fixed test window that starts once the seller has given notice of readiness and the goods can be tested, written reasons for any failure and one retest. Deemed acceptance may follow only a missed window.

**Owners:** Quality and Engineering set the tests; Procurement and Legal align acceptance, warranty and payment.

**Historical execution:** I tracked a manufacturer’s equipment acceptance against a 95% operating-rate requirement and drafted the default, cure and termination notices under the agreement’s cure and delay terms.

- [Clause positions, fallback options, redlines and bilingual terms](./02_legal_ops/Commercial_Contracting_Handbook.pdf)
- [Five anonymized matters and their outcomes](./04_case_studies/Selected_Case_Studies.pdf)

## Keep the next owner clear.

*02 / Workflow and controls*

Skills: intake, prioritization, approval routing, contract administration and obligation tracking.

As sole in-house counsel to a contractor, I built the contract review and approval workflow from scratch, with escalation by deal value, for about 50 contracts a month. Each risk rating sat next to the revenue at stake, and I tracked signed contracts through inspection, acceptance, invoicing and payment.

| Stage | Required record | Next owner |
| --- | --- | --- |
| Intake | Entity, paper and version, value, purpose, deadline and risk facts | Business owner |
| Review and escalation | Source clause, issue, proposed position and unresolved facts | Legal / specialist |
| Approval and signature | Recorded approval, complete attachments, final version and signing authority | Approver / authorized signer |
| Delivery and acceptance | Planned and actual dates, agreed tests and supporting evidence | Project owner / Quality |
| Payment and renewal | Invoice and acceptance status, notice source and action date | Finance / record owner |

### A working routing decision

The same rule runs in the command-line example (Node.js) and on the portfolio’s intake page, and 87 tests cover it. Known critical risk, or a value of $250,000 or more, routes RED before missing facts are considered. Otherwise, missing required information returns NEEDS INPUT, and $100,000 starts YELLOW. Only a routine, unchanged NDA can qualify for the delegated GREEN workflow.

**Control:** Every result keeps approval to sign separate from the route. Unknown amounts stay unknown. A notice date is calculated only from a verified source clause, on a stated calendar-day basis.

**Inspectable sample:** 24 fictional contracts, 48 allocated obligations and 12 compliance-calendar tasks. The tracker shows risk, value, owners, acceptance evidence and payment status together.

**Platform experience:** For an Ironclad client implementation, I worked on launch forms, templates and conditional approvals. At Lawsnote, I tracked a client’s contract expiry dates in DocuSign CLM. The included code demonstrates the underlying decisions locally.

- [Open the Excel tracker](./02_legal_ops/Contract_Operations_Tracker.xlsx)
- [Workflow guide and responsibility gates](./02_legal_ops/Legal_Operations_Workflow.pdf)

## Verify the move, then release it.

*03 / Data quality and reporting*

Skills: XML and JSON mapping, migration validation, exception analysis, SQL and reconciliation.

At Lawsnote, I validated a migration of more than 10,000 contract records through field mapping and import checks. This demonstration applies the same method to a small fictional dataset.

| XML source | JSON destination | Check |
| --- | --- | --- |
| None; assigned on import | repository_record_id | Unique key, case-insensitive |
| @id / @revision | source_record_id / source_revision | Exact match to the source; current revision |
| owner | business_owner | Required; blank space counts as missing |
| signed_on / expires_on | signed_date / expiry_date | Real ISO dates; expiry not before signature |
| amount_usd | value_usd | Exact decimal; blank stays null, not zero |
| visibility_group | access_group | Copied unchanged; approved groups only |

### Executed test / eight fictional records

The flawed export contains four seeded exception groups: a missing owner, a destination-key collision, an impossible date and a stale source revision. The validator finds all four, holds the five affected records and passes the other three; record counts reconcile. The corrected export has eight clean records and no exceptions, and **30 tests pass**.

Each exception records its source, field, expected and actual values, owner and next action. A clean batch is ready for owner signoff; the check does not grant release authority. The parser rejects DTD and entity declarations before reading any XML.

### Report what changes the next action

Six SQLite queries in the operations sample identify near-term renewals, value thresholds, insurance evidence, overdue milestones, notice review, and budget and invoice exceptions. Missing values remain visible instead of becoming zero.

- [Mapping, fixtures, code and correction reports](./05_solution_delivery/index.html)
- [Six SQL queries and the contract operations database](./02_legal_ops/README.md)

## Test the rule and the evidence.

*04 / Legal AI evaluation*

Skills: requirements translation, prompt design, structured outputs, evaluation and pilot judgment.

At Lawsnote, I turned an enterprise client’s NDA standards into rules that engineers built into an AI contract-review product. I reviewed about 1,000 NDAs and checked outputs against the source contracts for false positives, inconsistent results and edge cases. The portfolio lab separates the policy, prompt, document, finding and reviewer decision.

> **A checkable finding**
>
> Policy family → exact source quote → Section locator → proposed action → named review owner. Missing incorporated material triggers a request for the source. An instruction embedded in a contract is treated as document content and is not followed (indirect prompt injection, OWASP LLM01).

| Held-out synthetic test | Observed result |
| --- | --- |
| Documents / reference issues | 15 documents / 16 issues |
| Reference matches / critical misses | 16 of 16 matched / 0 of 9 RED issues missed |
| Source quotes and Section locators | 16 of 16 supported |
| Three later isolated agent batches | 45 reviews; each batch matched 16 of 16, no false positives |
| Reference labels | Ingrid Kao reviewed all 25 labels across the 20 documents and changed none, so the scores use the labels as first defined. |

### An error analysis worth keeping

v1 returned an extra PURPOSE finding that the clause supported. v2 folds that overlap into the more specific residuals and model-training findings. The change makes counting consistent; it is not evidence of improved legal accuracy.

### Pilot decision

**Proceed:** a supervised evaluation using an approved policy and authorized sample inputs. **Hold production release:** validate representative agreements, access controls, reviewer agreement, handling time and task completion before scaling. With client documents, the governing conduct rules apply (ABA Formal Opinion 512 (2024) is the U.S. guide): confidentiality, client consent where required, vendor diligence and lawyer supervision. The 16/16 results describe this synthetic set; the agent batches ran without exposed model settings.

- [Method, repeated-run results and source checks](./01_ai_review/AI_Contract_Review_Method.pdf)
- [Interactive replay of the saved results](./01_ai_review/replay.html)

## Make the handoff usable.

*05 / Program and knowledge operations*

Skills: project ownership, dependencies, evidence synthesis, knowledge controls, training and adoption.

I wrote the 17-step execution plan for a Taiwan company’s corporate division and a 12-stage plan for a cross-border share acquisition. Each step was tied to its legal basis, its dependencies and the person responsible. **Both transactions closed.**

### Sample escalation / ESC-101

> **What the source actually says**
>
> “Please retain the records for Account DEMO-71 and send me the account export.” The sender also writes: “I have not attached an authorization document.”

| Keep separate | Record and handoff |
| --- | --- |
| Known facts | The request asks for retention and an export; no authorization document is attached. |
| Unknowns | The sender’s identity and authority, the scope of the request and any duty that applies. |
| Owner and next action | Fictional Legal Intake Owner asks the system owner to pause routine deletion, tracks the acknowledgment, and verifies identity and authority through a contact already on file. |
| Current decision | Hold for Fictional Counsel. The pause is requested and the system owner’s acknowledgment is still open; nothing is disclosed or exported until authority is verified and Counsel approves the scope. |

### Guidance that can be checked before use

Before an article is used, a local check confirms its exact source quotes, that the approval covers the current text, independent review, dates and permitted roles. In the fixed test, one article is eligible, one draft is blocked and one article past its review date is blocked. All three fictional escalations keep a named reviewer and grant no authority; **29 tests pass**. Article approvals are simulated workflow records.

**Adoption:** At Lawsnote, I trained about 100 users, turned feedback into product issues and won back more than 20 subscribers with a ten-user group plan I proposed. The training sample measures progress by whether a learner checks a finding against its source and names the escalation owner.

- [Escalation records, maintained articles and executed checks](./06_knowledge_operations/index.html)
- [Training and customer-success sample](./03_training/Training_and_Customer_Success.pdf)
