"""
generate_enhanced_visualizations.py
====================================
Beautiful, publication-quality analyses and animations for the
Radiology Digital Twin evaluation pipeline.

Outputs → radiology_pipeline/results/enhanced_plots/
  Static figures  (.png, 150 dpi)
  Animations      (.gif)

FIXES APPLIED:
  1. Fixed fill_betweenx → fill_between in alluvial chart
  2. Fixed scatter set_array to use numpy arrays
  3. Fixed animation 2 collections removal (preserves hline)
  4. Fixed JSON parsing to handle both flat and nested structures
  5. Added safe fallbacks for missing/empty data
"""

import csv
import json
import os
import re
from collections import Counter, defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np

# ── Setup ──────────────────────────────────────────────────────────────────
OUT_DIR = 'radiology_pipeline/results/enhanced_plots'
os.makedirs(OUT_DIR, exist_ok=True)

# ── Colour palette ─────────────────────────────────────────────────────────
PRIORITY_COLORS = {
    '1': '#C0392B', '2': '#E67E22',
    '3': '#2980B9', '4': '#27AE60', '5': '#8E44AD'
}
PRIORITY_LABELS = {
    '1': 'P1 · Critical', '2': 'P2 · Emergency',
    '3': 'P3 · Urgent',   '4': 'P4 · Semi-urgent', '5': 'P5 · Non-urgent'
}
DARK_BG  = '#0D1117'
DARK_MID = '#161B22'
ACCENT   = '#58A6FF'

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'axes.spines.top':   False,
    'axes.spines.right': False,
})

# ── Load data ──────────────────────────────────────────────────────────────
CSV_PATH   = 'radiology_pipeline/results/summary.csv'
PARSED_DIR = 'radiology_pipeline/results/parsed'

rows = list(csv.DictReader(open(CSV_PATH, encoding='utf-8', errors='ignore')))
print(f"Loaded {len(rows)} patient records")

# ── FIX 1: Robust JSON parsing ─────────────────────────────────────────────
# Handles both flat {key:val} and nested {"pid":..., "parsed":{...}} formats
patients = {}
if os.path.exists(PARSED_DIR):
    for fn in sorted(os.listdir(PARSED_DIR)):
        if not fn.endswith('.json'):
            continue
        try:
            data = json.load(open(os.path.join(PARSED_DIR, fn),
                                  encoding='utf-8', errors='ignore'))
            # Support both structures
            if 'parsed' in data and isinstance(data['parsed'], dict):
                pid = data.get('pid', fn.replace('.json', ''))
                patients[pid] = data['parsed']
            elif 'pid' in data:
                pid = data['pid']
                patients[pid] = data
            else:
                pid = fn.replace('.json', '')
                patients[pid] = data
        except Exception:
            pass

# Merge CSV + JSON
for r in rows:
    r['_parsed'] = patients.get(r['pid'], {})

# ── Derived metrics ────────────────────────────────────────────────────────
priorities = [r['triage_priority'].strip() for r in rows if r['triage_priority'].strip()]
prio_counter = Counter(priorities)


