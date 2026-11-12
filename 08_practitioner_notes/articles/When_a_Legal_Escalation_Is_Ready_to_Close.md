# When a Legal Escalation Is Ready to Close

Ingrid Kao  
Independent practitioner note  
November 10, 2026

[Companion files · GitHub](https://github.com/ingridkuo/legal-workflow-lab/tree/main/08_practitioner_notes/toolkit)

### At a glance

**Built:** A Python/SQLite workflow for accepted handoffs, decisions, execution records, and continuing obligations.

**Observed (synthetic):** 12 of 12 scenarios matched; 62 audit events; two cases closed.

**Meaning:** Closure requires recorded completion evidence and an accepted owner for ongoing obligations.

A tracker can say “closed” as soon as a coordinator sends an email. The email may ask somebody else to act, leaving the substantive task unfinished. When the record contains no accepted handoff or execution receipt, the next person cannot tell whether the instruction reached its owner, whether anyone acted on it, or whether a further decision remains open.

As sole in-house counsel, I tracked contracts through signature, inspection, acceptance, and payment. That work made the distinction between sending an instruction and confirming completion practical. It is also a useful problem for legal program design. Before automating reminders or summaries, a team needs an agreed definition of completion. My proposed definition is narrow: a case is ready to close when an authorized decision has led to verified action and any continuing obligation has an accepted owner.

This note develops that definition through a reference workflow and a companion demonstration using synthetic records. It focuses on coordination among Legal, Product, Safety, Security, and User Operations. The aim is to make ownership and completion inspectable, including when a request arrives with incomplete information.

## Authority before automation

An intake record often combines different kinds of judgment. A coordinator may recognize that a request needs attention without having authority to decide its legal merits. A security specialist may confirm a technical event without deciding what communication or retention action follows. Clear roles keep those judgments attached to the people responsible for them.

NIST’s AI Risk Management Framework places documented responsibilities, training, and leadership accountability within governance. Its Generative AI Profile provides additional guidance for applying governance to generative AI systems.[1][2] I use those frameworks to support an operating choice: establish human decision authority before allowing automation to advance a case.

| Role | Responsibility in the reference design | Decision boundary |
| --- | --- | --- |
| Program coordinator | Collect facts, route questions, confirm accepted ownership, track blockers, and check completion evidence | Does not supply missing legal approval |
| Counsel or designated legal decision maker | Decide the legal question, approve the applicable action, and determine preservation instructions | Does not presume operational execution from a recommendation |
| Security, Safety, or User Operations owner | Investigate or execute actions within the owner’s authority and provide a receipt | Does not treat an AI recommendation as authorization |
| Records custodian | Carry out and maintain authorized preservation instructions | Does not infer release from case closure |

An AI-generated summary can help prepare a decision packet. It should not populate the approval field as though counsel had signed off. OWASP’s discussion of excessive agency supports constraining the actions and permissions available to AI-assisted processes.[3] In this design, a recommendation and an authorization remain separate records.

## A record another person can reconstruct

The tracker should hold enough information to explain progress without becoming an unnecessary second repository of sensitive material. A compact record needs a case identifier, intake key, intake time, request type, redacted summary, source reference, and source version. It also needs named owners, the next action, relevant dates, and the evidence supporting the current status.

Reported facts, assumptions, and unresolved questions deserve separate fields. “A user reported exposure” and “Security confirmed exposure” describe different evidence states. Combining them into a confident narrative can change the apparent basis for a decision.

Dates also need a clear basis. Distinguish internal targets from deadlines supplied by an authoritative source. The prototype uses illustrative case review and completion targets for overdue reporting. These are not acknowledgment targets, legal deadlines, or employer service commitments.

Source references should point to permissioned records, with a version identifying the basis for each decision. A classification label alone does not enforce access. The demonstration uses simulated roles; deployment requires authenticated identities, authorization checks, and appropriate storage controls.

## Progression with evidence gates

These proposed stages separate receipt, decision, execution, and confirmation. Information gathering, urgent routing, multi-team handoffs, and communication checks belong to the reference design. The prototype implements the narrower ownership, decision, receipt, version, and closure controls described later.

| Stage change | Evidence required to advance |
| --- | --- |
| Received to needs information | A specific missing item and an owner for obtaining it |
| Received to triaged | A request type, source reference, priority basis, and visible information gaps |
| Triaged to assigned | Named receiving owners and an accepted handoff |
| Assigned to ready for execution | The applicable decision or approval and a defined authorized action |
| Ready for execution to pending confirmation | Receipts for the required actions |
| Pending confirmation to closed | Completion checked, required communications recorded, and continuing obligations assigned |

Incomplete information should not suppress urgent routing. A reported urgent signal can enter the established specialist path while the coordinator continues gathering facts. The routing event should identify the basis for urgency and preserve uncertainty about unverified details.

After assignment, a blocker should remain attached to the case and its owner. Moving a record into a generic waiting column can conceal responsibility. A useful blocker states what is missing, who will obtain it, and what the next follow-up should accomplish.

## A fictional case through the workflow

Consider a fictional report from a product team: an exported support summary may contain information from another customer, and a scheduled cleanup could affect the relevant records. The report is incomplete. It identifies a sample file but does not establish who received it or what the cleanup will delete.

The coordinator records those uncertainties, links the sample in its restricted source location, and routes the reported issue under the example team’s existing escalation procedure. Security accepts responsibility for investigating distribution. User Operations accepts responsibility for any approved customer-facing action. Counsel receives a defined question about the proposed response and the records that may need preservation.

The coordinator does not turn the report into a confirmed incident or determine the scope of a preservation obligation. The pending preservation question is recorded separately. A deployment handling destructive actions should prevent execution while required preservation review remains unresolved. The companion prototype demonstrates a narrower control: pending preservation review blocks case closure; it does not implement a pre-execution preservation gate.

Suppose counsel then records an instruction covering the relevant source records. A records custodian accepts continuing responsibility. Security supplies its findings, and counsel authorizes a defined response based on those findings. The execution owner completes the authorized action and links its receipt. Where a communication is required, the record identifies the approved content and evidence that it was sent.

At that point, the coordinator checks the source version, decision reference, accepted owners, receipts, and unresolved tasks. A sent email requesting action would not satisfy that check. An execution receipt linked to the authorized task could.

The operational case can close while the preservation track remains active, provided the applicable decision permits that separation and the continuing custodian has accepted responsibility. Closing the case must not automatically release the preservation instruction. A later release requires its own authorized decision and execution record.

This distinction avoids an unhelpful choice between keeping every case open indefinitely and losing track of obligations that outlast the immediate response.

## Measure the queue as well as completed work

A fuller operating report should show intake completeness, unaccepted handoffs, blocker age, decision wait time, and missing receipts. It also identifies cases reopened after apparent completion. These proposed measures point to different interventions: better intake questions, clearer ownership, additional decision capacity, or more reliable execution checks. The prototype reports state and owner counts, overdue open cases, and preservation commitments; it does not yet compute these additional latency or quality measures.

Latency measures need pending items alongside completed ones. A median acknowledgment time calculated only from acknowledged requests can look reassuring while older requests remain unanswered. A reporting snapshot should retain those pending cases and show their age.

Closure-gate results also need clear denominators. Repeated attempts to close one case are multiple attempts, not multiple cases. A report should distinguish blocked attempts from affected cases and explain which missing condition triggered each rejection.

## What the demonstration can establish

The companion prototype makes a limited claim: specified workflow rules can be executed and inspected against fixed synthetic scenarios. Its records and event history allow a reviewer to examine why a proposed transition succeeded or failed.

Twelve workflow scenarios matched their expected behavior. The checks covered missing owners, unaccepted handoffs, missing counsel decisions, missing execution receipts, pending preservation review, ongoing preservation ownership, duplicate intake, source changes, and overdue reporting. The implementation rejected a counsel decision before an operational owner had accepted the handoff. A source-version change invalidated the earlier decision and execution receipt.

| Result from the synthetic run | Observed count |
| --- | --- |
| Scenarios matching expected behavior | 12 of 12 |
| Cases in the register | 12 |
| Final states | 2 closed, 7 blocked, 3 assigned |
| Overdue nonclosed cases at the fixed snapshot | 1 |
| Closed cases with an accepted active preservation follow-up | 1 |
| Recorded audit events | 62 |

The runner uses Python and SQLite, an explicit external-to-canonical field mapping, and configurable routing. Its SQL reports show state, owner workload, overdue cases, and preservation commitments. These are computed from stored case and event records. The fixed simulation clock and authored dates produce a repeatable snapshot; they do not measure staff effort.

The prototype implements a subset of the reference design. It checks required references, source-version alignment, handoff acceptance, and closure prerequisites. It does not fetch external receipts or verify that an action occurred, implement the full multi-team fictional incident, or determine whether a preservation instruction is legally appropriate. A referenced receipt is a required record in this exercise; substantive verification remains a deployment responsibility.

The records support inspection of the implemented controls and the exercised inputs; broader deployment requires the verification and identity controls described below.

## Release requires an owner for adoption

A small pilot should begin with one bounded request category and a named process owner. Before release, that owner should confirm the decision roles, required fields, escalation paths, and examples of acceptable completion evidence. Receiving teams need to accept the handoff definition, including what they are expected to acknowledge and return.

Training can then use the fictional case to show how an incomplete report moves forward, where counsel’s decision is required, and why closure can fail. A short guide should explain how to correct missing information and how to report a rule that prevents legitimate work.

The release decision should consider rejected transitions and user effort alongside throughput. If staff repeatedly bypass a field, the process owner should investigate whether its purpose is unclear, the evidence is unavailable, or the gate is poorly placed. Changes should receive a version, a responsible approver, and a regression check against the established scenarios.

A reliable closure record gives the next person a concrete account of the decision and its execution. It also makes unfinished work visible. That is the standard an automation should help a team maintain.

## Method and references

This independent practitioner study uses fictional scenarios and synthetic records. Its 12 workflow scenarios are separate from the portfolio’s knowledge-operations gate tests. The reference workflow is a proposed operating design rather than an employer policy or universal legal closure rule. Simulated identities and receipt references do not authenticate users or verify external execution. The prototype blocks closure during pending preservation review; it does not implement a pre-execution preservation gate or measure real staff effort, legal accuracy, or production security.

[1] NIST. Artificial Intelligence Risk Management Framework. NIST AI 100-1, January 2023. GOVERN 2.1 through 2.3. https://doi.org/10.6028/NIST.AI.100-1

[2] NIST. Artificial Intelligence Risk Management Framework Generative Artificial Intelligence Profile. NIST AI 600-1, July 2024. GV-2.1-002. https://doi.org/10.6028/NIST.AI.600-1

[3] OWASP. LLM06:2025 Excessive Agency. Sections on excessive functionality, permissions, autonomy, and mitigation. Accessed November 11, 2026. https://genai.owasp.org/llmrisk/llm062025-excessive-agency/
