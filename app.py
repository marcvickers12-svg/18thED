import streamlit as st
import json
import math
import sys
import os
import tempfile
import sys
from pathlib import Path

# --- Make sure we can import from utils folder ---
BASE_DIR = Path(__file__).resolve().parent
UTILS_PATH = BASE_DIR / "utils"
if str(UTILS_PATH) not in sys.path:
    sys.path.insert(0, str(UTILS_PATH))

from pdf_generator import generate_pdf


# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="Voltage Drop Calculator – 18th Edition",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("⚡ BS7671 Calc – Voltage Drop & Compliance Tool")
st.caption("Complies with BS 7671 | Includes derating & SWA support")

# ============ SIDEBAR: PROJECT INFO ============
st.sidebar.header("📋 Project Information")
engineer = st.sidebar.text_input("Engineer Name")
job_number = st.sidebar.text_input("Job Number")
company_logo = st.sidebar.file_uploader("Upload Company Logo (optional)", type=["png", "jpg", "jpeg"])

# --- FIX 2: Safely load cable data using absolute path ---
DATA_PATH = BASE_DIR / "data" / "cable_data.json"
if not DATA_PATH.exists():
    st.error(f"⚠️ Could not find data file at: {DATA_PATH}")
    st.stop()

with open(DATA_PATH, "r") as f:
    cable_data = json.load(f)

# ============ USER INPUTS ============
st.subheader("Circuit Details")

col1, col2 = st.columns(2)
with col1:
    current = st.number_input("Load current (A)", min_value=0.0, step=0.1)
    length = st.number_input("Cable length (m)", min_value=0.0, step=1.0)
    pf = st.number_input("Power factor", min_value=0.1, max_value=1.0, value=0.9)
with col2:
    voltage = st.number_input("Supply voltage (V)", min_value=100, max_value=1000, value=230)
    circuit_type = st.selectbox("Circuit type", ["Lighting (3%)", "General Use (5%)"])

st.markdown("---")

col3, col4 = st.columns(2)
with col3:
    cable_type = st.selectbox("Cable type", ["PVC Twin & Earth", "SWA"])
    material = st.selectbox("Material", ["Copper"])
with col4:
    size = st.selectbox("Cable size (mm²)", list(cable_data[cable_type].keys()))
    install_method = st.selectbox(
        "Installation method",
        ["Clipped Direct", "In Conduit in Wall", "On Cable Tray / Open Air",
         "In Thermal Insulation (100mm)", "Completely Surrounded by Insulation", "Buried Direct"]
    )

# ============ DERATING FACTORS ============
derating_factors = {
    "Clipped Direct": 1.00,
    "On Cable Tray / Open Air": 0.95,
    "In Conduit in Wall": 0.87,
    "In Thermal Insulation (100mm)": 0.70,
    "Completely Surrounded by Insulation": 0.50,
    "Buried Direct": 0.90
}
Ca = derating_factors[install_method]

# ============ CALCULATE ============
if st.button("Calculate Voltage Drop"):
    data = cable_data[cable_type][size]
    R = data["R"] / 1000  # Ω/m
    X = data["X"] / 1000  # Ω/m

    # Voltage drop (single phase)
    vd = current * (R * math.cos(math.acos(pf)) + X * math.sin(math.acos(pf))) * length
    vd_percent = (vd / voltage) * 100

    # Compliance
    limit = 3 if "Lighting" in circuit_type else 5
    compliant = vd_percent <= limit

    # Derated current
    Iz = current / Ca

    st.success("✅ Calculation complete")

    st.metric("Voltage Drop (V)", f"{vd:.2f}")
    st.metric("Voltage Drop (%)", f"{vd_percent:.2f}%")
    st.metric("Derated Current (A)", f"{Iz:.2f}")
    if compliant:
        st.success(f"Compliant (≤ {limit}% limit)")
    else:
        st.error(f"Not Compliant (> {limit}% limit)")

    # ============ PDF EXPORT ============
    if st.button("📄 Export to PDF"):
    temp_dir = tempfile.gettempdir()
    pdf_path = Path(temp_dir) / f"voltage_drop_report_{job_number or 'no_job'}.pdf"

    generate_pdf(pdf_path, {
        "engineer": engineer,
        "job_number": job_number,
        "cable_type": cable_type,
        "size": size,
        "install_method": install_method,
        "current": current,
        "length": length,
        "voltage": voltage,
        "pf": pf,
        "vd": vd,
        "vd_percent": vd_percent,
        "derating": Ca,
        "Iz": Iz,
        "compliant": compliant,
        "limit": limit
    }, logo_file=company_logo)

    with open(pdf_path, "rb") as file:
        st.download_button(
            label="⬇️ Download PDF Report",
            data=file,
            file_name=f"BS7671_Report_{job_number or 'Untitled'}.pdf",
            mime="application/pdf"
        )
