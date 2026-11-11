# Technical scope and demonstration

Ingrid Kao

## Portfolio description

I turn legal review standards into executable checks. This lab combines a browser interface, a Python HTTP service, structured findings and a scoring harness. The controls verify source identity, output format, exact quotations, rule-family matches and escalation requirements.

**Suggested resume wording**

Built a local full-stack legal-review prototype with a browser interface, Python API and repeatable evaluation harness; tested structured findings against source contracts and reviewed reference labels, and mapped the review taxonomy to SALI identifiers with explicit coverage gaps.

Use the wording only after running the demonstration and explaining the code and its boundaries. The prototype and portfolio describe a current work sample; they are separate from my historical Lawsnote implementation work.

## What the terms mean here

| Term | Inspectable implementation | Scope |
|---|---|---|
| Executable software | Python and JavaScript perform validation and return a result from supplied records. | Working local demonstration. |
| Harness | A fixed request, output schema, saved responses, reference labels and a scorer produce comparable results. | Re-executing a scorer does not generate new model responses. |
| Full-stack prototype | Browser UI sends a fixed request to a loopback Python HTTP endpoint; the endpoint runs the checks and returns JSON. | Local frontend/backend implementation, without a deployed multi-user service. |
| Production code | Requires an operating deployment and evidence of identity, authorization, secret management, monitoring, recovery, change control and user acceptance. | This sample does not establish that operational experience. |
| SALI crosswalk | Stable external concept identifiers are attached to local rules and document metadata, with mapping relationships and gaps recorded. | The local risk policy and approval requirements remain separate. |
| DMS design | Document/version identity, content hash, matter link, source provenance, access classification, retention and legal hold fields are modeled. | Metadata examples do not implement an enterprise DMS or enforce permissions. |

## A short interview walkthrough

1. Start the local web Lab and select **Run checks**. Explain that this checks recorded generations; it does not contact a model.
2. Open NDA-19. Show the source-contained approval instruction and the unlimited-liability clause, then the two findings.
3. Show the exact quote and Section check. A real quote in the wrong Section still fails the locator test.
4. Open NDA-18. Explain why a missing incorporated appendix returns NEED_SOURCE instead of an invented duration defect.
5. Open the three-run results. Separate issue detection, evidence support, severity/routing and consistency; a consistently missed issue is still a failure.
6. Open the SALI crosswalk. Show one broader or related concept and one unmapped control; explain why a content label cannot grant access or approve a contract.

## Metrics to explain

- The scoring unit is **document ID + rule ID**. The held-out partition has 16 positive reference instances across 15 documents, not 16 distinct issue types. The policy defines 15 rule types.
- Supported true positive: an expected rule is returned with an exact quotation in its stated Section.
- False positive: a returned finding does not qualify as a supported reference match. This category includes an unsupported quote; it does not always mean the legal concern is false.
- False negative: an expected reference issue is not supported by the returned result.
- Precision = supported true positives / returned findings. Recall = supported true positives / reference issues. A zero denominator is undefined, not automatically perfect.
- Presence consistency asks whether the same rule is returned in all three batches. Supported-match consistency also requires usable source evidence. Severity, route, status and reviewer requirements are reported separately.
- High consistency can be consistently wrong. A small synthetic set, especially a reused development-era partition, cannot establish performance on new client agreements.

The new study records three isolated agent batches using the same frozen request. The runtime did not expose a model snapshot or sampling parameters, so this is not a controlled provider-version benchmark.
