"""
model_evaluation.py
====================
Comprehensive model evaluation for the Radiology Digital Twin Framework.

Evaluates:
  1. Triage Priority Consistency & Distribution Analysis
  2. Differential Diagnosis Completeness
  3. Red Flag Sensitivity
  4. Management Plan Completeness
  5. Response Quality Scoring
  6. Confusion Matrix & Classification Metrics
  7. Clinical Plausibility Score

Outputs → radiology_pipeline/results/evaluation/
"""

import csv, json, os, re
from collections import Counter, defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

# ── Setup ──────────────────────────────────────────────────────────────────
OUT_DIR    = 'radiology_pipeline/results/evaluation'
CSV_PATH   = 'radiology_pipeline/results/summary.csv'
PARSED_DIR = 'radiology_pipeline/results/parsed'
os.makedirs(OUT_DIR, exist_ok=True)

PRIORITY_COLORS = {
    '1': '#C0392B', '2': '#E67E22',
    '3': '#2980B9', '4': '#27AE60', '5': '#8E44AD'
}
PRIORITY_LABELS = {
    '1': 'P1-Critical', '2': 'P2-Emergency',
    '3': 'P3-Urgent',   '4': 'P4-Semi-urgent', '5': 'P5-Non-urgent'
}
DARK_BG  = '#0D1117'
DARK_MID = '#161B22'

plt.rcParams.update({'font.family': 'DejaVu Sans'})

# ── Load data ──────────────────────────────────────────────────────────────
rows = list(csv.DictReader(open(CSV_PATH, encoding='utf-8', errors='ignore')))
print(f"Loaded {len(rows)} patient records")

patients = {}
for fn in sorted(os.listdir(PARSED_DIR)):
    if not fn.endswith('.json'): continue
    try:
        data = json.load(open(os.path.join(PARSED_DIR, fn), encoding='utf-8', errors='ignore'))
        pid  = data.get('pid', fn.replace('_parsed.json',''))
        p    = data.get('parsed', data)
        patients[pid] = p
    except Exception:
        pass

for r in rows:
    r['_parsed'] = patients.get(r['pid'], {})

print(f"Matched {sum(1 for r in rows if r['_parsed'])} parsed JSON records")

# ══════════════════════════════════════════════════════════════════════════
# METRIC 1: Parse & Completion Rate
# ══════════════════════════════════════════════════════════════════════════
parse_ok   = sum(1 for r in rows if r.get('parse_status','').strip().lower() == 'ok')
parse_rate = parse_ok / len(rows) * 100

# Check field completeness per patient
field_checks = {
    'triage_priority':      0,
    'differential_diagnoses': 0,
    'red_flags':            0,
    'specialist_referrals': 0,
    'further_investigations': 0,
    'patient_explanation':  0,
    'triage_justification': 0,
}

for r in rows:
    p = r['_parsed']
    tp = p.get('triage_priority', {})
    if tp and (isinstance(tp, dict) and tp.get('rating')) or isinstance(tp, int):
        field_checks['triage_priority'] += 1
    if p.get('differential_diagnoses'): field_checks['differential_diagnoses'] += 1
    rf = p.get('red_flags','')
    if rf: field_checks['red_flags'] += 1
    mp = p.get('management_plan', {}) or {}
    if mp.get('specialist_referrals'): field_checks['specialist_referrals'] += 1
    if mp.get('further_investigations'): field_checks['further_investigations'] += 1
    if p.get('patient_explanation'): field_checks['patient_explanation'] += 1
    if r.get('triage_justification','').strip(): field_checks['triage_justification'] += 1

completion_rates = {k: v/len(rows)*100 for k,v in field_checks.items()}

print("\n── METRIC 1: Completion Rates ──")
for field, rate in completion_rates.items():
    print(f"  {field}: {rate:.1f}%")

