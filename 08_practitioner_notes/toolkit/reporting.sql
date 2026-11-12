-- name: state_counts
SELECT state, COUNT(*) AS case_count
FROM cases
GROUP BY state
ORDER BY state;

-- name: overdue_cases
SELECT case_id, action_owner, due_at,
       ROUND((julianday(:as_of) - julianday(created_at)) * 24, 2) AS synthetic_age_hours
FROM cases
WHERE state != 'closed' AND due_at < :as_of
ORDER BY case_id;

-- name: cases_by_owner
SELECT COALESCE(action_owner, 'UNASSIGNED') AS action_owner,
       COUNT(*) AS case_count,
       SUM(CASE WHEN state != 'closed' THEN 1 ELSE 0 END) AS open_count
FROM cases
GROUP BY action_owner
ORDER BY action_owner;

-- name: preservation_commitments
SELECT case_id, state, preservation_status, preservation_owner,
       preservation_accepted, preservation_next_review
FROM cases
WHERE preservation_status IN ('pending', 'active')
ORDER BY case_id;
