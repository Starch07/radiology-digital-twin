import streamlit as st
import os
import base64
from pathlib import Path

st.set_page_config(
    page_title="Radiology Digital Twin · Emmanuel",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

:root {
    --bg: #0b0f14; --surface: #141920; --card: #1a2230;
    --border: #263040; --accent: #00d4aa; --accent2: #0096ff;
    --text: #e2e8f0; --muted: #64748b;
}
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important; color: var(--text);
    font-family: 'Syne', sans-serif;
}
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
.hero-title {
    font-size: 2.8rem; font-weight: 800;
    background: linear-gradient(120deg, #00d4aa, #0096ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1.1;
}
.hero-sub { color: #64748b; font-size: 0.95rem; font-family: 'DM Mono', monospace; }
.metric-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 1rem 1.25rem; text-align: center;
}
.metric-num { font-size: 2rem; font-weight: 800; color: var(--accent); }
.metric-label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; }
.section-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.25rem; margin-bottom: 1rem;
}
.stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    color: #0b0f14 !important; font-weight: 700; border: none;
    border-radius: 6px; padding: 0.55rem 1.4rem;
}
</style>
""", unsafe_allow_html=True)


def load_image_b64(path):
    try:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None


def show_image(path, caption="", width=None):
    if os.path.exists(path):
        st.image(path, caption=caption, use_container_width=width is None)
    else:
        st.info(f"Image not found: {path}")


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0">
      <div style="font-size:1.4rem;font-weight:800;background:linear-gradient(120deg,#00d4aa,#0096ff);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">
        🧠 RadDigitalTwin
      </div>
      <div style="font-size:0.75rem;color:#64748b;font-family:'DM Mono',monospace;margin-top:0.3rem;">
        FUT Minna · Medical Physics
      </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("Navigate", [
        "🏠 Home",
        "📊 Results Dashboard",
        "🔬 Model Evaluation",
        "📈 Enhanced Visualizations",
        "🧠 RadPersona App",
        "📋 About & Methods",
    ])

PLOTS_DIR = "radiology_pipeline/results/enhanced_plots"
EVAL_DIR  = "radiology_pipeline/results/evaluation"


# ══════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ══════════════════════════════════════════════════════════════════════════
if page == "🏠 Home":
    st.markdown("""
    <div style="padding:2rem 0 1rem 0">
      <div class="hero-title">Radiology Digital Twin</div>
      <div class="hero-sub" style="margin-top:0.5rem">
        // LLM-based Automated Clinical Interpretation & Triage of Brain MRI Reports
      </div>
      <div style="font-size:0.85rem;color:#475569;margin-top:0.5rem">
        Federal University of Technology Minna · Department of Physics · Medical Physics
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Key metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        ("100", "Patients Analyzed", "#00d4aa"),
        ("89.4", "Model Score / 100", "#0096ff"),
        ("66%", "Emergency Cases", "#ef4444"),
        ("100%", "AI Success Rate", "#22c55e"),
        ("21", "Visualizations", "#a78bfa"),
    ]
    for col, (num, label, color) in zip([c1,c2,c3,c4,c5], metrics):
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-num" style="color:{color}">{num}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # Project summary
    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.markdown("""
        <div class="section-card">
          <div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-bottom:0.75rem">
            🎯 Project Overview
          </div>
          <div style="font-size:0.875rem;color:#94a3b8;line-height:1.8">
            This study develops and evaluates a <b style="color:#00d4aa">Large Language Model-based
            Digital Twin Framework</b> for automated clinical interpretation and triage of brain
            MRI radiology reports obtained from a private hospital in Abuja, Nigeria.<br><br>
            The framework processes radiology PDF reports through a 6-stage pipeline —
            anonymization, persona generation, clinical question generation, LLM simulation,
            postprocessing, and visualization — using <b style="color:#00d4aa">Google Gemini 2.5 Flash</b>
            as the core AI engine.<br><br>
            <b style="color:#e2e8f0">100 brain MRI reports</b> were processed with a
            <b style="color:#00d4aa">100% success rate</b>, generating comprehensive clinical
            assessments including triage priorities, differential diagnoses, specialist referrals,
            and patient-friendly explanations.
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div class="section-card">
          <div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-bottom:0.75rem">
            📌 Key Findings
          </div>
          <div style="font-size:0.85rem;color:#94a3b8;line-height:2">
            ✅ &nbsp;Overall model score: <b style="color:#00d4aa">89.4/100</b><br>
            ✅ &nbsp;Response quality: <b style="color:#00d4aa">93.1/100</b><br>
            ✅ &nbsp;66 emergency/critical cases identified<br>
            ✅ &nbsp;25 red flags detected<br>
            ✅ &nbsp;29 neurology referrals generated<br>
            ✅ &nbsp;3 ranked diagnoses per patient<br>
            ✅ &nbsp;90% clinical plausibility<br>
            ✅ &nbsp;100% differential diagnosis completeness
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center;font-size:0.8rem;color:#475569;font-family:'DM Mono',monospace">
      Powered by Google Gemini AI · Built with Python & Streamlit ·
      Federal University of Technology Minna © 2025
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE: RESULTS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════
elif page == "📊 Results Dashboard":
    st.markdown("## 📊 Results Dashboard")
    st.markdown("*AI-powered analysis of 100 brain MRI radiology reports*")
    st.markdown("---")

    dashboard_path = "radiology_pipeline/results/dashboard.html"
    if os.path.exists(dashboard_path):
        with open(dashboard_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=900, scrolling=True)
    else:
        st.warning("Dashboard file not found. Run create_visualization.py first.")


# ══════════════════════════════════════════════════════════════════════════
# PAGE: MODEL EVALUATION
# ══════════════════════════════════════════════════════════════════════════
elif page == "🔬 Model Evaluation":
    st.markdown("## 🔬 Model Evaluation")
    st.markdown("*Comprehensive evaluation across 7 clinical metrics*")
    st.markdown("---")

    # Summary metrics
    c1,c2,c3,c4 = st.columns(4)
    eval_metrics = [
        ("89.4/100", "Overall Score", "#00d4aa"),
        ("93.1/100", "Response Quality", "#0096ff"),
        ("100%", "Parse Rate", "#22c55e"),
        ("90%", "Clinical Plausibility", "#a78bfa"),
    ]
    for col,(num,label,color) in zip([c1,c2,c3,c4], eval_metrics):
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-num" style="color:{color}">{num}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    eval_plots = {
        "Performance Dashboard": f"{EVAL_DIR}/eval1_performance_dashboard.png",
        "Performance Radar":     f"{EVAL_DIR}/eval2_performance_radar.png",
        "Diagnosis Quality":     f"{EVAL_DIR}/eval3_diagnosis_quality.png",
        "Priority vs Quality":   f"{EVAL_DIR}/eval4_priority_vs_quality.png",
    }

    for title, path in eval_plots.items():
        st.markdown(f"### {title}")
        show_image(path)
        st.markdown("")

    # Metrics table
    st.markdown("### 📋 Detailed Metrics")
    import pandas as pd
    metrics_df = pd.DataFrame({
        'Metric': ['Parse Rate','Triage Coverage','DD Completeness',
                   'Red Flag Detection','Mgmt Plan Score','Response Quality','Clinical Plausibility'],
        'Score': ['100%','100%','100%','25%','80.5/100','93.1/100','90%'],
        'Status': ['✅ Excellent','✅ Excellent','✅ Excellent',
                   '✅ Expected','✅ Good','✅ Excellent','✅ Excellent'],
        'Notes': [
            'All 100 patients parsed successfully',
            'All 100 patients assigned triage priority',
            'All patients received ranked & justified diagnoses',
            '25 critical red flags detected from 100 patients',
            '36 full management plans, 63 partial',
            '78% responses rated Excellent (≥90)',
            '90 of 100 responses clinically plausible',
        ]
    })
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE: ENHANCED VISUALIZATIONS
# ══════════════════════════════════════════════════════════════════════════
elif page == "📈 Enhanced Visualizations":
    st.markdown("## 📈 Enhanced Visualizations")
    st.markdown("*Publication-quality analysis of all 100 patients*")
    st.markdown("---")

    viz_options = {
        "Fig 1 · Clinical Command Centre":    f"{PLOTS_DIR}/fig1_command_centre.png",
        "Fig 2 · Diagnosis Landscape":        f"{PLOTS_DIR}/fig2_diagnosis_landscape.png",
        "Fig 3 · Priority × Diagnosis Heatmap": f"{PLOTS_DIR}/fig3_priority_diagnosis_heatmap.png",
        "Fig 4 · Referral Sunburst":          f"{PLOTS_DIR}/fig4_referral_sunburst.png",
        "Fig 5 · Severity Spectrum":          f"{PLOTS_DIR}/fig5_severity_spectrum_bubble.png",
        "Fig 6 · Investigation Waterfall":    f"{PLOTS_DIR}/fig6_investigation_waterfall.png",
        "Fig 7 · Patient Journey Alluvial":   f"{PLOTS_DIR}/fig7_alluvial_journey.png",
        "Fig 8 · Correlation Matrix":         f"{PLOTS_DIR}/fig8_correlation_matrix.png",
        "Fig 9 · Investigation Arsenal":      f"{PLOTS_DIR}/fig9_investigation_arsenal.png",
        "Fig 10 · Word Cloud":                f"{PLOTS_DIR}/fig10_justification_wordcloud.png",
        "Fig 11 · Referral Network":          f"{PLOTS_DIR}/fig11_referral_network.png",
        "Fig 12 · Complexity Radar":          f"{PLOTS_DIR}/fig12_complexity_radar.png",
        "Fig 13 · Follow-up Spectrum":        f"{PLOTS_DIR}/fig13_followup_spectrum.png",
    }

    selected = st.selectbox("Select visualization:", list(viz_options.keys()))
    show_image(viz_options[selected], caption=selected)

    st.markdown("---")
    st.markdown("### 🎬 Animations")
    anim_options = {
        "Anim 1 · Triage Tally":          f"{PLOTS_DIR}/anim1_triage_tally.gif",
        "Anim 2 · Red Flag Wave":          f"{PLOTS_DIR}/anim2_red_flag_wave.gif",
        "Anim 3 · Referral Build-Up":      f"{PLOTS_DIR}/anim3_referral_buildup.gif",
        "Anim 4 · Acuity Timeline":        f"{PLOTS_DIR}/anim4_acuity_timeline.gif",
        "Anim 5 · Radar Morph":            f"{PLOTS_DIR}/anim5_radar_morph.gif",
        "Anim 6 · Network Growth":         f"{PLOTS_DIR}/anim6_network_growth.gif",
        "Anim 7 · Investigation Race":     f"{PLOTS_DIR}/anim7_investigation_race.gif",
        "Anim 8 · Priority Grid Pulse":    f"{PLOTS_DIR}/anim8_priority_pulse.gif",
    }
    selected_anim = st.selectbox("Select animation:", list(anim_options.keys()))
    show_image(anim_options[selected_anim], caption=selected_anim)


# ══════════════════════════════════════════════════════════════════════════
# PAGE: RADPERSONA APP
# ══════════════════════════════════════════════════════════════════════════
elif page == "🧠 RadPersona App":
    st.markdown("## 🧠 RadPersona — PDF to Digital Twin Converter")
    st.markdown("*Upload radiology PDF reports to generate anonymized patient personas*")
    st.markdown("---")
    st.info("👉 The full RadPersona app runs at: **streamlit run app.py** on your local machine, or visit the RadPersona tab on the deployed version.")

    st.markdown("""
    <div class="section-card">
      <div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-bottom:0.75rem">How it works</div>
      <div style="font-size:0.875rem;color:#94a3b8;line-height:2">
        <b style="color:#00d4aa">Step 1</b> — Upload brain MRI radiology PDF reports<br>
        <b style="color:#00d4aa">Step 2</b> — App extracts and anonymizes patient data (HIPAA Safe Harbor)<br>
        <b style="color:#00d4aa">Step 3</b> — Each patient converted to structured persona file<br>
        <b style="color:#00d4aa">Step 4</b> — Download persona ZIP + anonymization key CSV<br>
        <b style="color:#00d4aa">Step 5</b> — Feed personas into the Digital Twin pipeline<br>
        <b style="color:#00d4aa">Step 6</b> — Gemini AI generates clinical assessments for each patient
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE: ABOUT & METHODS
# ══════════════════════════════════════════════════════════════════════════
elif page == "📋 About & Methods":
    st.markdown("## 📋 About & Methodology")
    st.markdown("---")

    st.markdown("""
    <div class="section-card">
      <div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-bottom:0.75rem">🎓 Project Details</div>
      <div style="font-size:0.875rem;color:#94a3b8;line-height:2">
        <b style="color:#e2e8f0">Title:</b> Development of a Large Language Model-based Digital Twin Framework
        for Automated Clinical Interpretation and Triage of Radiology Reports<br>
        <b style="color:#e2e8f0">Institution:</b> Federal University of Technology Minna, Nigeria<br>
        <b style="color:#e2e8f0">Department:</b> Physics (Medical Physics)<br>
        <b style="color:#e2e8f0">Dataset:</b> 100 brain MRI reports from a private hospital in Abuja, Nigeria<br>
        <b style="color:#e2e8f0">AI Model:</b> Google Gemini 2.5 Flash<br>
        <b style="color:#e2e8f0">Framework:</b> Radiology Digital Twin Pipeline
      </div>
    </div>

    <div class="section-card" style="margin-top:1rem">
      <div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-bottom:0.75rem">🔧 Pipeline Stages</div>
      <div style="font-size:0.875rem;color:#94a3b8;line-height:2">
        <b style="color:#00d4aa">Stage 1</b> · RadPersona App — PDF extraction & anonymization<br>
        <b style="color:#00d4aa">Stage 2</b> · Persona Preparation — PID mapping & organization<br>
        <b style="color:#00d4aa">Stage 3</b> · Question Generation — 6 clinical domain questions<br>
        <b style="color:#00d4aa">Stage 4</b> · Simulation Input — Persona + questions combined<br>
        <b style="color:#00d4aa">Stage 5</b> · LLM Simulation — Gemini AI clinical assessment<br>
        <b style="color:#00d4aa">Stage 6</b> · Postprocessing — Results compilation & visualization
      </div>
    </div>

    <div class="section-card" style="margin-top:1rem">
      <div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-bottom:0.75rem">🛠️ Technologies Used</div>
      <div style="font-size:0.875rem;color:#94a3b8;line-height:2">
        Python · Streamlit · Google Gemini AI · PDFPlumber · Matplotlib · NumPy · Pandas
      </div>
    </div>
    """, unsafe_allow_html=True)