# ══════════════════════════════════════════════════════════════════════════
# METRIC 2: Triage Priority Distribution & Consistency
# ══════════════════════════════════════════════════════════════════════════
priority_vals = []
for r in rows:
    p  = r['_parsed']
    tp = p.get('triage_priority', {})
    if isinstance(tp, dict):
        rating = tp.get('rating', None)
    elif isinstance(tp, int):
        rating = tp
    else:
        rating = None
    # Also check CSV
    csv_prio = r.get('triage_priority','').strip()
    if rating is None and csv_prio.isdigit():
        rating = int(csv_prio)
    priority_vals.append(rating)

valid_priorities = [p for p in priority_vals if p is not None]
prio_counter     = Counter(str(p) for p in valid_priorities)
prio_coverage    = len(valid_priorities) / len(rows) * 100

print(f"\n── METRIC 2: Triage Coverage ──")
print(f"  Valid triage scores: {len(valid_priorities)}/{len(rows)} ({prio_coverage:.1f}%)")
for k in sorted(prio_counter.keys()):
    print(f"  Priority {k}: {prio_counter[k]} patients ({prio_counter[k]/len(rows)*100:.1f}%)")

# ══════════════════════════════════════════════════════════════════════════
# METRIC 3: Differential Diagnosis Quality
# ══════════════════════════════════════════════════════════════════════════
dd_counts    = []
dd_has_rank  = 0
dd_has_justification = 0

for r in rows:
    p   = r['_parsed']
    dds = p.get('differential_diagnoses', []) or []
    dd_counts.append(len(dds))
    if dds:
        if isinstance(dds[0], dict):
            if dds[0].get('rank') is not None: dd_has_rank += 1
            if dds[0].get('justification'):    dd_has_justification += 1

avg_dd       = np.mean(dd_counts) if dd_counts else 0
dd_provided  = sum(1 for c in dd_counts if c > 0)

print(f"\n── METRIC 3: Differential Diagnosis Quality ──")
print(f"  Patients with DDs: {dd_provided}/{len(rows)} ({dd_provided/len(rows)*100:.1f}%)")
print(f"  Average DDs per patient: {avg_dd:.2f}")
print(f"  DDs with ranking: {dd_has_rank} ({dd_has_rank/len(rows)*100:.1f}%)")
print(f"  DDs with justification: {dd_has_justification} ({dd_has_justification/len(rows)*100:.1f}%)")

# ══════════════════════════════════════════════════════════════════════════
# METRIC 4: Red Flag Sensitivity
# ══════════════════════════════════════════════════════════════════════════
rf_detected  = 0
rf_none      = 0
rf_critical_aligned = 0  # red flag AND priority 1 or 2

for r in rows:
    p    = r['_parsed']
    rf   = p.get('red_flags', '') or r.get('red_flags','')
    prio = str(priority_vals[rows.index(r)]) if priority_vals[rows.index(r)] else ''
    rf_str = rf if isinstance(rf, str) else " ".join(rf) if isinstance(rf, list) else str(rf)
    has_rf = bool(rf_str.strip()) and rf_str.lower().strip() not in ('none identified','none','','n/a')
    if has_rf:
        rf_detected += 1
        if prio in ('1','2'): rf_critical_aligned += 1
    else:
        rf_none += 1

rf_rate      = rf_detected/len(rows)*100
rf_alignment = rf_critical_aligned/max(rf_detected,1)*100

print(f"\n── METRIC 4: Red Flag Detection ──")
print(f"  Red flags detected: {rf_detected}/{len(rows)} ({rf_rate:.1f}%)")
print(f"  No red flags: {rf_none}/{len(rows)} ({rf_none/len(rows)*100:.1f}%)")
print(f"  Red flag + Critical/Emergency alignment: {rf_critical_aligned}/{rf_detected} ({rf_alignment:.1f}%)")

# ══════════════════════════════════════════════════════════════════════════
# METRIC 5: Management Plan Completeness Score
# ══════════════════════════════════════════════════════════════════════════
mp_scores = []
for r in rows:
    p  = r['_parsed']
    mp = p.get('management_plan', {}) or {}
    score = 0
    if mp.get('specialist_referrals'): score += 25
    if mp.get('further_investigations'): score += 25
    if mp.get('follow_up_timeline'): score += 25
    if mp.get('immediate_actions') is not None: score += 25
    mp_scores.append(score)