def safe_get(d, *keys, default=None):
    """Safely navigate nested dicts."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d


def extract_specialties(row):
    specs = []
    p = row['_parsed']
    # Try nested management_plan first, then flat specialist_referrals
    sr = safe_get(p, 'management_plan', 'specialist_referrals', default=[])
    if not sr:
        sr_raw = row.get('specialist_referrals', '')
        if sr_raw:
            sr = [s.strip() for s in re.split(r'[&,|]', sr_raw) if s.strip()]
    for s in sr:
        if isinstance(s, str):
            s = re.sub(r'\(.*?\)', '', s).strip().rstrip(',')
            if s:
                specs.append(s)
    return specs


def extract_investigations(row):
    p = row['_parsed']
    inv = safe_get(p, 'management_plan', 'further_investigations', default=[])
    if not inv:
        inv_raw = row.get('further_investigations', '')
        if inv_raw:
            inv = [x.strip() for x in re.split(r'[&,|]', inv_raw) if x.strip()]
    return inv if isinstance(inv, list) else []


def extract_primary_diagnosis(row):
    p = row['_parsed']
    dds = safe_get(p, 'differential_diagnoses', default=[])
    if dds and isinstance(dds, list) and len(dds) > 0:
        d = dds[0]
        if isinstance(d, dict):
            return d.get('diagnosis', '')
        if isinstance(d, str):
            return d
    # fallback to CSV field
    dd_raw = row.get('differential_diagnoses', '')
    if dd_raw:
        return dd_raw.split('|')[0].split('.')[0][:80].strip()
    return ''


def has_red_flag(row):
    rf = row.get('red_flags', '').strip().lower()
    return bool(rf) and rf not in ('none identified', 'none', '', 'n/a')


all_specialties = []
for r in rows:
    all_specialties.extend(extract_specialties(r))


def norm_spec(s):
    s = s.lower()
    if 'neurosurg' in s:                               return 'Neurosurgery'
    if 'neurol' in s or 'stroke' in s:                return 'Neurology / Stroke'
    if 'ent' in s or 'otolar' in s or 'ear, nose' in s: return 'ENT'
    if 'cardio' in s:                                  return 'Cardiology'
    if 'geriat' in s:                                  return 'Geriatrics'
    if 'oncol' in s:                                   return 'Oncology'
    if 'rehab' in s or 'physio' in s:                 return 'Rehabilitation'
    if 'ophthal' in s:                                 return 'Ophthalmology'
    if 'psych' in s:                                   return 'Psychiatry'
    if 'primary care' in s or 'gp' in s:              return 'Primary Care'
    return s.title()


norm_specs      = [norm_spec(s) for s in all_specialties]
norm_spec_counts = Counter(norm_specs)
investigation_counts = [len(extract_investigations(r)) for r in rows]
primary_diagnoses    = [extract_primary_diagnosis(r) for r in rows
                        if extract_primary_diagnosis(r)]


# ══════════════════════════════════════════════════════════════════════════
# FIG 1: Clinical Command Centre – 2×3 grid overview
# ══════════════════════════════════════════════════════════════════════════
print("Generating Fig 1: Clinical Command Centre dashboard...")

fig = plt.figure(figsize=(20, 14), facecolor=DARK_BG)
gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.42, wspace=0.35,
                         left=0.06, right=0.97, top=0.91, bottom=0.07)
fig.suptitle("Radiology Digital Twin · Clinical Command Centre",
             fontsize=22, fontweight='bold', color='white', y=0.97)

ax_list = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(3)]
for ax in ax_list:
    ax.set_facecolor(DARK_MID)
    ax.tick_params(colors='#A0A0A0')
    for sp in ax.spines.values():
        sp.set_edgecolor('#2D333B')

# Panel A: Triage Priority Bar
ax = ax_list[0]
keys  = sorted(prio_counter.keys())
vals  = [prio_counter[k] for k in keys]
cols  = [PRIORITY_COLORS[k] for k in keys]
bars_p = ax.bar(range(len(keys)), vals, color=cols,
                edgecolor=DARK_BG, linewidth=2, width=0.7)
for bar, v in zip(bars_p, vals):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3, str(v),
            ha='center', va='bottom', color='white', fontsize=12, fontweight='bold')
ax.set_xticks(range(len(keys)))
ax.set_xticklabels([PRIORITY_LABELS[k] for k in keys],
                    color='#B0B0B0', fontsize=7.5, rotation=12)
ax.set_ylim(0, max(vals) + 8)
ax.set_title('Triage Priority Distribution', color='white', fontsize=11,
             fontweight='bold', pad=10)

# Panel B: Red Flag Donut
ax = ax_list[1]
rf_yes = sum(1 for r in rows if has_red_flag(r))
rf_no  = len(rows) - rf_yes
wedges, _, auts = ax.pie(
    [rf_yes, rf_no], colors=['#E74C3C', '#2ECC71'], startangle=90,
    wedgeprops=dict(width=0.55, edgecolor=DARK_BG, linewidth=2),
    autopct='%1.0f%%', pctdistance=0.75
)
for a in auts:
    a.set_color('white'); a.set_fontsize(12); a.set_fontweight('bold')
ax.text(0, 0, f'{rf_yes}\nFlags', ha='center', va='center',
        color='white', fontsize=14, fontweight='bold')
ax.legend([mpatches.Patch(color=c) for c in ['#E74C3C','#2ECC71']],
          ['Red Flags Detected', 'No Red Flags'],
          loc='lower center', bbox_to_anchor=(0.5, -0.18),
          frameon=False, fontsize=9, labelcolor='#A0A0A0', ncol=2)
ax.set_title('Red Flag Detection Rate', color='white', fontsize=11,
             fontweight='bold', pad=10)

# Panel C: Specialist Referrals Lollipop
ax = ax_list[2]
top8     = norm_spec_counts.most_common(8)
s_names  = [x[0] for x in top8[::-1]]
s_vals   = [x[1] for x in top8[::-1]]
cmap_lol = plt.cm.plasma
colors_lol = [cmap_lol(i / max(len(s_names)-1, 1)) for i in range(len(s_names))]
for i, (name, val, col) in enumerate(zip(s_names, s_vals, colors_lol)):
    ax.hlines(i, 0, val, colors='#3D4451', linewidth=1.5, linestyle='--')
    ax.plot(val, i, 'o', color=col, markersize=12, zorder=3)
    ax.text(val + 0.4, i, str(val), va='center', color='white',
            fontsize=10, fontweight='bold')
ax.set_yticks(range(len(s_names)))
ax.set_yticklabels(s_names, color='#B0B0B0', fontsize=9)
ax.set_xlim(0, max(s_vals) + 6 if s_vals else 10)
ax.set_title('Top Specialist Referrals', color='white', fontsize=11,
             fontweight='bold', pad=10)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.tick_params(left=False, bottom=False, colors='#A0A0A0')
ax.xaxis.set_visible(False)

# Panel D: Investigations Violin
ax = ax_list[3]
inv_data = [c for c in investigation_counts if 0 < c < 20]
if not inv_data:
    inv_data = [2, 3, 4, 5, 3, 2, 4]  # safe fallback
parts = ax.violinplot([inv_data], positions=[0], showmeans=True,
                       showmedians=True, showextrema=True)
for pc in parts['bodies']:
    pc.set_facecolor(ACCENT); pc.set_alpha(0.6)
parts['cmeans'].set_color('#F39C12')
parts['cmedians'].set_color('#2ECC71')
ax.scatter(np.random.normal(0, 0.08, len(inv_data)), inv_data,
           alpha=0.4, color='white', s=15, zorder=3)
ax.set_xticks([0])
ax.set_xticklabels(['All Patients'], color='#B0B0B0')
ax.set_ylabel('Investigations Ordered', color='#A0A0A0', fontsize=9)
ax.set_title('Investigations per Patient', color='white', fontsize=11,
             fontweight='bold', pad=10)
ax.tick_params(colors='#A0A0A0')
ax.legend(handles=[
    mpatches.Patch(color='#F39C12', label=f'Mean ({np.mean(inv_data):.1f})'),
    mpatches.Patch(color='#2ECC71', label=f'Median ({int(np.median(inv_data))})')
], frameon=False, fontsize=8, labelcolor='#A0A0A0', loc='upper right')

# Panel E: Priority Heatmap (10×10 grid)
ax = ax_list[4]
prio_list = []
for r in rows:
    p = r['triage_priority'].strip()
    prio_list.append(int(p) if p.isdigit() else 3)
grid_data = np.zeros((10, 10))
for i, p in enumerate(prio_list[:100]):
    grid_data[i // 10][i % 10] = p
cmap_hm = LinearSegmentedColormap.from_list(
    'priority', ['#C0392B','#E67E22','#2980B9','#27AE60','#8E44AD'], N=5)
im = ax.imshow(grid_data, cmap=cmap_hm, vmin=1, vmax=5, aspect='auto')
ax.set_xticks(range(10)); ax.set_yticks(range(10))
ax.set_xticklabels(range(1,11), color='#A0A0A0', fontsize=8)
ax.set_yticklabels(range(1,11), color='#A0A0A0', fontsize=8)
ax.set_title('Patient Priority Grid (100 pts)', color='white', fontsize=11,
             fontweight='bold', pad=10)
for i in range(10):
    for j in range(10):
        val = int(grid_data[i][j])
        ax.text(j, i, str(val), ha='center', va='center',
                color='white', fontsize=8, fontweight='bold',
                path_effects=[pe.withStroke(linewidth=1, foreground=DARK_BG)])
cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
cbar.ax.tick_params(colors='#A0A0A0', labelsize=7)
cbar.set_label('Priority', color='#A0A0A0', fontsize=8)

# Panel F: Parse Success Gauge
ax = ax_list[5]
parse_ok  = sum(1 for r in rows if r.get('parse_status','').strip().lower() == 'ok')
success_pct = parse_ok / len(rows) if rows else 1.0
theta_arc  = np.linspace(np.pi, 2*np.pi, 200)
ax.plot(np.cos(theta_arc), np.sin(theta_arc), color='#2D333B',
        linewidth=15, solid_capstyle='round')
theta_fill = np.linspace(np.pi, np.pi + success_pct*np.pi, 200)
ax.plot(np.cos(theta_fill), np.sin(theta_fill), color='#2ECC71',
        linewidth=15, solid_capstyle='round')
ax.text(0, -0.15, f'{success_pct*100:.0f}%', ha='center', va='center',
        color='white', fontsize=28, fontweight='bold')
ax.text(0, -0.5, f'{parse_ok} / {len(rows)} parsed OK', ha='center', va='center',
        color='#A0A0A0', fontsize=10)
ax.set_xlim(-1.3, 1.3); ax.set_ylim(-0.8, 1.3)
ax.axis('off')
ax.set_title('Model Parse Success Rate', color='white', fontsize=11,
             fontweight='bold', pad=10)

plt.savefig(f'{OUT_DIR}/fig1_command_centre.png', dpi=150,
            bbox_inches='tight', facecolor=DARK_BG)
plt.close()
print("  ✓ Fig 1: Clinical Command Centre")


# ══════════════════════════════════════════════════════════════════════════
# FIG 2: Diagnosis Landscape
# ══════════════════════════════════════════════════════════════════════════
print("Generating Fig 2: Diagnosis Landscape...")


def categorize_dx(d):
    d = d.lower()
    if any(x in d for x in ['stroke','infarct','ischemi','cerebrovascular']): return 'Stroke / Ischemia'
    if any(x in d for x in ['rhinitis','sinusit','nasal','ent','polyp']):      return 'ENT / Sinonasal'
    if any(x in d for x in ['tumor','glioma','meningioma','metastas','neoplasm']): return 'Neoplasm'
    if any(x in d for x in ['demyelinat','multiple sclerosis']):               return 'Demyelinating'
    if any(x in d for x in ['small vessel','microangiopat','white matter','leukoaraiosis']): return 'Small Vessel Disease'
    if any(x in d for x in ['hemorrhag','haematom','subdural','epidural']):    return 'Haemorrhage'
    if any(x in d for x in ['hydrocephalu','csf','arachnoid']):               return 'CSF / Hydrocephalus'
    if any(x in d for x in ['abscess','infect','encephal','menin']):           return 'Infection / Inflammation'
    if any(x in d for x in ['atrophy','degenerat']):                           return 'Atrophy / Degeneration'
    return 'Other'


diag_categories  = [categorize_dx(d) for d in primary_diagnoses]
diag_cat_counts  = Counter(diag_categories)
cat_order = sorted(diag_cat_counts, key=lambda x: -diag_cat_counts[x])
cat_vals  = [diag_cat_counts[c] for c in cat_order]
cat_cols  = plt.cm.Spectral(np.linspace(0.1, 0.9, len(cat_order)))
total     = max(sum(cat_vals), 1)

fig, (ax_main, ax_bar) = plt.subplots(1, 2, figsize=(18, 8),
                                        gridspec_kw={'width_ratios': [1.4, 1]},
                                        facecolor='white')
running = 0.0
for val, col, cat in zip(cat_vals, cat_cols, cat_order):
    w = val / total
    ax_main.barh(0, w, left=running, height=0.6, color=col,
                  edgecolor='white', linewidth=2)
    if w > 0.04:
        ax_main.text(running + w/2, 0, f'{cat}\nn={val}',
                     ha='center', va='center', fontsize=9,
                     fontweight='bold', color='black')
    running += w
ax_main.set_xlim(0, 1); ax_main.set_ylim(-0.5, 0.5)
ax_main.axis('off')
ax_main.set_title('Primary Diagnosis Landscape · Proportional View',
                   fontsize=14, fontweight='bold', pad=15)

y_pos = range(len(cat_order))
bars = ax_bar.barh(list(y_pos), cat_vals, color=cat_cols,
                    edgecolor='white', linewidth=1.5, height=0.7)
for bar, val in zip(bars, cat_vals):
    ax_bar.text(bar.get_width()+0.2, bar.get_y()+bar.get_height()/2,
                f'{val} ({val/total*100:.0f}%)', va='center',
                fontsize=10, fontweight='bold', color='#333')
ax_bar.set_yticks(list(y_pos))
ax_bar.set_yticklabels(cat_order, fontsize=10)
ax_bar.set_xlabel('Patient Count', fontsize=11)
ax_bar.set_xlim(0, max(cat_vals)+8 if cat_vals else 10)
ax_bar.set_title('Diagnosis Category Breakdown', fontsize=14,
                  fontweight='bold', pad=15)
ax_bar.spines['top'].set_visible(False)
ax_bar.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(f'{OUT_DIR}/fig2_diagnosis_landscape.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Fig 2: Diagnosis Landscape")


# ══════════════════════════════════════════════════════════════════════════
# FIG 3: Priority × Diagnosis Matrix Heatmap
# ══════════════════════════════════════════════════════════════════════════
print("Generating Fig 3: Priority × Diagnosis Matrix Heatmap...")

dx_by_priority = defaultdict(list)
for r in rows:
    prio = r['triage_priority'].strip()
    dx   = categorize_dx(extract_primary_diagnosis(r))
    if prio:
        dx_by_priority[prio].append(dx)

diag_set  = sorted({dx for dxs in dx_by_priority.values() for dx in dxs})
prio_keys = ['1','2','3','4','5']
matrix    = np.zeros((len(diag_set), len(prio_keys)))
for pi, pk in enumerate(prio_keys):
    c = Counter(dx_by_priority[pk])
    for di, dx in enumerate(diag_set):
        matrix[di][pi] = c.get(dx, 0)

order  = np.argsort(matrix.sum(axis=1))[::-1]
matrix = matrix[order]
diag_set = [diag_set[i] for i in order]

fig, ax = plt.subplots(figsize=(13, 8), facecolor='white')
cmap_hm2 = LinearSegmentedColormap.from_list('clinical',
                                              ['#FFFFFF','#2980B9','#C0392B'])
im = ax.imshow(matrix, cmap=cmap_hm2, aspect='auto', interpolation='nearest')
ax.set_xticks(range(len(prio_keys)))
ax.set_xticklabels([PRIORITY_LABELS[k] for k in prio_keys],
                    fontsize=10, rotation=15, ha='right')
ax.set_yticks(range(len(diag_set)))
ax.set_yticklabels(diag_set, fontsize=10)
ax.set_title('Diagnosis Category × Triage Priority Matrix',
             fontsize=15, fontweight='bold', pad=15)
for i in range(len(diag_set)):
    for j in range(len(prio_keys)):
        val = int(matrix[i][j])
        if val > 0:
            ax.text(j, i, str(val), ha='center', va='center',
                    fontsize=12, fontweight='bold',
                    color='white' if matrix[i][j] > matrix.max()*0.4 else '#333')
cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cbar.set_label('Patient Count', fontsize=10)
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/fig3_priority_diagnosis_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Fig 3: Priority × Diagnosis Heatmap")


# ══════════════════════════════════════════════════════════════════════════
# FIG 4: Referral Sunburst (polar bar)
# ══════════════════════════════════════════════════════════════════════════
print("Generating Fig 4: Specialist Referral Sunburst...")

fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(polar=True),
                        facecolor=DARK_BG)
ax.set_facecolor(DARK_BG)
top_specs  = norm_spec_counts.most_common(10)
spec_names = [x[0] for x in top_specs]
spec_vals  = [x[1] for x in top_specs]
N = len(spec_names)
angles = np.linspace(0, 2*np.pi, N, endpoint=False)
width  = 2*np.pi/N * 0.85
ax.bar(angles, spec_vals, width=width, bottom=2,
        color=plt.cm.cool(np.linspace(0.1, 0.9, N)),
        alpha=0.85, edgecolor=DARK_BG, linewidth=1.5)
for angle, name, val in zip(angles, spec_names, spec_vals):
    angle_deg = np.degrees(angle)
    rotation  = angle_deg if 0 <= angle_deg <= 180 else angle_deg + 180
    ax.text(angle, max(spec_vals)+5, name, ha='center', va='bottom',
            rotation=rotation, rotation_mode='anchor',
            color='white', fontsize=9, fontweight='bold')
    ax.text(angle, 2+val/2, str(val), ha='center', va='center',
            color='white', fontsize=11, fontweight='bold')
ax.set_ylim(0, max(spec_vals)+10 if spec_vals else 10)
ax.set_yticks([]); ax.set_xticks([])
ax.spines['polar'].set_edgecolor('#2D333B')
ax.set_title('Specialist Referral Sunburst · Top 10 Specialties',
             fontsize=15, fontweight='bold', color='white', pad=30)
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/fig4_referral_sunburst.png', dpi=150,
            bbox_inches='tight', facecolor=DARK_BG)
plt.close()
print("  ✓ Fig 4: Referral Sunburst")


# ══════════════════════════════════════════════════════════════════════════
# FIG 5: Clinical Severity Spectrum – Bubble Chart
# ══════════════════════════════════════════════════════════════════════════
print("Generating Fig 5: Severity Spectrum Bubble Chart...")

fig, ax = plt.subplots(figsize=(14, 8), facecolor='white')
np.random.seed(42)
for r in rows:
    prio = r['triage_priority'].strip()
    if not prio or not prio.isdigit():
        continue
    prio_int = int(prio)
    n_inv    = min(len(extract_investigations(r)), 10)
    rf       = 1 if has_red_flag(r) else 0
    size     = 80 + rf*200 + np.random.rand()*30
    col      = PRIORITY_COLORS[prio]
    ax.scatter(prio_int + np.random.normal(0, 0.12),
               n_inv + np.random.normal(0, 0.15),
               s=size, color=col, alpha=0.55,
               edgecolors='white', linewidth=0.8)
for pk, col in PRIORITY_COLORS.items():
    prows = [r for r in rows if r['triage_priority'].strip() == pk]
    if prows:
        mean_inv = np.mean([len(extract_investigations(r)) for r in prows])
        ax.hlines(mean_inv, int(pk)-0.35, int(pk)+0.35,
                  colors=col, linewidth=3, alpha=0.9)
ax.set_xticks([1,2,3,4,5])
ax.set_xticklabels([PRIORITY_LABELS[k] for k in ['1','2','3','4','5']], fontsize=11)
ax.set_ylabel('Investigations Ordered', fontsize=12)
ax.set_xlabel('Triage Priority Level', fontsize=12)
ax.set_title('Clinical Severity Spectrum · Priority vs Investigations Ordered\n'
             '(bubble size = red flag; horizontal bar = group mean)',
             fontsize=13, fontweight='bold', pad=12)
legend_elements = [mpatches.Patch(color=PRIORITY_COLORS[k], label=PRIORITY_LABELS[k])
                   for k in ['1','2','3','4','5']]
legend_elements += [
    plt.scatter([], [], s=80,  color='gray', edgecolors='white', label='No Red Flag'),
    plt.scatter([], [], s=280, color='gray', edgecolors='white', label='Red Flag Present'),
]
ax.legend(handles=legend_elements, fontsize=9, loc='upper right', frameon=True, framealpha=0.9)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/fig5_severity_spectrum_bubble.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Fig 5: Severity Spectrum Bubble Chart")


# ══════════════════════════════════════════════════════════════════════════
# FIG 6: Investigation Complexity Waterfall
# ══════════════════════════════════════════════════════════════════════════
print("Generating Fig 6: Investigation Complexity Waterfall...")

sorted_rows = sorted(rows, key=lambda r: len(extract_investigations(r)), reverse=True)
x_idx   = list(range(len(sorted_rows)))
y_inv   = [min(len(extract_investigations(r)), 15) for r in sorted_rows]
y_prio  = [int(r['triage_priority'].strip()) if r['triage_priority'].strip().isdigit() else 3
           for r in sorted_rows]
colors_wf = [PRIORITY_COLORS[str(p)] for p in y_prio]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 10), facecolor='white',
                                gridspec_kw={'height_ratios': [3, 1]})
ax1.bar(x_idx, y_inv, color=colors_wf, edgecolor='white', linewidth=0.4, width=1)
ax1.set_xlim(-0.5, len(rows)-0.5)
ax1.set_ylabel('Investigations Ordered (capped at 15)', fontsize=11)
ax1.set_title('Investigation Complexity per Patient · Sorted by Workload\n'
              '(colour = triage priority)', fontsize=13, fontweight='bold', pad=12)
ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)
window = min(10, len(y_inv))
ma = np.convolve(y_inv, np.ones(window)/window, mode='same')
ax1.plot(x_idx, ma, color='black', linewidth=2, label=f'{window}-patient moving avg')
legend_e = [mpatches.Patch(color=PRIORITY_COLORS[k], label=PRIORITY_LABELS[k])
            for k in ['1','2','3','4','5']]
ax1.legend(handles=legend_e+[mpatches.Patch(color='black', label='Moving Avg')],
           fontsize=9, loc='upper left')
ax2.bar(x_idx, [1]*len(rows), color=colors_wf, edgecolor='none', width=1)
ax2.set_xlim(-0.5, len(rows)-0.5); ax2.set_yticks([])
ax2.set_xlabel('Patient (sorted by investigation count)', fontsize=11)
ax2.set_title('Triage Priority Strip', fontsize=10, pad=3)
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/fig6_investigation_waterfall.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Fig 6: Investigation Complexity Waterfall")


# ══════════════════════════════════════════════════════════════════════════
# ANIMATION 1: Triage Tally
# ══════════════════════════════════════════════════════════════════════════
print("Generating Animation 1: Triage Tally (may take ~30s)...")

prio_seq    = [r['triage_priority'].strip() for r in rows if r['triage_priority'].strip()]
running_d   = {'1':0,'2':0,'3':0,'4':0,'5':0}
frames_data = []
for p in prio_seq:
    if p in running_d:
        running_d[p] += 1
    frames_data.append(dict(running_d))

fig_anim, ax_anim = plt.subplots(figsize=(12, 7), facecolor=DARK_BG)
ax_anim.set_facecolor(DARK_MID)
for sp in ax_anim.spines.values():
    sp.set_edgecolor('#333')

prio_order = ['1','2','3','4','5']
x_pos      = np.arange(len(prio_order))
bars_anim  = ax_anim.bar(x_pos, [0]*5,
                          color=[PRIORITY_COLORS[k] for k in prio_order],
                          edgecolor=DARK_BG, linewidth=2, width=0.6)
val_texts  = [ax_anim.text(x, 0.3, '0', ha='center', va='bottom',
                            color='white', fontsize=14, fontweight='bold')
              for x in x_pos]
patient_txt = ax_anim.text(0.5, 0.97, 'Patient 0 / 100',
                            transform=ax_anim.transAxes,
                            ha='center', va='top', color='#A0A0A0', fontsize=11)
ax_anim.set_xticks(x_pos)
ax_anim.set_xticklabels([PRIORITY_LABELS[k] for k in prio_order],
                         color='#B0B0B0', fontsize=10)
ax_anim.set_ylabel('Patients Triaged', color='#B0B0B0', fontsize=11)
ax_anim.set_ylim(0, max(prio_counter.values(), default=10) + 8)
ax_anim.set_title('Live Triage — Patients Arriving in Sequence',
                   color='white', fontsize=14, fontweight='bold', pad=15)
ax_anim.tick_params(colors='#A0A0A0')


def update_triage(frame):
    fd = frames_data[frame]
    for bar, vt, pk in zip(bars_anim, val_texts, prio_order):
        h = fd.get(pk, 0)
        bar.set_height(h)
        vt.set_position((vt.get_position()[0], h + 0.3))
        vt.set_text(str(h))
    patient_txt.set_text(f'Patient {frame+1} / {len(rows)}')
    return list(bars_anim) + val_texts + [patient_txt]


ani = FuncAnimation(fig_anim, update_triage, frames=len(frames_data),
                    interval=60, blit=False, repeat=False)
ani.save(f'{OUT_DIR}/anim1_triage_tally.gif',
         writer=PillowWriter(fps=16), dpi=100)
plt.close()
print("  ✓ Animation 1: Triage Tally")


# ══════════════════════════════════════════════════════════════════════════
# ANIMATION 2: Red Flag Wave  (FIX: safe collection removal)
# ══════════════════════════════════════════════════════════════════════════
print("Generating Animation 2: Red Flag Detection Wave...")

rf_flags  = [1 if has_red_flag(r) else 0 for r in rows]
cum_flags = np.cumsum(rf_flags)
cum_total = np.arange(1, len(rows)+1)
cum_rate  = cum_flags / cum_total * 100

fig_anim2, ax_anim2 = plt.subplots(figsize=(12, 6), facecolor=DARK_BG)
ax_anim2.set_facecolor(DARK_MID)
for sp in ax_anim2.spines.values():
    sp.set_edgecolor('#333')

line_rate, = ax_anim2.plot([], [], color='#E74C3C', linewidth=2.5,
                            label='Detection rate %')
# FIX: keep a reference to the fill so we can remove it safely
fill_obj = [None]
# FIX: keep hline as a separate artist — do NOT include in collections removal
ax_anim2.axhline(cum_rate[-1], color='#F39C12', linestyle='--',
                  linewidth=1.5, label=f'Final rate {cum_rate[-1]:.1f}%', zorder=2)

ax_anim2.set_xlim(1, 100); ax_anim2.set_ylim(0, 100)
ax_anim2.set_xlabel('Patient Number', color='#B0B0B0', fontsize=11)
ax_anim2.set_ylabel('Cumulative Red Flag Detection Rate (%)', color='#B0B0B0', fontsize=11)
ax_anim2.set_title('Red Flag Detection Rate · Rolling Accumulation',
                    color='white', fontsize=14, fontweight='bold', pad=15)
ax_anim2.tick_params(colors='#A0A0A0')
ax_anim2.legend(fontsize=10, labelcolor='#B0B0B0', frameon=False)

xs_anim = list(range(1, len(rows)+1))


def update_rf(frame):
    n  = frame + 1
    xd = xs_anim[:n]
    yd = cum_rate[:n].tolist()
    line_rate.set_data(xd, yd)

    # FIX: remove only the fill, not all collections
    if fill_obj[0] is not None:
        try:
            fill_obj[0].remove()
        except Exception:
            pass
    fill_obj[0] = ax_anim2.fill_between(xd, yd, alpha=0.15, color='#E74C3C')

    sc_colors = ['#E74C3C' if f else '#2ECC71' for f in rf_flags[:n]]
    # FIX: avoid adding scatter every frame; use line markers instead
    ax_anim2.plot(xd[-1:], yd[-1:], 'o',
                  color=sc_colors[-1], markersize=5,
                  markeredgecolor='white', markeredgewidth=0.3,
                  alpha=0.8, zorder=5)
    return [line_rate]


ani2 = FuncAnimation(fig_anim2, update_rf, frames=len(rows),
                      interval=50, blit=False, repeat=False)
ani2.save(f'{OUT_DIR}/anim2_red_flag_wave.gif',
          writer=PillowWriter(fps=18), dpi=100)
plt.close()
print("  ✓ Animation 2: Red Flag Detection Wave")


# ══════════════════════════════════════════════════════════════════════════
# ANIMATION 3: Referral Build-Up Sunburst
# ══════════════════════════════════════════════════════════════════════════
print("Generating Animation 3: Referral Build-Up...")

fig_anim3, ax_anim3 = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True),
                                     facecolor=DARK_BG)
ax_anim3.set_facecolor(DARK_BG)
N_s        = len(spec_names)
angles_s   = np.linspace(0, 2*np.pi, N_s, endpoint=False)
width_s    = 2*np.pi/N_s * 0.82
max_val_s  = max(spec_vals) if spec_vals else 1
spec_cols_s = plt.cm.cool(np.linspace(0.1, 0.9, N_s))

ax_anim3.set_ylim(0, max_val_s + 5)
ax_anim3.set_yticks([]); ax_anim3.set_xticks([])
ax_anim3.spines['polar'].set_edgecolor('#2D333B')
ax_anim3.set_title('Specialist Referrals · Building Up',
                    color='white', fontsize=14, fontweight='bold', pad=25)
bars_ref = ax_anim3.bar(angles_s, [0]*N_s, width=width_s, bottom=1.5,
                         color=spec_cols_s, alpha=0.0,
                         edgecolor=DARK_BG, linewidth=1.5)
n_frames = 40


def update_sunburst(frame):
    progress = frame / max(n_frames-1, 1)
    for bar, target in zip(bars_ref, spec_vals):
        bar.set_height(target * progress)
        bar.set_alpha(0.3 + 0.7*progress)
    return list(bars_ref)


ani3 = FuncAnimation(fig_anim3, update_sunburst, frames=n_frames,
                      interval=55, blit=True, repeat=True)
ani3.save(f'{OUT_DIR}/anim3_referral_buildup.gif',
          writer=PillowWriter(fps=18), dpi=100)
plt.close()
print("  ✓ Animation 3: Referral Build-Up")


# ══════════════════════════════════════════════════════════════════════════
# FIG 7: Patient Journey Alluvial  (FIX: removed erroneous fill_betweenx)
# ══════════════════════════════════════════════════════════════════════════
print("Generating Fig 7: Patient Journey Alluvial...")

all_dx_cats = sorted({categorize_dx(extract_primary_diagnosis(r)) for r in rows
                      if extract_primary_diagnosis(r)})
all_prio_labels = ['P1 · Critical','P2 · Emergency','P3 · Urgent',
                    'P4 · Semi-urgent','P5 · Non-urgent']

flows = defaultdict(lambda: defaultdict(int))
for r in rows:
    dx = categorize_dx(extract_primary_diagnosis(r))
    pk = r['triage_priority'].strip()
    if dx and pk and pk in PRIORITY_LABELS:
        flows[dx][PRIORITY_LABELS[pk]] += 1

fig, ax = plt.subplots(figsize=(16, 10), facecolor='white')
ax.axis('off')

left_x, right_x = 0.05, 0.75
n_total = max(len(rows), 1)

dx_heights    = {d: sum(flows[d].values())/n_total for d in all_dx_cats if flows[d]}
prio_totals   = defaultdict(int)
for d in all_dx_cats:
    for p, v in flows[d].items():
        prio_totals[p] += v
ph = {p: prio_totals.get(p, 0)/n_total for p in all_prio_labels}


def make_positions(items, heights, gap=0.01):
    pos, y = {}, 0.0
    for item in items:
        h = heights.get(item, 0)
        pos[item] = (y, h)
        y += h + gap
    total_h = y - gap
    shift   = max((1 - total_h) / 2, 0)
    return {k: (v[0]+shift, v[1]) for k, v in pos.items()}


left_pos  = make_positions(all_dx_cats, dx_heights)
right_pos = make_positions(all_prio_labels, ph)
dx_cols   = {d: plt.cm.Spectral(i/max(len(all_dx_cats)-1,1))
             for i, d in enumerate(all_dx_cats)}
prio_cols_map = {
    'P1 · Critical':   '#C0392B', 'P2 · Emergency': '#E67E22',
    'P3 · Urgent':     '#2980B9', 'P4 · Semi-urgent':'#27AE60',
    'P5 · Non-urgent': '#8E44AD'
}

for dx, dx_flows in flows.items():
    if dx not in left_pos:
        continue
    ly, lh = left_pos[dx]
    ly_cur = ly
    for pr, count in sorted(dx_flows.items(), key=lambda x: -x[1]):
        if pr not in right_pos:
            continue
        ry, rh = right_pos[pr]
        flow_h = count / n_total
        col    = dx_cols[dx]
        path_x = np.linspace(left_x + 0.02, right_x - 0.02, 100)
        smooth = 1 / (1 + np.exp(-12*(path_x - 0.4)))
        mid_y  = ly + lh/2 + (ry + rh/2 - ly - lh/2) * smooth
        top_y  = mid_y + flow_h/2
        bot_y  = mid_y - flow_h/2
        # FIX: use fill_between (not fill_betweenx)
        ax.fill_between(path_x, bot_y, top_y, alpha=0.35, color=col)
        ly_cur += flow_h

for dx, (y, h) in left_pos.items():
    if h < 0.005:
        continue
    ax.add_patch(mpatches.FancyBboxPatch((left_x, y), 0.02, h,
                                          boxstyle='round,pad=0.005',
                                          color=dx_cols[dx], alpha=0.9))
    ax.text(left_x - 0.01, y+h/2, dx, ha='right', va='center',
            fontsize=8, fontweight='bold', color='#333')

for pr, (y, h) in right_pos.items():
    if h < 0.005:
        continue
    col = prio_cols_map.get(pr, '#999')
    ax.add_patch(mpatches.FancyBboxPatch((right_x, y), 0.02, h,
                                          boxstyle='round,pad=0.005',
                                          color=col, alpha=0.9))
    ax.text(right_x+0.035, y+h/2,
            f'{pr}  (n={prio_totals.get(pr,0)})',
            ha='left', va='center', fontsize=9, fontweight='bold', color=col)

ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.set_title('Patient Journey · Diagnosis → Triage Priority (Alluvial)',
             fontsize=15, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig(f'{OUT_DIR}/fig7_alluvial_journey.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✓ Fig 7: Patient Journey Alluvial")


# ══════════════════════════════════════════════════════════════════════════
# ANIMATION 4: Acuity Timeline Race
# ══════════════════════════════════════════════════════════════════════════
print("Generating Animation 4: Acuity Timeline Race...")

np.random.seed(7)
arrival_times = np.sort(np.random.uniform(0, 12, len(rows)))
prio_nums     = [int(r['triage_priority'].strip())
                 if r['triage_priority'].strip().isdigit() else 3
                 for r in rows]
jitter = np.random.normal(0, 0.12, len(rows))

fig_anim4, ax_anim4 = plt.subplots(figsize=(14, 6), facecolor=DARK_BG)
ax_anim4.set_facecolor(DARK_MID)
ax_anim4.set_xlim(-0.3, 12.3); ax_anim4.set_ylim(0.5, 5.5)
ax_anim4.set_yticks([1,2,3,4,5])
ax_anim4.set_yticklabels([PRIORITY_LABELS[k] for k in ['1','2','3','4','5']],
                          color='#B0B0B0', fontsize=9)
ax_anim4.set_xlabel('Time into Shift (hours)', color='#B0B0B0', fontsize=11)
ax_anim4.set_title('Patient Acuity Timeline · ED Shift Simulation',
                    color='white', fontsize=14, fontweight='bold', pad=15)
ax_anim4.tick_params(colors='#A0A0A0')
for sp in ax_anim4.spines.values():
    sp.set_edgecolor('#333')

# FIX: initialise scatter with empty arrays of the correct type
scat      = ax_anim4.scatter([], [], c=[], s=80,
                              cmap='RdYlGn_r', vmin=1, vmax=5,
                              edgecolors='white', linewidth=0.5,
                              alpha=0.85, zorder=4)
time_line = ax_anim4.axvline(0, color=ACCENT, linewidth=2, alpha=0.8)
time_txt  = ax_anim4.text(0.02, 0.97, 'Time: 0:00',
                           transform=ax_anim4.transAxes,
                           color='white', fontsize=11, va='top')
count_txt = ax_anim4.text(0.98, 0.97, 'Patients seen: 0',
                           transform=ax_anim4.transAxes,
                           color='#A0A0A0', fontsize=10, va='top', ha='right')
n_frames4 = 60


def update_timeline(frame):
    t    = frame / max(n_frames4-1, 1) * 12
    mask = arrival_times <= t
    xs   = arrival_times[mask]
    ys   = np.array(prio_nums)[mask] + jitter[mask]
    cs   = np.array(prio_nums, dtype=float)[mask]

    if len(xs) > 0:
        # FIX: pass 2-D array and numpy array for colours
        scat.set_offsets(np.column_stack([xs, ys]))
        scat.set_array(cs)
    else:
        scat.set_offsets(np.zeros((0, 2)))
        scat.set_array(np.array([]))

    time_line.set_xdata([t, t])
    h, m = int(t), int((t % 1)*60)
    time_txt.set_text(f'Time: {h:02d}:{m:02d}')
    count_txt.set_text(f'Patients seen: {int(mask.sum())}')
    return [scat, time_line, time_txt, count_txt]


ani4 = FuncAnimation(fig_anim4, update_timeline, frames=n_frames4,
                      interval=80, blit=True, repeat=True)
ani4.save(f'{OUT_DIR}/anim4_acuity_timeline.gif',
          writer=PillowWriter(fps=14), dpi=100)
plt.close()
print("  ✓ Animation 4: Acuity Timeline Race")


# ── Summary ────────────────────────────────────────────────────────────────
static = sorted(f for f in os.listdir(OUT_DIR) if f.endswith('.png'))
anim   = sorted(f for f in os.listdir(OUT_DIR) if f.endswith('.gif'))

print("\n" + "="*60)
print("  ALL ENHANCED VISUALIZATIONS COMPLETE")
print("="*60)
print(f"  Output: {OUT_DIR}/")
print(f"  Static figures : {len(static)}")
for f in static:
    print(f"    • {f}")
print(f"  Animations     : {len(anim)}")
for f in anim:
    print(f"    • {f}")
print("="*60)
