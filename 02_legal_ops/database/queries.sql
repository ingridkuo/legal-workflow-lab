-- Each named block is one read-only query. The builder executes these exact
-- statements and exports the actual rows. As-of and thresholds live in
-- dataset_settings. Dates below are calendar dates, not time-of-day findings.

-- name: q01_expiring_within_90_days
SELECT c.contract_id, c.contract_type, c.counterparty, c.business_owner,
       c.renewal_date,
       CAST(julianday(c.renewal_date) - julianday(s.as_of_date) AS INTEGER) AS days_until_renewal,
       c.value_usd, c.computed_rag, n.calculated_notice_date, n.notice_gate,
       c.source_locator
FROM v_contract_risk c
CROSS JOIN dataset_settings s
JOIN v_notice_review n ON n.contract_id = c.contract_id
WHERE date(c.renewal_date) BETWEEN date(s.as_of_date) AND date(s.as_of_date, '+90 days')
ORDER BY c.renewal_date, c.contract_id;

-- name: q02_value_threshold_escalations
SELECT c.contract_id, c.contract_type, c.counterparty, c.business_owner,
       c.value_usd,
       CASE WHEN c.value_usd >= s.threshold_red_usd
            THEN 'RED VALUE BAND - SENIOR LEGAL / FINANCE / BUSINESS OWNER'
            ELSE 'YELLOW VALUE BAND - LEGAL / FINANCE'
       END AS value_escalation,
       c.computed_rag AS overall_rag, c.risk_trigger, c.next_action,
       'DEMONSTRATION ROUTING ONLY - NOT APPROVAL' AS decision_limit
FROM v_contract_risk c
CROSS JOIN dataset_settings s
WHERE c.value_usd >= s.threshold_yellow_usd
ORDER BY c.value_usd DESC, c.contract_id;

-- name: q03_coi_missing_or_expired
SELECT c.contract_id, c.counterparty, c.business_owner, c.coi_required,
       c.coi_evidence, c.coi_expiry,
       trim(
           CASE WHEN ifnull(c.coi_evidence, '') = 'Missing'
                THEN 'MISSING COI; ' ELSE '' END ||
           CASE WHEN ifnull(c.coi_evidence, '') NOT IN ('Verified','Missing')
                THEN 'UNVERIFIED EVIDENCE; ' ELSE '' END ||
           CASE WHEN c.coi_expiry IS NULL
                THEN 'MISSING EXPIRY; ' ELSE '' END ||
           CASE WHEN date(c.coi_expiry) < date(s.as_of_date)
                THEN 'DATE EXPIRED; ' ELSE '' END,
           '; '
       ) AS evidence_exception,
       'VERIFY ACTUAL POLICY AND ENDORSEMENTS - COI IS NOT COVERAGE APPROVAL' AS required_action
FROM contracts c
CROSS JOIN dataset_settings s
WHERE c.coi_required = 'Yes'
  AND (ifnull(c.coi_evidence, '') <> 'Verified'
       OR c.coi_expiry IS NULL
       OR date(c.coi_expiry) < date(s.as_of_date))
ORDER BY c.coi_expiry IS NOT NULL, c.coi_expiry, c.contract_id;

-- name: q04_overdue_acceptance_payment_milestones
SELECT o.obligation_id, o.contract_id, c.counterparty, o.milestone, o.owner,
       o.planned_date, o.actual_date,
       CAST(julianday(s.as_of_date) - julianday(o.planned_date) AS INTEGER) AS days_past_due,
       o.acceptance_required, o.acceptance_evidence,
       o.invoiced_usd, o.paid_usd, o.reviewer_check,
       'DUE DATE PASSED - COMPLETION UNCONFIRMED' AS status,
       o.source_locator
FROM obligations o
JOIN contracts c ON c.contract_id = o.contract_id
CROSS JOIN dataset_settings s
WHERE o.milestone IN ('Acceptance','Payment')
  AND date(o.planned_date) < date(s.as_of_date)
  AND o.actual_date IS NULL
ORDER BY o.planned_date, o.obligation_id;