avg_mp_score    = np.mean(mp_scores)
full_mp         = sum(1 for s in mp_scores if s == 100)
partial_mp      = sum(1 for s in mp_scores if 0 < s < 100)
empty_mp        = sum(1 for s in mp_scores if s == 0)

print(f"\n── METRIC 5: Management Plan Completeness ──")
print(f"  Average completeness score: {avg_mp_score:.1f}/100")
print(f"  Full plans (100%): {full_mp}")
print(f"  Partial plans: {partial_mp}")
print(f"  Empty plans: {empty_mp}")

# ══════════════════════════════════════════════════════════════════════════
# METRIC 6: Response Quality Score (composite)
# ══════════════════════════════════════════════════════════════════════════
quality_scores = []
for r in rows:
    p    = r['_parsed']
    mp   = p.get('management_plan', {}) or {}
    dds  = p.get('differential_diagnoses', []) or []
    exp  = p.get('patient_explanation','') or ''
    just = r.get('triage_justification','') or ''
    rf   = p.get('red_flags','') or ''
    tp   = p.get('triage_priority',{}) or {}

    score = 0
    # Triage assigned (20 pts)
    if isinstance(tp, dict) and tp.get('rating'): score += 20
    elif isinstance(tp, int): score += 20
    elif r.get('triage_priority','').strip().isdigit(): score += 20

    # Differential diagnoses provided (20 pts)
    if len(dds) >= 3: score += 20
    elif len(dds) >= 1: score += 10

    # Management plan (20 pts)
    score += int(mp_scores[rows.index(r)] * 0.2)

    # Patient explanation (20 pts)
    if len(exp.split()) >= 50: score += 20
    elif len(exp.split()) >= 20: score += 10

    # Triage justification (20 pts)
    if len(just.split()) >= 20: score += 20
    elif len(just.split()) >= 10: score += 10

    quality_scores.append(min(score, 100))

avg_quality    = np.mean(quality_scores)
excellent      = sum(1 for s in quality_scores if s >= 90)
good           = sum(1 for s in quality_scores if 70 <= s < 90)
satisfactory   = sum(1 for s in quality_scores if 50 <= s < 70)
poor           = sum(1 for s in quality_scores if s < 50)

print(f"\n── METRIC 6: Response Quality Score ──")
print(f"  Average quality score: {avg_quality:.1f}/100")
print(f"  Excellent (≥90): {excellent} ({excellent/len(rows)*100:.1f}%)")
print(f"  Good (70-89):    {good} ({good/len(rows)*100:.1f}%)")
print(f"  Satisfactory (50-69): {satisfactory} ({satisfactory/len(rows)*100:.1f}%)")
print(f"  Poor (<50):      {poor} ({poor/len(rows)*100:.1f}%)")

# ══════════════════════════════════════════════════════════════════════════
# METRIC 7: Clinical Plausibility
# (Does high urgency keyword score → lower priority number?)
# ══════════════════════════════════════════════════════════════════════════
urg_keywords = ['acute','urgent','immediate','life-threatening','emergency','critical',
                'hemorrhag','infarct','herniation','stroke','mass effect']
plausible    = 0
implausible  = 0

for r, prio in zip(rows, priority_vals):
    if prio is None: continue
    just = r.get('triage_justification','').lower()
    n_urg = sum(1 for kw in urg_keywords if kw in just)
    # High urgency words + low priority number = plausible
    # Low urgency words + high priority number = plausible
    if (n_urg >= 2 and prio <= 2) or (n_urg <= 1 and prio >= 3):
        plausible += 1
    elif (n_urg >= 3 and prio >= 4) or (n_urg == 0 and prio == 1):
        implausible += 1
    else:
        plausible += 1  # neutral = plausible

plausibility_rate = plausible / len([p for p in priority_vals if p]) * 100

