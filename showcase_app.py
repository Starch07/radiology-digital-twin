import streamlit as st
import os
import base64

st.set_page_config(
    page_title="Radiology Digital Twin · FUT Minna",
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
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
/* Force sidebar always visible */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    left: 0 !important;
    z-index: 999 !important;
}
section[data-testid="stSidebar"] {
    min-width: 250px !important;
    display: block !important;
    visibility: visible !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 250px !important;
    margin-left: 0 !important;
}
button[data-testid="baseButton-header"] {
    display: flex !important;
    visibility: visible !important;
}
/* Hide Streamlit branding */
.stDeployButton {display: none !important;}
#stDecoration {display: none !important;}
div[data-testid="stToolbar"] {display: none !important;}
footer {visibility: hidden !important;}
#MainMenu {visibility: hidden !important;}
header {visibility: hidden !important;}
div[data-testid="stStatusWidget"] {display: none !important;}

</style>
""", unsafe_allow_html=True)


def show_image(path, caption=""):
    if os.path.exists(path):
        st.image(path, caption=caption, use_container_width=True)
    else:
        st.warning(f"⚠️ Image not available in deployed version. Run locally to view: `{path}`")


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0">
      <div style="font-size:1.4rem;font-weight:800;background:linear-gradient(120deg,#00d4aa,#0096ff);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">
        🧠 RadDigitalTwin
      </div>
      <div style="font-size:0.7rem;color:#64748b;font-family:'DM Mono',monospace;margin-top:0.3rem;line-height:1.6">
        Federal University of Technology Minna<br>
        School of Physical Sciences<br>
        Department of Physics
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
        Federal University of Technology Minna &nbsp;·&nbsp;
        School of Physical Sciences &nbsp;·&nbsp;
        Department of Physics (Medical Physics)
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    c1,c2,c3,c4,c5 = st.columns(5)
    metrics = [
        ("100", "Patients Analyzed", "#00d4aa"),
        ("89.4", "Model Score / 100", "#0096ff"),
        ("66%", "Emergency Cases", "#ef4444"),
        ("100%", "AI Success Rate", "#22c55e"),
        ("21", "Visualizations", "#a78bfa"),
    ]
    for col,(num,label,color) in zip([c1,c2,c3,c4,c5], metrics):
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-num" style="color:{color}">{num}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")
    col_left, col_right = st.columns([3,2])

    with col_left:
        st.markdown("""
        <div class="section-card">
          <div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-bottom:0.75rem">🎯 Project Overview</div>
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
          <div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-bottom:0.75rem">📌 Key Findings</div>
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
      Powered by Google Gemini AI &nbsp;·&nbsp; Built with Python & Streamlit &nbsp;·&nbsp;
      Federal University of Technology Minna © 2026
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE: RESULTS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════
elif page == "📊 Results Dashboard":
    st.markdown("## 📊 Results Dashboard")
    st.markdown("*AI-powered analysis of 100 brain MRI radiology reports*")
    st.markdown("---")

    # Show key stats even without dashboard file
    c1,c2,c3,c4 = st.columns(4)
    for col,(num,label,color) in zip([c1,c2,c3,c4],[
        ("100","Total Patients","#00d4aa"),
        ("66","Emergency/Critical","#ef4444"),
        ("50","Neurology Referrals","#0096ff"),
        ("25","Red Flags Detected","#f59e0b"),
    ]):
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-num" style="color:{color}">{num}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # Triage distribution
    st.markdown("### 📊 Triage Priority Distribution")
    st.markdown("""
    <div class="section-card">
    <div style="font-size:0.875rem;color:#94a3b8;line-height:2">
      <span style="color:#C0392B">●</span> <b style="color:#e2e8f0">Priority 1 — Critical:</b> 6 patients (6%)<br>
      <span style="color:#E67E22">●</span> <b style="color:#e2e8f0">Priority 2 — Emergency:</b> 60 patients (60%)<br>
      <span style="color:#2980B9">●</span> <b style="color:#e2e8f0">Priority 3 — Urgent:</b> 12 patients (12%)<br>
      <span style="color:#27AE60">●</span> <b style="color:#e2e8f0">Priority 4 — Semi-urgent:</b> 17 patients (17%)<br>
      <span style="color:#8E44AD">●</span> <b style="color:#e2e8f0">Priority 5 — Non-urgent:</b> 5 patients (5%)
    </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🏥 Top Specialist Referrals")
    import pandas as pd
    ref_df = pd.DataFrame({
        'Specialist': ['Neurologist','ENT Specialist','Neurology','Otolaryngologist','ENT','Neurosurgery','Neuro-oncology','Primary Care'],
        'Referrals': [29, 27, 17, 13, 11, 8, 3, 3],
    })
    st.bar_chart(ref_df.set_index('Specialist'))

    st.markdown("### 🚩 Red Flag Summary")
    col_a, col_b = st.columns(2)
    col_a.metric("Red Flags Detected", "25 patients", "25%")
    col_b.metric("No Red Flags", "75 patients", "75%")

    dashboard_path = "radiology_pipeline/results/dashboard.html"
    if os.path.exists(dashboard_path):
        st.markdown("### 📈 Full Interactive Dashboard")
        with open(dashboard_path,'r',encoding='utf-8',errors='ignore') as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=900, scrolling=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE: MODEL EVALUATION
# ══════════════════════════════════════════════════════════════════════════
elif page == "🔬 Model Evaluation":
    st.markdown("## 🔬 Model Evaluation")
    st.markdown("*Comprehensive evaluation across 7 clinical metrics*")
    st.markdown("---")

    c1,c2,c3,c4 = st.columns(4)
    for col,(num,label,color) in zip([c1,c2,c3,c4],[
        ("89.4/100","Overall Score","#00d4aa"),
        ("93.1/100","Response Quality","#0096ff"),
        ("100%","Parse Rate","#22c55e"),
        ("90%","Clinical Plausibility","#a78bfa"),
    ]):
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-num" style="color:{color}">{num}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # Metrics table - always shows
    st.markdown("### 📋 Detailed Evaluation Metrics")
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

    st.markdown("### 📊 Performance Visualization")
    st.markdown("""
    <div class="section-card">
    <div style="font-size:0.875rem;color:#94a3b8;line-height:2.2">
      <b style="color:#00d4aa">Parse Rate:</b>
      <div style="background:#1a2230;border-radius:6px;height:20px;margin:4px 0 8px">
        <div style="background:#2ECC71;width:100%;height:100%;border-radius:6px;display:flex;align-items:center;padding-left:8px">
          <span style="color:white;font-size:12px;font-weight:700">100%</span></div></div>
      <b style="color:#00d4aa">Response Quality:</b>
      <div style="background:#1a2230;border-radius:6px;height:20px;margin:4px 0 8px">
        <div style="background:#3498DB;width:93%;height:100%;border-radius:6px;display:flex;align-items:center;padding-left:8px">
          <span style="color:white;font-size:12px;font-weight:700">93.1%</span></div></div>
      <b style="color:#00d4aa">Clinical Plausibility:</b>
      <div style="background:#1a2230;border-radius:6px;height:20px;margin:4px 0 8px">
        <div style="background:#9B59B6;width:90%;height:100%;border-radius:6px;display:flex;align-items:center;padding-left:8px">
          <span style="color:white;font-size:12px;font-weight:700">90%</span></div></div>
      <b style="color:#00d4aa">Management Plan:</b>
      <div style="background:#1a2230;border-radius:6px;height:20px;margin:4px 0 8px">
        <div style="background:#E67E22;width:80%;height:100%;border-radius:6px;display:flex;align-items:center;padding-left:8px">
          <span style="color:white;font-size:12px;font-weight:700">80.5%</span></div></div>
      <b style="color:#00d4aa">Overall Score:</b>
      <div style="background:#1a2230;border-radius:6px;height:24px;margin:4px 0 8px">
        <div style="background:linear-gradient(90deg,#00d4aa,#0096ff);width:89%;height:100%;border-radius:6px;display:flex;align-items:center;padding-left:8px">
          <span style="color:#0b0f14;font-size:13px;font-weight:800">89.4/100</span></div></div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # Show eval plots if available
    eval_plots = [
        ("Performance Dashboard", f"{EVAL_DIR}/eval1_performance_dashboard.png"),
        ("Performance Radar",     f"{EVAL_DIR}/eval2_performance_radar.png"),
        ("Diagnosis Quality",     f"{EVAL_DIR}/eval3_diagnosis_quality.png"),
        ("Priority vs Quality",   f"{EVAL_DIR}/eval4_priority_vs_quality.png"),
    ]
    for title, path in eval_plots:
        if os.path.exists(path):
            st.markdown(f"### {title}")
            st.image(path, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE: ENHANCED VISUALIZATIONS
# ══════════════════════════════════════════════════════════════════════════
elif page == "📈 Enhanced Visualizations":
    st.markdown("## 📈 Enhanced Visualizations")
    st.markdown("*Publication-quality analysis of all 100 patients*")
    st.markdown("---")

    viz_options = {
        "Fig 1 · Clinical Command Centre":       f"{PLOTS_DIR}/fig1_command_centre.png",
        "Fig 2 · Diagnosis Landscape":           f"{PLOTS_DIR}/fig2_diagnosis_landscape.png",
        "Fig 3 · Priority × Diagnosis Heatmap":  f"{PLOTS_DIR}/fig3_priority_diagnosis_heatmap.png",
        "Fig 4 · Referral Sunburst":             f"{PLOTS_DIR}/fig4_referral_sunburst.png",
        "Fig 5 · Severity Spectrum":             f"{PLOTS_DIR}/fig5_severity_spectrum_bubble.png",
        "Fig 6 · Investigation Waterfall":       f"{PLOTS_DIR}/fig6_investigation_waterfall.png",
        "Fig 7 · Patient Journey Alluvial":      f"{PLOTS_DIR}/fig7_alluvial_journey.png",
        "Fig 8 · Correlation Matrix":            f"{PLOTS_DIR}/fig8_correlation_matrix.png",
        "Fig 9 · Investigation Arsenal":         f"{PLOTS_DIR}/fig9_investigation_arsenal.png",
        "Fig 10 · Word Cloud":                   f"{PLOTS_DIR}/fig10_justification_wordcloud.png",
        "Fig 11 · Referral Network":             f"{PLOTS_DIR}/fig11_referral_network.png",
        "Fig 12 · Complexity Radar":             f"{PLOTS_DIR}/fig12_complexity_radar.png",
        "Fig 13 · Follow-up Spectrum":           f"{PLOTS_DIR}/fig13_followup_spectrum.png",
    }

    available = {k:v for k,v in viz_options.items() if os.path.exists(v)}
    unavailable = {k:v for k,v in viz_options.items() if not os.path.exists(v)}

    if available:
        selected = st.selectbox("Select visualization:", list(available.keys()))
        st.image(available[selected], caption=selected, use_container_width=True)
    else:
        st.markdown("""
        <div class="section-card">
        <div style="font-size:0.9rem;color:#94a3b8;line-height:2">
          <b style="color:#00d4aa">ℹ️ About the visualizations</b><br><br>
          This project generated <b style="color:#e2e8f0">21 publication-quality visualizations</b>
          including 13 static figures and 8 animated GIFs.<br><br>
          The visualizations include:<br>
          • Clinical Command Centre Dashboard (6-panel overview)<br>
          • Diagnosis Landscape (proportional & breakdown charts)<br>
          • Priority × Diagnosis Heatmap<br>
          • Referral Sunburst (polar chart)<br>
          • Severity Spectrum Bubble Chart<br>
          • Investigation Complexity Waterfall<br>
          • Patient Journey Alluvial Diagram<br>
          • Correlation Matrix of clinical metrics<br>
          • Investigation Arsenal by Priority<br>
          • Triage Justification Word Cloud<br>
          • Referral Co-occurrence Network<br>
          • Complexity Radar per Priority<br>
          • Follow-up Urgency Spectrum<br><br>
          <b style="color:#e2e8f0">8 Animations:</b> Triage Tally, Red Flag Wave, Referral Build-Up,
          Acuity Timeline, Morphing Radar, Network Growth, Investigation Race, Priority Grid Pulse<br><br>
          <i style="color:#64748b">Note: Images are stored locally. Run the app locally to view all visualizations.</i>
        </div>
        </div>
        """, unsafe_allow_html=True)

    if unavailable:
        with st.expander("ℹ️ Visualizations available when running locally"):
            for name in unavailable.keys():
                st.markdown(f"• {name}")

    # Animations section
    st.markdown("---")
    st.markdown("### 🎬 Animations")
    anim_options = {
        "Anim 1 · Triage Tally":       f"{PLOTS_DIR}/anim1_triage_tally.gif",
        "Anim 2 · Red Flag Wave":       f"{PLOTS_DIR}/anim2_red_flag_wave.gif",
        "Anim 3 · Referral Build-Up":   f"{PLOTS_DIR}/anim3_referral_buildup.gif",
        "Anim 4 · Acuity Timeline":     f"{PLOTS_DIR}/anim4_acuity_timeline.gif",
        "Anim 5 · Radar Morph":         f"{PLOTS_DIR}/anim5_radar_morph.gif",
        "Anim 6 · Network Growth":      f"{PLOTS_DIR}/anim6_network_growth.gif",
        "Anim 7 · Investigation Race":  f"{PLOTS_DIR}/anim7_investigation_race.gif",
        "Anim 8 · Priority Grid Pulse": f"{PLOTS_DIR}/anim8_priority_pulse.gif",
    }
    avail_anim = {k:v for k,v in anim_options.items() if os.path.exists(v)}
    if avail_anim:
        selected_anim = st.selectbox("Select animation:", list(avail_anim.keys()))
        st.image(avail_anim[selected_anim], caption=selected_anim, use_container_width=True)
    else:
        st.info("8 animations available when running locally. Run: `streamlit run showcase_app.py`")


# ══════════════════════════════════════════════════════════════════════════
# PAGE: RADPERSONA APP
# ══════════════════════════════════════════════════════════════════════════
elif page == "🧠 RadPersona App":
    st.markdown("## 🧠 RadPersona — PDF to Digital Twin Converter")
    st.markdown("*Upload radiology PDF reports to generate anonymized patient personas*")
    st.markdown("---")

    st.markdown("""
    <div class="section-card">
      <div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-bottom:0.75rem">⚙️ How it works</div>
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

    st.markdown("### 🚀 Try the RadPersona App")
    st.info("Run locally with: `streamlit run app.py` — or the full app is integrated in this repository.")

    # Embed the actual app functionality
    try:
        import pdfplumber, io, zipfile, csv
        from datetime import datetime

        st.markdown("#### Upload Radiology PDF Reports")
        uploaded_files = st.file_uploader(
            "Upload PDF radiology reports",
            type=["pdf"],
            accept_multiple_files=True,
            key="pdf_uploader"
        )
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")
            st.info("Full processing available when running locally with app.py")
    except ImportError:
        st.warning("PDF processing libraries not available in this deployment.")


# ══════════════════════════════════════════════════════════════════════════
# PAGE: ABOUT & METHODS
# ══════════════════════════════════════════════════════════════════════════
elif page == "📋 About & Methods":
    st.markdown("## 📋 About & Methodology")
    st.markdown("---")

    st.markdown("""
    <div class="section-card">
      <div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-bottom:0.75rem">🎓 Project Details</div>
      <div style="font-size:0.875rem;color:#94a3b8;line-height:2.2">
        <b style="color:#e2e8f0">Title:</b> Development of a Large Language Model-based Digital Twin Framework
        for Automated Clinical Interpretation and Triage of Radiology Reports<br>
        <b style="color:#e2e8f0">Institution:</b> Federal University of Technology Minna, Nigeria<br>
        <b style="color:#e2e8f0">Faculty:</b> School of Physical Sciences (SPS)<br>
        <b style="color:#e2e8f0">Department:</b> Physics (Medical Physics)<br>
        <b style="color:#e2e8f0">Dataset:</b> 100 brain MRI reports from a private hospital in Abuja, Nigeria<br>
        <b style="color:#e2e8f0">AI Model:</b> Google Gemini 2.5 Flash<br>
        <b style="color:#e2e8f0">Framework:</b> Radiology Digital Twin Pipeline<br>
        <b style="color:#e2e8f0">Year:</b> 2026
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
        Python &nbsp;·&nbsp; Streamlit &nbsp;·&nbsp; Google Gemini AI &nbsp;·&nbsp;
        PDFPlumber &nbsp;·&nbsp; Matplotlib &nbsp;·&nbsp; NumPy &nbsp;·&nbsp; Pandas
      </div>
    </div>

    <div class="section-card" style="margin-top:1rem">
      <div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-bottom:0.75rem">📊 Model Performance Summary</div>
      <div style="font-size:0.875rem;color:#94a3b8;line-height:2">
        <b style="color:#e2e8f0">Overall Score:</b> <b style="color:#00d4aa">89.4/100</b><br>
        <b style="color:#e2e8f0">Parse Rate:</b> 100% — All 100 patients successfully processed<br>
        <b style="color:#e2e8f0">Response Quality:</b> 93.1/100 — 78% rated Excellent<br>
        <b style="color:#e2e8f0">Clinical Plausibility:</b> 90% — Clinically sound AI reasoning<br>
        <b style="color:#e2e8f0">DD Completeness:</b> 100% — All patients received ranked diagnoses
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center;font-size:0.8rem;color:#475569;font-family:'DM Mono',monospace">
      Federal University of Technology Minna &nbsp;·&nbsp;
      School of Physical Sciences &nbsp;·&nbsp;
      Department of Physics © 2026
    </div>
    """, unsafe_allow_html=True)