-- name: q05_nonrenewal_notice_review
SELECT n.contract_id, n.counterparty, n.business_owner, n.renewal_date,
       n.notice_days, n.notice_basis, n.notice_method, n.notice_source_verified,
       n.calculated_notice_date, n.notice_gate,
       CASE
           WHEN n.calculated_notice_date IS NULL THEN 'MANUAL / SOURCE REVIEW'
           WHEN date(n.calculated_notice_date) < date(s.as_of_date) THEN 'DATE PASSED - REVIEW RIGHTS AND DELIVERY'
           WHEN date(n.calculated_notice_date) = date(s.as_of_date) THEN 'DUE TODAY - VERIFY DELIVERY REQUIREMENTS'
           ELSE 'FUTURE DATE - VERIFY SOURCE AND DELIVERY'
       END AS date_status,
       n.source_locator
FROM v_notice_review n
CROSS JOIN dataset_settings s
WHERE n.renewal_date IS NOT NULL
   OR ifnull(n.notice_basis, '') <> 'Calendar'
   OR n.notice_days IS NULL
   OR ifnull(n.notice_source_verified, '') <> 'Yes'
ORDER BY n.calculated_notice_date IS NULL, n.calculated_notice_date, n.contract_id;

-- name: q06_budget_invoice_exceptions
WITH exception_rows AS (
    SELECT o.*,
       CASE WHEN o.budget_usd IS NOT NULL AND o.actual_cost_usd IS NOT NULL
            THEN o.actual_cost_usd - o.budget_usd ELSE NULL END AS actual_over_budget_usd,
       CASE WHEN o.invoiced_usd IS NOT NULL AND o.paid_usd IS NOT NULL
            THEN o.invoiced_usd - o.paid_usd ELSE NULL END AS invoiced_less_paid_usd,
       CASE WHEN o.budget_usd IS NULL OR o.committed_usd IS NULL
                  OR o.actual_cost_usd IS NULL OR o.invoiced_usd IS NULL OR o.paid_usd IS NULL
            THEN 'NEEDS INPUT' ELSE 'EXCEPTION' END AS financial_status,
       trim(
           CASE WHEN o.budget_usd IS NULL OR o.committed_usd IS NULL
                      OR o.actual_cost_usd IS NULL OR o.invoiced_usd IS NULL OR o.paid_usd IS NULL
                THEN 'MISSING FINANCIAL INPUT; ' ELSE '' END ||
           CASE WHEN o.actual_cost_usd > o.budget_usd
                THEN 'ACTUAL COST ABOVE BUDGET; ' ELSE '' END ||
           CASE WHEN o.committed_usd > o.budget_usd
                THEN 'COMMITTED ABOVE BUDGET; ' ELSE '' END ||
           CASE WHEN o.invoiced_usd > o.committed_usd
                THEN 'INVOICE ABOVE COMMITMENT; ' ELSE '' END ||
           CASE WHEN o.paid_usd > o.invoiced_usd
                THEN 'PAYMENT ABOVE INVOICE; ' ELSE '' END ||
           CASE WHEN o.invoiced_usd > 0 AND length(trim(ifnull(o.invoice_number, ''))) = 0
                THEN 'MISSING INVOICE NUMBER; ' ELSE '' END ||
           CASE WHEN o.acceptance_required = 'Yes'
                     AND ifnull(o.acceptance_evidence, '') <> 'Verified'
                     AND (o.invoiced_usd > 0 OR o.paid_usd > 0)
                THEN 'ACCEPTANCE EVIDENCE NOT VERIFIED; ' ELSE '' END,
           '; '
       ) AS exception_reasons
    FROM obligations o
)
SELECT e.obligation_id, e.contract_id, c.counterparty, e.milestone, e.owner,
       e.budget_usd, e.committed_usd, e.actual_cost_usd,
       e.invoice_number, e.invoiced_usd, e.paid_usd,
       e.actual_over_budget_usd, e.invoiced_less_paid_usd,
       e.acceptance_required, e.acceptance_evidence,
       e.financial_status, e.exception_reasons, e.reviewer_check,
       'REVIEW EXCEPTION - NOT PAYMENT APPROVAL' AS decision_limit,
       e.source_locator
FROM exception_rows e
JOIN contracts c ON c.contract_id = e.contract_id
WHERE e.exception_reasons <> ''
ORDER BY e.financial_status = 'NEEDS INPUT' DESC, e.contract_id, e.obligation_id;