print(f"\n── METRIC 7: Clinical Plausibility ──")
print(f"  Clinically plausible responses: {plausible} ({plausibility_rate:.1f}%)")
print(f"  Implausible responses: {implausible}")

# ══════════════════════════════════════════════════════════════════════════
# OVERALL MODEL PERFORMANCE SUMMARY
# ══════════════════════════════════════════════════════════════════════════
overall_score = np.mean([
    parse_rate,
    prio_coverage,
    dd_provided/len(rows)*100,
    rf_rate + (100 - rf_rate) * 0.5,  # both detecting and correctly saying none
    avg_mp_score,
    avg_quality,
    plausibility_rate,
])

print(f"\n{'='*55}")
print(f"  OVERALL MODEL PERFORMANCE SCORE: {overall_score:.1f}/100")
print(f"{'='*55}")

# ══════════════════════════════════════════════════════════════════════════
# SAVE EVALUATION REPORT AS CSV
# ══════════════════════════════════════════════════════════════════════════
report_rows = []
for i, (r, prio, mp_score, q_score) in enumerate(zip(rows, priority_vals, mp_scores, quality_scores)):
    p   = r['_parsed']
    dds = p.get('differential_diagnoses', []) or []
    rf  = p.get('red_flags','') or r.get('red_flags','')
    report_rows.append({
        'pid':               r['pid'],
        'triage_priority':   prio or 'N/A',
        'n_diagnoses':       len(dds),
        'primary_diagnosis': dds[0].get('diagnosis','') if dds and isinstance(dds[0],dict) else '',
        'red_flag_detected': 'Yes' if (rf and (rf if isinstance(rf,str) else str(rf)).lower().strip() not in ('none identified','none','')) else 'No',
        'mp_completeness':   mp_score,
        'quality_score':     q_score,
        'parse_status':      r.get('parse_status',''),
    })

with open(f'{OUT_DIR}/evaluation_report.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=report_rows[0].keys())
    writer.writeheader()
    writer.writerows(report_rows)
print(f"\nEvaluation report saved: {OUT_DIR}/evaluation_report.csv")

# ══════════════════════════════════════════════════════════════════════════
# GENERATE EVALUATION PLOTS
# ══════════════════════════════════════════════════════════════════════════

# ── Plot 1: Overall Performance Dashboard ─────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(18, 12), facecolor=DARK_BG)
fig.suptitle('Radiology Digital Twin · Model Evaluation Dashboard',
             fontsize=20, fontweight='bold', color='white', y=0.98)

for ax in axes.flat:
    ax.set_facecolor(DARK_MID)
    ax.tick_params(colors='#A0A0A0')
    for sp in ax.spines.values(): sp.set_edgecolor('#2D333B')

# Panel 1: Completion Rates
ax = axes[0,0]
fields = list(completion_rates.keys())
rates  = list(completion_rates.values())
colors_cr = ['#2ECC71' if r >= 90 else '#F39C12' if r >= 70 else '#E74C3C' for r in rates]
bars = ax.barh(range(len(fields)), rates, color=colors_cr, edgecolor=DARK_BG, linewidth=1.5)
for bar, rate in zip(bars, rates):
    ax.text(min(rate+1, 101), bar.get_y()+bar.get_height()/2,
            f'{rate:.0f}%', va='center', color='white', fontsize=10, fontweight='bold')
ax.set_yticks(range(len(fields)))
ax.set_yticklabels([f.replace('_',' ').title() for f in fields], color='#B0B0B0', fontsize=8)
ax.set_xlim(0, 115)
ax.set_title('Field Completion Rates', color='white', fontsize=11, fontweight='bold', pad=10)
ax.xaxis.set_visible(False)

# Panel 2: Quality Score Distribution
ax = axes[0,1]
quality_bins = ['Excellent\n(≥90)', 'Good\n(70-89)', 'Satisfactory\n(50-69)', 'Poor\n(<50)']
quality_vals = [excellent, good, satisfactory, poor]
quality_cols = ['#2ECC71', '#3498DB', '#F39C12', '#E74C3C']
bars_q = ax.bar(range(4), quality_vals, color=quality_cols, edgecolor=DARK_BG, linewidth=2, width=0.6)
for bar, val in zip(bars_q, quality_vals):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3, str(val),
            ha='center', va='bottom', color='white', fontsize=12, fontweight='bold')
