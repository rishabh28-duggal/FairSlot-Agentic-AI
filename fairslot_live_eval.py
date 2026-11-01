"""Run a live Groq-backed parser evaluation from the FairSlot repository root.

Set GROQ_API_KEY in your environment (never commit secrets):
    python fairslot_live_eval.py

This tests 20 authored requests, NOT 20 student interactions.
It does not establish that a live evaluation was successfully run until its CSV
and summary results are inspected. No secrets or user-identifying data are saved.
"""
import csv
import json
import os
import time
from pathlib import Path
from agents import parse_prefs, llm_available, MODEL

CASES = [
    ('T01','Tennis, weekday evenings, 2 hrs, under ₹700',dict(activity='tennis',days=['mon','tue','wed','thu','fri'],start_hour=17,end_hour=24,duration_hours=2,max_price=700)),
    ('T02','Saturday morning badminton, 7am for two hours',dict(activity='badminton',days=['sat'],start_hour=7,end_hour=8,duration_hours=2)),
    ('T03','Cricket on Sunday after 4pm, budget Rs 500',dict(activity='cricket',days=['sun'],start_hour=16,end_hour=24,max_price=500)),
    ('T04','Squash on Tuesdays or Thursdays, after 6pm',dict(activity='squash',days=['tue','thu'],start_hour=18,end_hour=24)),
    ('T05','Football on weekends, flexible timing',dict(activity='football',days=['sat','sun'],flexible=True)),
    ('T06','Basketball on Monday before 10am',dict(activity='basketball',days=['mon'],start_hour=0,end_hour=10)),
    ('T07','Swimming on Friday evening, 1 hour',dict(activity='swimming',days=['fri'],start_hour=17,end_hour=24,duration_hours=1)),
    ('T08','Pickleball on Wednesday morning',dict(activity='pickleball',days=['wed'],start_hour=5,end_hour=12)),
    ('T09','Tennis on Saturday after 6pm, under Rs 400',dict(activity='tennis',days=['sat'],start_hour=18,end_hour=24,max_price=400)),
    ('T10','Badminton on Monday and Friday evening, 90 minutes',dict(activity='badminton',days=['mon','fri'],start_hour=17,end_hour=24,duration_hours=1.5)),
    ('T11','I need two hours of tennis on Sunday night',dict(activity='tennis',days=['sun'],start_hour=20,end_hour=24,duration_hours=2)),
    ('T12','Can play squash anytime on weekdays, below ₹600',dict(activity='squash',days=['mon','tue','wed','thu','fri'],max_price=600)),
    ('T13','Tennis Thursday after 7pm for 1.5 hrs',dict(activity='tennis',days=['thu'],start_hour=19,end_hour=24,duration_hours=1.5)),
    ('T14','Badminton Saturday before 9am, up to Rs 300',dict(activity='badminton',days=['sat'],start_hour=0,end_hour=9,max_price=300)),
    ('T15','Cricket Tuesday afternoons',dict(activity='cricket',days=['tue'],start_hour=12,end_hour=17)),
    ('T16','Football on Sunday, anything works, 2 hours',dict(activity='football',days=['sun'],flexible=True,duration_hours=2)),
    ('T17','Tennis on Friday after 5pm, under 700 rupees',dict(activity='tennis',days=['fri'],start_hour=17,end_hour=24,max_price=700)),
    ('T18','Basketball Monday after 8pm, 1 hour',dict(activity='basketball',days=['mon'],start_hour=20,end_hour=24,duration_hours=1)),
    ('T19','Swimming on Saturday mornings, max ₹250',dict(activity='swimming',days=['sat'],start_hour=5,end_hour=12,max_price=250)),
    ('T20','Badminton Tuesday or Saturday evenings, 2 hours',dict(activity='badminton',days=['tue','sat'],start_hour=17,end_hour=24,duration_hours=2)),
]
FIELDS = ['activity','days','start_hour','end_hour','duration_hours','max_price','flexible']

def normalized(value):
    return sorted(value) if isinstance(value, list) else value

def main():
    if not llm_available():
        raise SystemExit('Live evaluation requires GROQ_API_KEY and SLOT_AGENT_OFFLINE unset. No requests were made.')
    rows = []
    total_fields = correct_fields = 0
    for cid, request, expected in CASES:
        started = time.perf_counter()
        try:
            p = parse_prefs(request)
            actual = {field: getattr(p, field) for field in FIELDS}
            checks = {field: normalized(actual[field]) == normalized(value) for field, value in expected.items()}
            total_fields += len(checks)
            correct_fields += sum(checks.values())
            row = dict(case_id=cid, request=request, expected=json.dumps(expected, ensure_ascii=False),
                       actual=json.dumps(actual, ensure_ascii=False), source=p.source,
                       matched_fields=sum(checks.values()), tested_fields=len(checks),
                       all_correct=all(checks.values()),
                       errors=','.join(key for key, match in checks.items() if not match),
                       latency_ms=round((time.perf_counter()-started)*1000), exception='')
        except Exception as exc:
            total_fields += len(expected)
            row = dict(case_id=cid, request=request, expected=json.dumps(expected, ensure_ascii=False),
                       actual='', source='ERROR', matched_fields=0, tested_fields=len(expected),
                       all_correct=False, errors='exception',
                       latency_ms=round((time.perf_counter()-started)*1000), exception=str(exc))
        rows.append(row)
        print(cid, row['source'], row['matched_fields'], '/', row['tested_fields'], row['errors'])
    dest = Path('fairslot_live_eval_results.csv')
    with dest.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print('\nModel:', MODEL)
    print('Exact-case accuracy:', sum(r['all_correct'] for r in rows), '/', len(rows))
    print('Field accuracy:', correct_fields, '/', total_fields)
    print('LLM used:', sum(str(r['source']).startswith('llm') for r in rows), '/', len(rows))
    print('Rule fallback:', sum(str(r['source']).startswith('rules') for r in rows), '/', len(rows))
    print('CSV:', dest.resolve())
    print('NOTE: checks cover specified fields only; inspect extra fields and ambiguous cases manually.')
    print('NOTE: mixed LLM/rule fallback accuracy is not equivalent to pure LLM accuracy.')

if __name__ == '__main__':
    main()
