PRAGMA foreign_keys = ON;

CREATE TABLE dataset_settings (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
    as_of_date TEXT NOT NULL CHECK (date(as_of_date) = as_of_date),
    currency TEXT NOT NULL CHECK (currency = 'USD'),
    fictional INTEGER NOT NULL CHECK (fictional = 1),
    policy_id TEXT NOT NULL,
    threshold_yellow_usd NUMERIC NOT NULL,
    threshold_red_usd NUMERIC NOT NULL,
    near_term_days INTEGER NOT NULL,
    source_sha256 TEXT NOT NULL,
    source_notes TEXT NOT NULL,
    source_metadata_json TEXT NOT NULL,
    CHECK (threshold_yellow_usd >= 0),
    CHECK (threshold_red_usd >= threshold_yellow_usd)
);

CREATE TABLE contracts (
    contract_id TEXT PRIMARY KEY,
    contract_type TEXT NOT NULL,
    counterparty TEXT NOT NULL,
    business_owner TEXT NOT NULL,
    value_usd NUMERIC CHECK (value_usd IS NULL OR value_usd >= 0),
    risk_trigger TEXT,
    stage TEXT NOT NULL,
    next_action TEXT,
    approval_due TEXT,
    target_signature TEXT,
    actual_signature TEXT,
    renewal_date TEXT,
    notice_days INTEGER CHECK (notice_days IS NULL OR notice_days >= 0),
    notice_basis TEXT,
    notice_method TEXT,
    notice_source_verified TEXT,
    coi_required TEXT,
    coi_expiry TEXT,
    coi_evidence TEXT,
    entity_verified TEXT,
    signature_authority TEXT,
    template_unchanged TEXT,
    personal_data TEXT,
    controlled_technology TEXT,
    other_red_flag TEXT,
    reviewer_check TEXT,
    source_locator TEXT NOT NULL,
    review_notes TEXT,
    expected_rag TEXT NOT NULL CHECK (expected_rag IN ('GREEN','YELLOW','RED','NEEDS INPUT'))
);

CREATE TABLE obligations (
    obligation_id TEXT PRIMARY KEY,
    contract_id TEXT NOT NULL REFERENCES contracts(contract_id),
    milestone TEXT NOT NULL,
    description TEXT NOT NULL,
    owner TEXT NOT NULL,
    planned_date TEXT,
    actual_date TEXT,
    budget_usd NUMERIC,
    committed_usd NUMERIC,
    actual_cost_usd NUMERIC,
    invoice_number TEXT,
    invoiced_usd NUMERIC,
    paid_usd NUMERIC,
    acceptance_required TEXT,
    acceptance_evidence TEXT,
    reviewer_check TEXT,
    source_locator TEXT NOT NULL
);

CREATE TABLE compliance_calendar (
    compliance_id TEXT PRIMARY KEY,
    entity TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    obligation TEXT NOT NULL,
    owner TEXT NOT NULL,
    planned_due TEXT,
    completed_date TEXT,
    source TEXT NOT NULL,
    reviewer_check TEXT
);

CREATE INDEX idx_contracts_renewal ON contracts(renewal_date);
CREATE INDEX idx_contracts_value ON contracts(value_usd);
CREATE INDEX idx_obligations_contract ON obligations(contract_id);
CREATE INDEX idx_obligations_due ON obligations(planned_date, actual_date);
CREATE INDEX idx_calendar_due ON compliance_calendar(planned_due, completed_date);

-- The computed result does not read expected_rag. Reference labels are retained
-- only for fixture verification, not as approval decisions.
CREATE VIEW v_contract_risk AS
SELECT c.*,
    CASE
        WHEN c.personal_data = 'Yes'
          OR c.controlled_technology = 'Yes'
          OR c.other_red_flag = 'Yes'
          OR lower(trim(c.risk_trigger)) IN (
              'residuals','personal data','shared-model training',
              'controlled technology','sanctions alert','export-control alert',
              'unlimited liability','exclusivity','noncompete'
          )
          OR c.value_usd >= s.threshold_red_usd
        THEN 'RED'
        WHEN c.value_usd IS NULL
          OR typeof(c.value_usd) NOT IN ('integer', 'real')
          OR c.value_usd < 0
          OR trim(ifnull(c.contract_id, '')) = ''
          OR ifnull(c.contract_type, '') NOT IN ('NDA','SaaS','Services','Hardware supply','Equipment','Lease','Subcontract')
          OR ifnull(c.risk_trigger, '') NOT IN ('None','Nonstandard term')
          OR ifnull(c.entity_verified, '') NOT IN ('Yes','No')
          OR ifnull(c.signature_authority, '') NOT IN ('Yes','No')
          OR (c.contract_type = 'NDA' AND ifnull(c.template_unchanged, '') NOT IN ('Yes','No'))
          OR ifnull(c.personal_data, '') NOT IN ('Yes','No')
          OR ifnull(c.controlled_technology, '') NOT IN ('Yes','No')
          OR ifnull(c.other_red_flag, '') NOT IN ('Yes','No')
          OR ifnull(c.reviewer_check, '') NOT IN ('Verified','Pending')
        THEN 'NEEDS INPUT'
        WHEN c.value_usd >= s.threshold_yellow_usd
          OR lower(trim(c.risk_trigger)) <> 'none'
          OR ifnull(c.entity_verified, '') <> 'Yes'
          OR ifnull(c.signature_authority, '') <> 'Yes'
          OR (c.contract_type = 'NDA' AND c.template_unchanged = 'No')
          OR ifnull(c.reviewer_check, '') <> 'Verified'
        THEN 'YELLOW'
        ELSE 'GREEN'
    END AS computed_rag
FROM contracts c
CROSS JOIN dataset_settings s;

-- Calculate calendar-day notice dates only when the source and method are
-- supplied and verified. Business-day calendars and unknown bases are gated.
CREATE VIEW v_notice_review AS
SELECT c.contract_id, c.counterparty, c.business_owner,
       c.renewal_date, c.notice_days, c.notice_basis, c.notice_method,
       c.notice_source_verified, c.source_locator,
       CASE
           WHEN c.renewal_date IS NOT NULL
            AND c.notice_basis = 'Calendar'
            AND c.notice_days IS NOT NULL
            AND c.notice_source_verified = 'Yes'
            AND length(trim(ifnull(c.notice_method, ''))) > 0
           THEN date(c.renewal_date, printf('-%d days', c.notice_days))
           ELSE NULL
       END AS calculated_notice_date,
       CASE
           WHEN c.renewal_date IS NULL THEN 'NO RENEWAL DATE RECORDED'
           WHEN ifnull(c.notice_basis, '') <> 'Calendar' THEN 'MANUAL REVIEW - NOTICE BASIS'
           WHEN c.notice_days IS NULL THEN 'MANUAL REVIEW - MISSING NOTICE DAYS'
           WHEN ifnull(c.notice_source_verified, '') <> 'Yes' THEN 'MANUAL REVIEW - SOURCE UNVERIFIED'
           WHEN length(trim(ifnull(c.notice_method, ''))) = 0 THEN 'MANUAL REVIEW - MISSING NOTICE METHOD'
           ELSE 'CALCULATED - VERIFY NOTICE DELIVERY'
       END AS notice_gate
FROM contracts c;
