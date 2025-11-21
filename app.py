import streamlit as st
import math
import json
import tempfile
from pathlib import Path
from utils.pdf_generator import generate_pdf

st.set_page_config(page_title="BS7671 Calc", page_icon="⚡", layout="centered")

# --- Title ---
st.title("⚡ BS7671 Calc – Voltage Drop, Derating & Zs Compliance Tool")
st.markdown("Complies with 18th Edition Wiring Regulations (BS7671)")

# --- Sidebar ---
with st.sidebar:
    st.header("Project Details")
    engineer = st.text_input("Engineer Name")
    job_number = st.text_input("Job Number")
    company_logo = st.file_uploader("Upload Company Logo (optional)", type=["png", "jpg", "jpeg"])

# --- Cable Selection ---
st.subheader("Cable & Installation Details")

cable_type = st.selectbox("Cable Type", ["SWA", "PVC Twin & Earth"])
size = st.selectbox("Cable Size (mm²)", [1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0])
install_method = st.selectbox("Installation Method", ["Clipped Direct", "In Conduit", "Thermal Insulation"])

length = st.number_input("Circuit Length (m)", min_value=1.0, value=30.0)
current = st.number_input("Design Current (A)", min_value=0.1, value=10.0)
voltage = 230
pf = st.slider("Power Factor", 0.1, 1.0, 0.9)

# --- Derating Factors ---
st.subheader("Derating Factors")
Ca = st.selectbox("Ambient Temperature Factor (Ca)", [1.0, 0.94, 0.87, 0.79, 0.71])
Cg = st.selectbox("Grouping Factor (Cg)", [1.0, 0.9, 0.8, 0.7, 0.6])
Ci = st.selectbox("Thermal Insulation Factor (Ci)", [1.0, 0.89, 0.75, 0.63])
Cd = st.selectbox("Other Derating Factor (Cd)", [1.0, 0.95, 0.9, 0.85])

# --- MCB Details ---
st.subheader("Protective Device")
device_type = st.selectbox("MCB Type", ["B", "C", "D"])
device_rating = st.selectbox("MCB Rating (A)", [6, 10, 16, 20, 32, 40, 50, 63])

# --- Resistance and Reactance Lookup (Safe Fallback) ---
try:
    with open("data/cable_data.json") as f:
        cable_data = json.load(f)
except FileNotFoundError:
    st.error("Could not find data file at: data/cable_data.json")
    st.stop()

size_key = str(size)
if size_key not in cable_data.get(cable_type, {}):
    st.error(f"⚠️ Cable size {size_key} mm² not found for {cable_type} in cable_data.json.")
    st.stop()

R = cable_data[cable_type][size_key]["R"]
X = cable_data[cable_type][size_key]["X"]

# --- Voltage Drop ---
vd = (math.sqrt(R ** 2 + X ** 2) * current * length) / 1000
vd_percent = (vd / voltage) * 100
limit = 5
vd_compliance = "PASS" if vd_percent <= limit else "FAIL"

# --- Derating Calculations ---
Iz_base = current * 1.45
Iz_corrected = Iz_base / (Ca * Cg * Ci * Cd)
thermal_compliance = "PASS" if Iz_corrected >= current else "FAIL"

# --- Zs Limit Table (BS7671) ---
zs_limits = {
    "B": {6: 7.67, 10: 4.41, 16: 2.76, 20: 2.21, 32: 1.38, 40: 1.1, 50: 0.88, 63: 0.69},
    "C": {6: 3.83, 10: 2.21, 16: 1.38, 20: 1.1, 32: 0.69, 40: 0.55, 50: 0.44, 63: 0.35},
    "D": {6: 1.92, 10: 1.1, 16: 0.69, 20: 0.55, 32: 0.35, 40: 0.28, 50: 0.22, 63: 0.17}
}

zs_limit = zs_limits[device_type][device_rating]
zs_calc = (R * length / 1000) + 0.35
zs_compliance = "PASS" if zs_calc <= zs_limit else "FAIL"

# --- Overall Compliance ---
if all(x == "PASS" for x in [vd_compliance, thermal_compliance, zs_compliance]):
    overall = "PASS"
else:
    overall = "FAIL"

# --- Display Results ---
st.subheader("Results")
col1, col2 = st.columns(2)
col1.metric("Voltage Drop (V)", f"{vd:.2f}")
col2.metric("Voltage Drop (%)", f"{vd_percent:.2f}%")
col1.metric("Derating Result", f"Iz={Iz_corrected:.2f} A ({thermal_compliance})")
col2.metric("Zs (Ω)", f"{zs_calc:.2f} Ω ({zs_compliance})")

if overall == "PASS":
    st.success("✅ Overall Compliance: PASS")
else:
    st.error("❌ Overall Compliance: FAIL")

# --- PDF Export ---
st.subheader("Export Compliance Report")
if st.button("📄 Generate PDF Report"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        calc_results = {
            "engineer": engineer,
            "job_number": job_number,
            "Cable Type": cable_type,
            "Cable Size": f"{size:.1f} mm²",
            "Resistance R (mΩ/m)": R,
            "Reactance X (mΩ/m)": X,
            "Length (m)": length,
            "Power Factor": pf,
            "Voltage Drop (V)": round(vd, 2),
            "Voltage Drop (%)": round(vd_percent, 2),
            "Voltage Drop Limit": f"{limit}%",
            "Voltage Compliance": vd_compliance,
            "Ca": Ca,
            "Cg": Cg,
            "Ci": Ci,
            "Cd": Cd,
            "Iz Base": round(Iz_base, 2),
            "Iz Corrected": round(Iz_corrected, 2),
            "Thermal Compliance": thermal_compliance,
            "Device Type": f"MCB Type {device_type}",
            "Device Rating": device_rating,
            "Zs Calculated": round(zs_calc, 2),
            "Zs Limit": zs_limit,
            "Zs Compliance": zs_compliance,
            "Overall Compliance": overall
        }

        generate_pdf(tmpfile.name, calc_results, logo_file=company_logo)
        st.download_button("⬇️ Download PDF", data=open(tmpfile.name, "rb").read(),
                           file_name=f"BS7671_Calc_Report_{job_number or 'report'}.pdf")