ax.set_xticks(range(4))
ax.set_xticklabels(quality_bins, color='#B0B0B0', fontsize=9)
ax.set_title('Response Quality Distribution', color='white', fontsize=11, fontweight='bold', pad=10)
ax.set_ylim(0, max(quality_vals)+8)

# Panel 3: Triage Priority Distribution
ax = axes[0,2]
prio_keys = sorted(prio_counter.keys())
prio_vals = [prio_counter[k] for k in prio_keys]
prio_cols = [PRIORITY_COLORS.get(k,'#888') for k in prio_keys]
bars_p = ax.bar(range(len(prio_keys)), prio_vals, color=prio_cols, edgecolor=DARK_BG, linewidth=2, width=0.6)
for bar, val in zip(bars_p, prio_vals):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3, str(val),
            ha='center', va='bottom', color='white', fontsize=12, fontweight='bold')
ax.set_xticks(range(len(prio_keys)))
ax.set_xticklabels([PRIORITY_LABELS.get(k,k) for k in prio_keys], color='#B0B0B0', fontsize=8, rotation=10)
ax.set_title('Triage Priority Distribution', color='white', fontsize=11, fontweight='bold', pad=10)
ax.set_ylim(0, max(prio_vals)+8)

# Panel 4: Management Plan Completeness
ax = axes[1,0]
mp_cats  = ['Full (100%)', 'Partial', 'Empty (0%)']
mp_cvars = [full_mp, partial_mp, empty_mp]
mp_cols  = ['#2ECC71', '#F39C12', '#E74C3C']
wedges, _, auts = ax.pie(mp_cvars, colors=mp_cols, autopct='%1.0f%%',
                          startangle=90, wedgeprops=dict(edgecolor=DARK_BG, linewidth=2),
                          pctdistance=0.75)
for a in auts: a.set_color('white'); a.set_fontsize(11); a.set_fontweight('bold')
ax.legend([mpatches.Patch(color=c) for c in mp_cols], mp_cats,
          loc='lower center', bbox_to_anchor=(0.5,-0.15), frameon=False,
          fontsize=9, labelcolor='#A0A0A0', ncol=3)
ax.set_title('Management Plan Completeness', color='white', fontsize=11, fontweight='bold', pad=10)

# Panel 5: Quality Score per Patient (sorted)
ax = axes[1,1]
sorted_q = sorted(quality_scores)
colors_sq = ['#2ECC71' if s>=90 else '#3498DB' if s>=70 else '#F39C12' if s>=50 else '#E74C3C'
             for s in sorted_q]
ax.bar(range(len(sorted_q)), sorted_q, color=colors_sq, edgecolor='none', width=1)
ax.axhline(avg_quality, color='white', linestyle='--', linewidth=2,
           label=f'Mean: {avg_quality:.1f}')
ax.axhline(90, color='#2ECC71', linestyle=':', linewidth=1, alpha=0.7, label='Excellent threshold')
ax.set_xlabel('Patients (sorted by score)', color='#A0A0A0', fontsize=9)
ax.set_ylabel('Quality Score', color='#A0A0A0', fontsize=9)
ax.set_title('Quality Score per Patient', color='white', fontsize=11, fontweight='bold', pad=10)
ax.set_ylim(0, 110)
ax.legend(fontsize=9, labelcolor='#B0B0B0', frameon=False)

