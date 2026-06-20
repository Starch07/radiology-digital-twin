import csv
import json
from collections import Counter

# Read the CSV
rows = list(csv.DictReader(open('radiology_pipeline/results/summary.csv')))

# Extract triage priorities
priorities = [r['triage_priority'].strip() for r in rows if r['triage_priority'].strip()]
priority_counts = Counter(priorities)

# Extract red flags
red_flags = [r['red_flags'].strip() for r in rows if r['red_flags'].strip()]
red_flag_counts = Counter(red_flags)

# Extract referral specialties
specialties = []
for r in rows:
    if r['specialist_referrals'].strip():
        parts = r['specialist_referrals'].split('&')
        for p in parts:
            p = p.strip().split('(')[0].strip()
            if p:
                specialties.append(p)
specialty_counts = Counter(specialties)

# Print summary
print("=== TRIAGE PRIORITIES ===")
for k,v in sorted(priority_counts.items()):
    label = {
        '1': 'Priority 1 - Critical',
        '2': 'Priority 2 - Emergency', 
        '3': 'Priority 3 - Urgent',
        '4': 'Priority 4 - Semi-urgent',
        '5': 'Priority 5 - Non-urgent'
    }.get(k, f'Priority {k}')
    print(f"  {label}: {v} patients")

print("\n=== TOP RED FLAGS ===")
for flag, count in red_flag_counts.most_common(5):
    print(f"  {flag}: {count}")

print("\n=== TOP SPECIALIST REFERRALS ===")
for spec, count in specialty_counts.most_common(5):
    print(f"  {spec}: {count}")

print(f"\nTotal patients processed: {len(rows)}")
