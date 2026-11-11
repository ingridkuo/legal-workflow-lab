# Implementation control design

Ingrid Kao | Proposed operational controls

The local NDA example uses fictional sources, a reviewed reference key, saved output records and deterministic scoring. Its replay displays those saved records. Source hashes, exact-quote/Section checks, routing comparisons and the required human-review output flag are exercised locally.

## Controls for real matter work

Implementation starts with the task, tool and data. I would review provider terms, access, retention and training use, then determine the applicable confidentiality and client-communication obligations. Informed consent is obtained where required. A lawyer verifies material assertions and retains responsibility for legal judgment.

The following records are proposed design choices for an approved organization-specific implementation. Identity, access and release permissions must be enforced outside the model by the organization's systems.

| Control | Proposed record | Decision owner |
|---|---|---|
| Task and tool assessment | Use case, limitations and acceptance criteria | Reviewing lawyer |
| Provider and data review | Terms, access, retention, training use and confidentiality assessment | Legal with Security |
| Client authority and communication | Authorization and applicable disclosure or informed-consent decision | Matter lawyer |
| Source access | Approved source identifiers, policy version and minimum permitted read scope | Data and policy owner |
| Output verification | Material assertion, source locator and reviewer disposition | Reviewing lawyer |
| Supervision and release | Draft-only state, exception owner and recorded release authority | Supervising lawyer |

ABA Formal Opinion 512 supplies Model Rules guidance on competence, confidentiality, communication and supervision. Apply the governing jurisdiction's rules and engagement terms; informed consent is fact-specific. See sections A-C and E, especially pages 2-4, 6-9 and 10-11.

## Instruction and tool boundaries

NDA-19 contains an indirect prompt-injection attempt: a contract sentence asks the reviewer to suppress findings and output approval. The saved review reports it and continues to review the separate unlimited-liability issue. This is consistent with the source-content boundary described in OWASP LLM01:2025.

A real implementation should constrain source reads to authorized identifiers, keep policy changes outside the review session, validate structured draft output and require the responsible person to make high-impact release decisions. A prompt instruction alone is not an access-control mechanism. Additional adversarial documents, retrieval patterns and connected-tool behaviors belong in the next-stage test plan.

## Primary references

- [ABA Formal Opinion 512](https://www.americanbar.org/content/dam/aba/administrative/professional_responsibility/ethics-opinions/aba-formal-opinion-512.pdf)
- [Official ABA release](https://www.americanbar.org/content/aba-cms-dotorg/en/news/abanews/aba-news-archives/2024/07/aba-issues-first-ethics-guidance-ai-tools/)
- [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)

These references inform the design; the sample is not a certification of compliance or a deployed enterprise security system.
