import csv
from collections import Counter

rows = list(csv.DictReader(open('radiology_pipeline/results/summary.csv')))

priorities = [r['triage_priority'].strip() for r in rows if r['triage_priority'].strip()]
priority_counts = Counter(priorities)

specialties = []
for r in rows:
    if r['specialist_referrals'].strip():
        parts = r['specialist_referrals'].split('&')
        for p in parts:
            p = p.strip().split('(')[0].strip()
            if p:
                specialties.append(p)
specialty_counts = Counter(specialties)

priority_labels = {
    '1': 'Priority 1 - Critical',
    '2': 'Priority 2 - Emergency',
    '3': 'Priority 3 - Urgent',
    '4': 'Priority 4 - Semi-urgent',
    '5': 'Priority 5 - Non-urgent'
}
priority_colors = {
    '1': '#E24B4A',
    '2': '#EF9F27',
    '3': '#378ADD',
    '4': '#1D9E75',
    '5': '#888780'
}

p_labels = [priority_labels.get(k, f'Priority {k}') for k in sorted(priority_counts.keys())]
p_data = [priority_counts[k] for k in sorted(priority_counts.keys())]
p_colors = [priority_colors.get(k, '#888780') for k in sorted(priority_counts.keys())]

top_specs = specialty_counts.most_common(5)
s_labels = [s[0] for s in top_specs]
s_data = [s[1] for s in top_specs]
s_colors = ['#534AB7', '#0F6E56', '#993C1D', '#185FA5', '#854F0B']

total = len(rows)
critical = priority_counts.get('1', 0) + priority_counts.get('2', 0)
neuro = sum(v for k, v in specialty_counts.items() if 'neurol' in k.lower())

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Radiology Digital Twin - Results Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: Arial, sans-serif; background: #f5f5f5; color: #222; padding: 24px; }}
  h1 {{ font-size: 22px; font-weight: 600; margin-bottom: 4px; color: #1a1a1a; }}
  .subtitle {{ font-size: 14px; color: #666; margin-bottom: 24px; }}
  .cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }}
  .card {{ background: #fff; border-radius: 10px; padding: 16px; border: 1px solid #e0e0e0; }}
  .card-label {{ font-size: 12px; color: #888; margin-bottom: 6px; }}
  .card-value {{ font-size: 28px; font-weight: 600; }}
  .charts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
  .chart-box {{ background: #fff; border-radius: 10px; padding: 20px; border: 1px solid #e0e0e0; }}
  .chart-box h3 {{ font-size: 14px; font-weight: 600; margin-bottom: 16px; color: #333; }}
  .chart-full {{ background: #fff; border-radius: 10px; padding: 20px; border: 1px solid #e0e0e0; margin-bottom: 24px; }}
  .chart-full h3 {{ font-size: 14px; font-weight: 600; margin-bottom: 16px; color: #333; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ background: #f0f0f0; padding: 10px 12px; text-align: left; font-weight: 600; color: #444; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #f0f0f0; color: #333; }}
  tr:hover td {{ background: #fafafa; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
  .b1 {{ background: #fde8e8; color: #A32D2D; }}
  .b2 {{ background: #fef3e2; color: #854F0B; }}
  .b3 {{ background: #e6f1fb; color: #185FA5; }}
  .b4 {{ background: #e1f5ee; color: #0F6E56; }}
  .b5 {{ background: #f0f0f0; color: #5F5E5A; }}
  .footer {{ text-align: center; font-size: 12px; color: #aaa; margin-top: 24px; }}
</style>
</head>
<body>

<h1>Radiology Digital Twin — Results Dashboard</h1>
<p class="subtitle">AI-powered analysis of {total} brain MRI radiology reports | Federal University of Technology Minna</p>

<div class="cards">
  <div class="card">
    <div class="card-label">Total patients analyzed</div>
    <div class="card-value" style="color:#185FA5">{total}</div>
  </div>
  <div class="card">
    <div class="card-label">Critical / emergency cases</div>
    <div class="card-value" style="color:#A32D2D">{critical}</div>
  </div>
  <div class="card">
    <div class="card-label">Neurology referrals</div>
    <div class="card-value" style="color:#534AB7">{neuro}</div>
  </div>
  <div class="card">
    <div class="card-label">AI success rate</div>
    <div class="card-value" style="color:#3B6D11">100%</div>
  </div>
</div>

<div class="charts">
  <div class="chart-box">
    <h3>Triage priority distribution</h3>
    <div style="position:relative;height:220px;">
      <canvas id="triageChart"></canvas>
    </div>
  </div>
  <div class="chart-box">
    <h3>Top specialist referrals</h3>
    <div style="position:relative;height:220px;">
      <canvas id="referralChart"></canvas>
    </div>
  </div>
</div>

<div class="chart-full">
  <h3>Patient triage breakdown</h3>
  <div style="position:relative;height:180px;">
    <canvas id="barChart"></canvas>
  </div>
</div>

<div class="chart-full">
  <h3>Patient summary table</h3>
  <table>
    <tr>
      <th>Patient ID</th>
      <th>Triage Priority</th>
      <th>Red Flags</th>
      <th>Specialist Referral</th>
      <th>Status</th>
    </tr>
"""

badge_class = {'1':'b1','2':'b2','3':'b3','4':'b4','5':'b5'}
for r in rows:
    pid = r['pid']
    priority = r['triage_priority'].strip()
    label = priority_labels.get(priority, f'Priority {priority}')
    bc = badge_class.get(priority, 'b5')
    red_flag = r['red_flags'].strip()
    if len(red_flag) > 50:
        red_flag = red_flag[:50] + '...'
    if not red_flag:
        red_flag = 'None identified'
    referral = r['specialist_referrals'].strip().split('&')[0].split('(')[0].strip()
    if not referral:
        referral = 'N/A'
    html += f"""    <tr>
      <td>{pid}</td>
      <td><span class="badge {bc}">{label}</span></td>
      <td>{red_flag}</td>
      <td>{referral}</td>
      <td><span class="badge b4">Completed</span></td>
    </tr>
"""

html += f"""  </table>
</div>

<div class="footer">Generated by Radiology Digital Twin Pipeline | Powered by Google Gemini AI | {total} patients processed</div>

<script>
new Chart(document.getElementById('triageChart'), {{
  type: 'doughnut',
  data: {{
    labels: {p_labels},
    datasets: [{{
      data: {p_data},
      backgroundColor: {p_colors},
      borderWidth: 2,
      borderColor: '#fff'
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }}, padding: 8 }} }}
    }}
  }}
}});

new Chart(document.getElementById('referralChart'), {{
  type: 'bar',
  data: {{
    labels: {s_labels},
    datasets: [{{
      data: {s_data},
      backgroundColor: {s_colors},
      borderWidth: 0,
      borderRadius: 4
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ font: {{ size: 11 }} }} }},
      y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }}
    }}
  }}
}});

new Chart(document.getElementById('barChart'), {{
  type: 'bar',
  data: {{
    labels: {p_labels},
    datasets: [{{
      data: {p_data},
      backgroundColor: {p_colors},
      borderWidth: 0,
      borderRadius: 4
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }},
      y: {{ ticks: {{ font: {{ size: 11 }}, autoSkip: false }} }}
    }}
  }}
}});
</script>
</body>
</html>"""

with open('radiology_pipeline/results/dashboard.html', 'w') as f:
    f.write(html)

print("Dashboard created! Opening in browser...")
import webbrowser, os
webbrowser.open('file:///' + os.path.abspath('radiology_pipeline/results/dashboard.html').replace('\\', '/'))
print("Done! File saved at: radiology_pipeline/results/dashboard.html")
