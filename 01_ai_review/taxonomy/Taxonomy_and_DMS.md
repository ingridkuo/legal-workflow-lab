# Legal taxonomy and document metadata

**Ingrid Kao · 11 November 2026**

This crosswalk connects the NDA Lab's review vocabulary with SALI topics so a finding can be retrieved across systems without losing the policy decision that produced it. It covers **15 local rule types** and **16 reference issue instances across 15 held-out NDAs**. An instance is a document plus a rule; it is not a new issue type.

## What is mapped

| Local rule | SALI topic | Relationship | What remains local |
|---|---|---|---|
| DURATION | Survival Clause | Broader | Survival clock, five-year position and three-year fallback |
| TRADE_SECRET | Trade Secret Law; Confidentiality Clause | Related | Protection while information qualifies; no fixed cap |
| RESIDUALS | Confidentiality Clause | Broader | Residual-memory exception and separate review |
| PURPOSE | Confidentiality Clause | Broader | Evaluation-only use and broader business-use exception |
| MODEL_TRAINING | Machine Learning; Confidentiality Clause | Related | Shared-model use, consent and approval |
| REPRESENTATIVES | Permitted Disclosure Clause; “Representatives” Definition | Related | Need to know, equivalent duties and recipient responsibility |
| COMPELLED_NOTICE | Legally Compelled Disclosure Clause | Broader | Notice and cooperation only where lawful |
| COMPELLED_SCOPE | Legally Compelled Disclosure Clause | Broader | Production limited to what is legally required |
| RETENTION | Retention and Litigation Hold Management | Related | Contract return/deletion deadline and permitted exceptions |
| COMMERCIAL_RESTRICTION | Exclusive Agreement Clause; Non-Competition Covenant | Related | Other restrictions, including no-hire and IP transfer |
| SOURCE_COMPLETENESS | No adequate concept identified | Unmapped | Missing incorporated material and NEED_SOURCE state |
| EMBEDDED_INSTRUCTION | Adversarial Machine Learning | Related | Contract-contained instruction and review isolation |
| UNLIMITED_LIABILITY | Liability Clause | Broader | Express unlimited exposure and escalation |
| PERSONAL_DATA | Data Privacy Clause; Data Protection Agreement | Related | Actual context, processing authority and Privacy review |
| CONTROLLED_TECH | Export Controls Practice | Related | Technical classification and license determination |

“Broader” and “related” describe subject-matter relationships. They do not import a risk rating, preferred clause or approval rule. No exact equivalence is claimed. The machine-readable [crosswalk](sali_issue_crosswalk.json) includes every target's source label, stable IRI, gap note and reference-instance linkage.

## Decisions that matter

- **Preserve two tests under one topic.** Compelled notice and compelled scope share a SALI concept but remain separate local rules. A lawful-notice qualification does not cure excessive production scope.
- **Read definitions before matching labels.** SALI's “Attachment” describes a creditor's seizure remedy. It is not an appropriate tag for an unseen NDA appendix. The source-completeness rule stays unmapped.
- **Do not map an opposite term as an equivalent.** An express unlimited-liability clause is not a “Liability Cap Clause.” The broader liability topic is used instead.
- **Retain the unresolved detail.** A machine-learning tag does not say whether the parties permitted shared-model training. An export-controls practice tag does not classify the technical data or establish a violation.

## DMS design

The [metadata example](dms_metadata_example.json) binds a fictional matter, document and immutable version to the exact bytes of NDA-19. It is a design record, with no connection to a vendor DMS.

| Layer | Stored information | Reason |
|---|---|---|
| Matter | Matter ID, fictional entity, responsible role | Groups work without treating each version as a new matter |
| Document and version | Separate IDs, status, source path and SHA-256 | Prevents a review from silently following a changed document |
| Taxonomy | SALI IRIs plus display labels and pinned revision | Supports retrieval and interoperability while labels evolve |
| Access | Distinct read, edit and export roles | A document topic or RED route grants no access rights |
| Retention and hold | Trigger, schedule, disposition authority and hold owner | A hold suspends disposition; it does not authorize disclosure |
| Review | Local rule IDs, policy version, review record and human decision | Keeps classification separate from legal approval |

In an implementation, the application would enforce access before retrieval, bind review output to the source version, and check retention and hold state before disposition. Those enforcement steps are not represented as deployed features here. The example leaves disposition dates unset because the triggering event has not occurred.

## Source and verification

The source is the official [SALI LMSS repository](https://github.com/sali-legal/LMSS), pinned to commit [`3f9ac0c9357b2a971582ae79ede243511d47811d`](https://github.com/sali-legal/LMSS/tree/3f9ac0c9357b2a971582ae79ede243511d47811d), committed 10 March 2026. This is a pinned `main` snapshot, not a claimed formal release.

The full OWL file's SHA-256 is `51acefd5051aa8f52e60d6dd142b0925c7cec3a5d789bfbe4fcbe69021c9bba1`. The package includes 20 selected source concepts, preserving their labels, definitions and direct parent IRIs. The mapping is my analytical layer; it does not modify the SALI ontology and is not a SALI-endorsed mapping.

From this folder, with Python 3:

```sh
python3 validate_taxonomy.py
python3 validate_taxonomy.py --verify-upstream
```

The first command works offline. It checks all rule and issue-instance links, labels and IRIs against the included excerpt, source-file hashes and the DMS design boundaries. The second downloads the pinned official OWL source and also verifies its full hash and each selected concept against the original. Neither command contacts a DMS or calls a language model.

The [source records](sources/selected_sali_concepts.json) and [original repository license](sources/SALI_LICENSE.txt) are included. SALI's [official standard page](https://sali.org/explore-the-standard/) explains versioned exports and separately describes its website's CC BY-ND license; the pinned GitHub repository carries the included MIT notice.