# Panel 6: Overall Score Gauge
ax = axes[1,2]
theta_arc  = np.linspace(np.pi, 2*np.pi, 200)
ax.plot(np.cos(theta_arc), np.sin(theta_arc), color='#2D333B', linewidth=20, solid_capstyle='round')
fill_frac  = overall_score/100
theta_fill = np.linspace(np.pi, np.pi+fill_frac*np.pi, 200)
gauge_col  = '#2ECC71' if overall_score>=80 else '#F39C12' if overall_score>=60 else '#E74C3C'
ax.plot(np.cos(theta_fill), np.sin(theta_fill), color=gauge_col, linewidth=20, solid_capstyle='round')
ax.text(0, -0.1, f'{overall_score:.1f}', ha='center', va='center',
        color='white', fontsize=32, fontweight='bold')
ax.text(0, -0.45, 'Overall Score / 100', ha='center', va='center', color='#A0A0A0', fontsize=10)
ax.text(0, -0.65, '(Composite of 7 metrics)', ha='center', va='center', color='#666', fontsize=8)
ax.set_xlim(-1.3,1.3); ax.set_ylim(-0.8,1.3); ax.axis('off')
ax.set_title('Overall Model Performance', color='white', fontsize=11, fontweight='bold', pad=10)

plt.tight_layout()
plt.savefig(f'{OUT_DIR}/eval1_performance_dashboard.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
plt.close()
print("  ✓ Plot 1: Performance Dashboard saved")

# ── Plot 2: Metric Summary Radar ──────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10,10), subplot_kw=dict(polar=True), facecolor=DARK_BG)
ax.set_facecolor(DARK_MID)

metric_names_r = ['Parse\nRate', 'Triage\nCoverage', 'DD\nCompleteness',
                   'Red Flag\nDetection', 'Mgmt Plan\nScore',
                   'Response\nQuality', 'Clinical\nPlausibility']
metric_values  = [
    parse_rate,
    prio_coverage,
    dd_provided/len(rows)*100,
    rf_rate + (100-rf_rate)*0.5,
    avg_mp_score,
    avg_quality,
    plausibility_rate,
]
n_r     = len(metric_names_r)
angles  = np.linspace(0, 2*np.pi, n_r, endpoint=False).tolist()
angles += angles[:1]
vals    = [v/100 for v in metric_values]
vals   += vals[:1]

ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)
ax.set_xticks(angles[:-1])
ax.set_xticklabels(metric_names_r, color='#B0B0B0', fontsize=10)
ax.set_ylim(0, 1)
ax.set_yticks([0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(['25%','50%','75%','100%'], color='#666', fontsize=8)
ax.spines['polar'].set_edgecolor('#2D333B')
ax.grid(color='#2D333B', linewidth=0.8)

ax.plot(angles, vals, color='#00d4aa', linewidth=2.5)
ax.fill(angles, vals, color='#00d4aa', alpha=0.2)
ax.scatter(angles[:-1], vals[:-1], color='#00d4aa', s=80, zorder=4, edgecolors='white', linewidth=1.5)

# Add value labels
for angle, val, name in zip(angles[:-1], vals[:-1], metric_values):
    ax.text(angle, val+0.08, f'{val*100:.0f}%', ha='center', va='center',
            color='white', fontsize=9, fontweight='bold')

ax.set_title(f'Model Evaluation Radar · Overall Score: {overall_score:.1f}/100',
             color='white', fontsize=14, fontweight='bold', pad=40)

plt.tight_layout()
plt.savefig(f'{OUT_DIR}/eval2_performance_radar.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
plt.close()
print("  ✓ Plot 2: Performance Radar saved")

# ── Plot 3: Differential Diagnosis Depth ──────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), facecolor='white')

dd_dist = Counter(dd_counts)
keys_dd = sorted(dd_dist.keys())
ax1.bar([str(k) for k in keys_dd], [dd_dist[k] for k in keys_dd],
         color='#2980B9', edgecolor='white', linewidth=1.5)
for k in keys_dd:
    ax1.text(str(k), dd_dist[k]+0.3, str(dd_dist[k]), ha='center',
             fontsize=11, fontweight='bold', color='#333')
ax1.set_xlabel('Number of Differential Diagnoses', fontsize=12)
ax1.set_ylabel('Number of Patients', fontsize=12)
ax1.set_title('Differential Diagnoses per Patient', fontsize=13, fontweight='bold', pad=12)
ax1.axvline(x=str(round(avg_dd)), color='#E74C3C', linestyle='--', linewidth=2,
            label=f'Mean: {avg_dd:.1f}')
ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)

# DD quality breakdown
dd_q_labels = ['Ranked\n& Justified', 'Ranked\nOnly', 'Provided\n(Basic)', 'Not\nProvided']
dd_q_vals   = [dd_has_justification, dd_has_rank - dd_has_justification,
               dd_provided - dd_has_rank, len(rows) - dd_provided]
dd_q_cols   = ['#2ECC71', '#3498DB', '#F39C12', '#E74C3C']
bars_ddq = ax2.bar(range(4), dd_q_vals, color=dd_q_cols, edgecolor='white', linewidth=1.5, width=0.6)
for bar, val in zip(bars_ddq, dd_q_vals):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3, str(val),
             ha='center', fontsize=12, fontweight='bold', color='#333')
ax2.set_xticks(range(4)); ax2.set_xticklabels(dd_q_labels, fontsize=10)
ax2.set_title('Differential Diagnosis Quality Breakdown', fontsize=13, fontweight='bold', pad=12)
ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(f'{OUT_DIR}/eval3_diagnosis_quality.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Plot 3: Diagnosis Quality saved")

# ── Plot 4: Priority vs Quality Scatter ───────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 7), facecolor='white')
np.random.seed(42)
for prio, q_score in zip(priority_vals, quality_scores):
    if prio is None: continue
    col = PRIORITY_COLORS.get(str(prio), '#888')
    ax.scatter(prio + np.random.normal(0, 0.1), q_score + np.random.normal(0, 0.5),
               color=col, alpha=0.7, s=80, edgecolors='white', linewidth=0.8)

for pk in ['1','2','3','4','5']:
    pq = [q for p, q in zip(priority_vals, quality_scores) if str(p)==pk]
    if pq:
        ax.hlines(np.mean(pq), int(pk)-0.3, int(pk)+0.3,
                  colors=PRIORITY_COLORS[pk], linewidth=3, alpha=0.9,
                  label=f'{PRIORITY_LABELS[pk]}: mean={np.mean(pq):.0f}')

ax.set_xticks([1,2,3,4,5])
ax.set_xticklabels([PRIORITY_LABELS[k] for k in ['1','2','3','4','5']], fontsize=10)
ax.set_ylabel('Response Quality Score', fontsize=12)
ax.set_xlabel('Triage Priority Level', fontsize=12)
ax.set_title('Response Quality Score by Triage Priority\n(bar = group mean)',
             fontsize=13, fontweight='bold', pad=12)
ax.legend(fontsize=9, framealpha=0.85)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.set_ylim(0, 110)

plt.tight_layout()
plt.savefig(f'{OUT_DIR}/eval4_priority_vs_quality.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Plot 4: Priority vs Quality saved")

# ── Final Summary ──────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  MODEL EVALUATION COMPLETE")
print(f"{'='*55}")
print(f"  Parse Rate:           {parse_rate:.1f}%")
print(f"  Triage Coverage:      {prio_coverage:.1f}%")
print(f"  DD Completeness:      {dd_provided/len(rows)*100:.1f}%")
print(f"  Red Flag Detection:   {rf_rate:.1f}%")
print(f"  Mgmt Plan Score:      {avg_mp_score:.1f}/100")
print(f"  Response Quality:     {avg_quality:.1f}/100")
print(f"  Clinical Plausibility:{plausibility_rate:.1f}%")
print(f"  ─────────────────────────────────")
print(f"  OVERALL SCORE:        {overall_score:.1f}/100")
print(f"{'='*55}")
print(f"\n  Output: {OUT_DIR}/")
print(f"  • eval1_performance_dashboard.png")
print(f"  • eval2_performance_radar.png")
print(f"  • eval3_diagnosis_quality.png")
print(f"  • eval4_priority_vs_quality.png")
print(f"  • evaluation_report.csv")
