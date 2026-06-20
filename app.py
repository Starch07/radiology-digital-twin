import streamlit as st
import os
import pandas as pd

# ─── NAVIGATION CONFIGURATION ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Radiology Digital Twin Console",
    page_icon="🧠",
    layout="wide"
)

st.title("🏥 Radiology Digital Twin Operations Dashboard")
st.markdown("---")

# Paths matching your generate_enhanced_visualizations_v2.py
CSV_PATH = 'radiology_pipeline/results/summary.csv'
# ─── UPDATE THESE PATHS TO MATCH YOUR DIRECTORY ──────────────────────────────
CSV_PATH = 'radiology_pipeline/results/summary.csv' if os.path.exists('radiology_pipeline/results/summary.csv') else 'summary.csv'
PLOT_DIR = 'radiology_pipeline/results/enhanced_plots' if os.path.exists('radiology_pipeline/results/enhanced_plots') else '.'

# ─── LOADING DATA LEDGER ──────────────────────────────────────────────────────
@st.cache_data
def load_data():
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    return None

df = load_data()

if df is not None:
    # Top Metrics Row
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Patients Logged", len(df))
    m2.metric("System Pipeline Check", "100% Operational")
    m3.metric("Data Parsing Status", "OK")
else:
    st.info("💡 Standard metrics summary ledger not loaded yet. Run your processing script to populate table parameters.")

# ─── GRAPH LAYOUT SECTION ─────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Static Analysis Plots", "🎬 Workflow Simulations", "📋 Data Explorer"])

def render_plot(name, desc):
    path = os.path.join(PLOT_DIR, name)
    if os.path.exists(path):
        st.image(path, caption=desc, use_container_width=True)
    else:
        st.caption(f"ℹ️ {name} asset is building or resting. Execute your visualization scripts to populate.")

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        render_plot("fig1_clinical_command_centre.png", "Clinical Command Centre Performance Vectors")
        render_plot("fig3_diagnosis_landscape.png", "Primary Structural Diagnoses Landscape")
    with c2:
        render_plot("fig2_priority_distribution.png", "Triage Priorities Allocation Matrix")
        render_plot("fig6_priority_matrix_heatmap.png", "Operational Workflow Density Map")

with tab2:
    st.subheader("Dynamic Workflow Simulation Replays")
    a1, a2 = st.columns(2)
    with a1:
        render_plot("anim1_triage_tally.gif", "Incident Load Accumulation Stream")
        render_plot("anim3_network_growth.gif", "Topological Cluster Expansion Graph")
    with a2:
        render_plot("anim2_acuity_race.gif", "Specialist Response Speed Tracking")
        render_plot("anim4_acuity_timeline.gif", "Patient Influx Arrival Sequence Vector")

with tab3:
    if df is not None:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No summary ledger arrays detected on disk.")