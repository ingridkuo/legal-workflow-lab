"""Fill next_update_due in sample_feedback_queue.csv from the update cadence in README.md.

The intervals live in one place: the "Update cadence" table in README.md. This script reads that table and gives
each open entry its next update date, which is its last_update plus the interval for its severity, counted in
business days (Monday to Friday). A closed entry, or a severity with no fixed interval, gets no date.

usage: python3 queue_dates.py           rewrite next_update_due in the CSV
       python3 queue_dates.py --check   list any date that does not follow the table, and exit 1 if there is one
"""
import csv
import datetime as dt
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
README, QUEUE = HERE / 'README.md', HERE / 'sample_feedback_queue.csv'
CLOSED = ('Closed',)          # a sample_status that starts with one of these has no next update


def cadence():
    """{severity: business days, or None for no fixed date}, read from the README's table"""
    text = README.read_text(encoding='utf-8')
    section = re.search(r'^## Update cadence\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    if not section:
        sys.exit('README.md has no "## Update cadence" section')
    table = {}
    for sev, days in re.findall(r'^\| (S\d) \| ([^|\n]+?) \|$', section.group(1), re.M):
        number = re.match(r'\d+', days)
        table[sev] = int(number.group(0)) if number else None
    if not table:
        sys.exit('the "Update cadence" section has no severity rows')
    return table


def add_business_days(day, n):
    while n:
        day += dt.timedelta(days=1)
        if day.weekday() < 5:
            n -= 1
    return day


def due(row, table):
    if row['severity'] not in table:
        sys.exit(f"{row['feedback_id']}: severity {row['severity']!r} is not in the README's update cadence")
    try:
        last = dt.date.fromisoformat(row['last_update'])
    except ValueError:                                         # 2026-11-31, say, or a blank
        sys.exit(f"{row['feedback_id']}: last_update {row['last_update']!r} is not a real date in YYYY-MM-DD form")
    if row['sample_status'].startswith(CLOSED) or table[row['severity']] is None:
        return ''
    return add_business_days(last, table[row['severity']]).isoformat()


def main(check):
    table = cadence()
    with QUEUE.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)
    for column in ('severity', 'sample_status', 'last_update', 'next_update_due'):
        if column not in (fields or ()):
            sys.exit(f'sample_feedback_queue.csv has no {column} column')
    wrong = [(r['feedback_id'], r['next_update_due'], due(r, table)) for r in rows if r['next_update_due'] != due(r, table)]
    if check:
        for fid, found, expected in wrong:
            print(f'{fid}: next_update_due is {found or "blank"}, the table gives {expected or "blank"}')
        print(f'{len(rows)} entries, {len(wrong)} dates off the table')
        return 1 if wrong else 0
    for r in rows:
        r['next_update_due'] = due(r, table)
    with QUEUE.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\r\n')
        writer.writeheader()
        writer.writerows(rows)
    print(f'{len(rows)} entries, {len(wrong)} dates changed')
    return 0


if __name__ == '__main__':
    sys.exit(main('--check' in sys.argv[1:]))
