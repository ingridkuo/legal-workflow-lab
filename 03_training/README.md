# Training and Customer Success

Ingrid Kao | 10 November 2026

Start with **Training_and_Customer_Success.pdf**. Page 1 is my Lawsnote experience; pages 2-4 are sample materials for the fictional product Clause Harbor.

The supporting files make the sample session easy to follow:

- **training_excerpt.txt**: fictional NDA text, sample rules, and facilitator reference.
- **feedback_form.md**: reusable feedback fields and severity guide.
- **sample_feedback_queue.csv**: six fictional scenarios for triage and follow-through discussion, each with its last update and, while it stays open, the date its next update is due.
- **queue_dates.py**: calculates those next update dates from the table below.
- **Training_and_Customer_Success.md**: editable text of the four-page document.

## Update cadence

These intervals are for the demonstration only; a real team would set its own. This table is the only place they are written: **queue_dates.py** reads it and fills **next_update_due** in the CSV.

| Severity | Business days from the last update to the next |
| --- | --- |
| S1 | 1 |
| S2 | 2 |
| S3 | 5 (once a week) |
| S4 | No fixed date: reviewed with the backlog |

- **next_update_due** is **last_update** plus the interval for the entry's severity. Business days run Monday to Friday; the sample keeps no holiday calendar.
- A closed entry has no next update, so its date is blank, as is an S4 entry's.
- When an entry's severity changes, its **last_update** becomes the day of the change, and the next date counts from there.
- After editing the table or the CSV, run `python3 queue_dates.py`. `python3 queue_dates.py --check` lists any date that does not follow the table.
