# Versioned rulebook demonstration results

The run matched authored expectations on 36 policy evaluations across 18 synthetic scenarios and two policy versions. It produced 108 per-rule results. These are checks of software behavior against authored fixtures, not legal or model accuracy.

| Aggregate result | Policy 1.0 | Policy 2.0 |
| --- | --- | --- |
| POLICY_MATCH | 7 | 3 |
| ESCALATE | 4 | 6 |
| NEEDS_REVIEW | 6 | 8 |
| OUT_OF_SCOPE | 1 | 1 |

4 scenarios changed aggregate outcomes. 6 scenarios had a changed rule reason, including threshold changes where the outcome remained the same. The change report identifies comparisons for a new review context. It does not apply a policy retroactively or revoke a prior decision.

All 4 review-freshness scenarios matched authored expectations: one CURRENT and three RECHECK_REQUIRED. A changed version identifies a comparison task, without changing any earlier decision.

The engine evaluates supplied annotations and exact source-linkage fields. It does not extract contractual meaning, verify annotation correctness, authenticate counsel, approve agreements, or resolve substantive uncertainty. The policy's 36- and 60-month thresholds are fictional sponsor instructions. Missing, stale, conflicting or incorrectly typed material facts produce NEEDS_REVIEW for the affected rule. A confirmed policy departure remains ESCALATE even if another rule needs review.

No network request or model inference occurred. Legal accuracy, reviewer effort and ROI are unmeasured.
