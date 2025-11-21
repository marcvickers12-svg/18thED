import streamlit as st
import math
import pandas as pd
import datetime
import tempfile
from pathlib import Path
from utils.pdf_generator import generate_pdf  # ensure utils/pdf_generator.py exists

# --- PAGE CONFIG ---
st.set_page_config(page_title="BS7671 Calc – 18th Edition", page_icon="⚡", layout="centered")

st.title("⚡ BS7671 Calc – Voltage Drop, Derating & Protective Device Tool")
st.caption("Complies with BS 7671:2018 + A2:2022")

# ===================== PROJECT DETAILS =====================
st.header("📋 Project Information")
engineer_name = st.text_input("Engineer Name")
job_number = st.text_input("Job Number")
company_logo = st.file_uploader("Upload Company Logo (optional)", type=["png", "jpg", "jpeg"])

st.divider()

# ===================== CIRCUIT INPUTS =====================
st.header("🔌 Circuit Parameters")
ib = st.number_input("Design Current (Ib) [A]", min_value=0.1, step=0.1, value=10.0)
iz_base = st.number_input("Base Cable Capacity (Iz) [A]", min_value=0.1, step=0.1, value=16.0)

# ===================== DERATING SECTION =====================
st.header("⚙️ Derating Factors (Tables 4C1 / 4C2 / 4C3)")

ca_dict = {
    "1.00 - ≤30°C": 1.00,
    "0.94 - 35°C": 0.94,
    "0.87 - 40°C": 0.87,
    "0.79 - 45°C": 0.79,
    "0.71 - 50°C": 0.71,
    "0.61 - 55°C": 0.61
}
cg_dict = {
    "1.00 - 1 Circuit": 1.00,
    "0.85 - 2 Circuits": 0.85,
    "0.70 - 3 Circuits": 0.70,
    "0.63 - 4 Circuits": 0.63,
    "0.60 - 5 Circuits": 0.60,
    "0.57 - 6 Circuits": 0.57
}
ci_dict = {
    "1.00 - Clipped Direct / In Free Air": 1.00,
    "0.89 - Touching Wall": 0.89,
    "0.75 - Enclosed in Conduit (in insulation)": 0.75,
    "0.63 - Totally Surrounded by Insulation": 0.63
}

ca = st.selectbox("Ambient Temperature Factor (Ca)", ca_dict.keys())
cg = st.selectbox("Grouping Factor (Cg)", cg_dict.keys())
ci = st.selectbox("Thermal Insulation Factor (Ci)", ci_dict.keys())

ca_val, cg_val, ci_val = ca_dict[ca], cg_dict[cg], ci_dict[ci]
cd = round(ca_val * cg_val * ci_val, 3)
iz_corrected = round(iz_base * cd, 2)

if ib <= iz_corrected:
    compliant = True
    thermal_text = f"✅ PASS — Ib = {ib} A ≤ Iz × Cd = {iz_corrected} A"
    thermal_color = "green"
else:
    compliant = False
    thermal_text = f"❌ FAIL — Ib = {ib} A > Iz × Cd = {iz_corrected} A"
    thermal_color = "red"

st.markdown(f"**Total Derating Factor (Cd):** {cd}")
st.markdown(f"**Corrected Capacity (Iz × Cd):** {iz_corrected} A")
st.markdown(f"<div style='background-color:{thermal_color};padding:15px;border-radius:10px;text-align:center;color:white;font-size:22px;font-weight:bold;'>{thermal_text}</div>", unsafe_allow_html=True)

# ===================== VOLTAGE DROP =====================
st.header("🔋 Voltage Drop Compliance (Appendix 4)")
cable_data = {
    "PVC T&E (Table 4D5)": {"1.5 mm²": (12.1, 0.08), "2.5 mm²": (7.41, 0.08), "4.0 mm²": (4.61, 0.08), "6.0 mm²": (3.08, 0.08), "10 mm²": (1.83, 0.07)},
    "XLPE SWA (Table 4E2A)": {"2.5 mm²": (7.41, 0.08), "4.0 mm²": (4.61, 0.08), "6.0 mm²": (3.08, 0.08), "10 mm²": (1.83, 0.07), "16 mm²": (1.15, 0.07), "25 mm²": (0.727, 0.07)},
}

cable_type = st.selectbox("Cable Type", list(cable_data.keys()))
cable_size = st.selectbox("Cable Size", list(cable_data[cable_type].keys()))
r_auto, x_auto = cable_data[cable_type][cable_size]
st.markdown(f"**Auto-selected:** R = {r_auto} mΩ/m | X = {x_auto} mΩ/m")

manual_override = st.checkbox("Manually override R and X values")
if manual_override:
    r = st.number_input("Resistance R (mΩ/m)", min_value=0.01, value=r_auto)
    x = st.number_input("Reactance X (mΩ/m)", min_value=0.01, value=x_auto)
else:
    r, x = r_auto, x_auto

voltage = st.number_input("System Voltage (V)", min_value=100, max_value=1000, value=230)
length = st.number_input("Cable Length (m)", min_value=1.0, step=1.0, value=20.0)
pf = st.number_input("Power Factor (pf)", min_value=0.1, max_value=1.0, value=0.9)

r_ohm = r / 1000
x_ohm = x / 1000
vd = ib * (r_ohm * math.cos(math.acos(pf)) + x_ohm * math.sin(math.acos(pf))) * length * 2
vd_percent = round((vd / voltage) * 100, 2)

usage_type = st.selectbox("Circuit Type", ["Lighting (3%)", "General / Other (5%)"])
limit = 3 if "Lighting" in usage_type else 5
vdrop_compliant = vd_percent <= limit
v_color = "green" if vdrop_compliant else "red"
vdrop_text = f"{'✅ PASS' if vdrop_compliant else '❌ FAIL'} — Voltage Drop = {vd_percent:.2f}% {'≤' if vdrop_compliant else '>'} {limit}% limit"

st.markdown(f"**Voltage Drop (V):** {vd:.2f}")
st.markdown(f"**Voltage Drop (%):** {vd_percent:.2f}%")
st.markdown(f"<div style='background-color:{v_color};padding:15px;border-radius:10px;text-align:center;color:white;font-size:22px;font-weight:bold;'>{vdrop_text}</div>", unsafe_allow_html=True)

# ===================== PROTECTIVE DEVICE =====================
st.header("⚙️ Protective Device Calculator (MCB / Fuse)")
device_type = st.selectbox("Protective Device Type", ["MCB", "Fuse"])

if device_type == "MCB":
    mcb_type = st.selectbox("MCB Curve", ["Type B", "Type C", "Type D"])
    standard_ratings = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100]
    auto_in = min([s for s in standard_ratings if s >= ib], default=standard_ratings[-1])
    device_label = f"{mcb_type} MCB"
else:
    fuse_standard = st.selectbox("Fuse Type", ["BS 88", "BS 1361", "BS 3036"])
    fuse_ratings = [5, 10, 15, 20, 25, 30, 32, 40, 45, 50, 60, 63, 80, 100, 125]
    auto_in = min([s for s in fuse_ratings if s >= ib], default=fuse_ratings[-1])
    if fuse_standard == "BS 3036":
        effective_in = auto_in * 0.725
    else:
        effective_in = auto_in
    device_label = f"{fuse_standard} Fuse (effective {effective_in:.1f}A)"

# --- Compliance Check ---
if device_type == "MCB":
    compliant_mcb = ib <= auto_in <= iz_corrected
    protect_text = f"✅ PASS — Ib = {ib}A ≤ In = {auto_in}A ≤ Iz×Cd = {iz_corrected}A" if compliant_mcb else f"❌ FAIL — In = {auto_in}A outside Ib/Iz limits"
    protect_color = "green" if compliant_mcb else "red"
else:
    compliant_mcb = ib <= effective_in <= iz_corrected
    protect_text = f"✅ PASS — Ib = {ib}A ≤ Fuse In = {effective_in:.1f}A ≤ Iz×Cd = {iz_corrected}A" if compliant_mcb else f"❌ FAIL — Fuse In = {effective_in:.1f}A outside Ib/Iz limits"
    protect_color = "green" if compliant_mcb else "red"

st.markdown(f"**Selected Device:** {device_label}")
st.markdown(f"<div style='background-color:{protect_color};padding:15px;border-radius:10px;text-align:center;color:white;font-size:22px;font-weight:bold;'>{protect_text}</div>", unsafe_allow_html=True)

# ===================== EXPORT SECTION =====================
st.divider()
st.header("📤 Export Compliance Report")

if st.button("📄 Generate PDF Report"):
    today_str = datetime.date.today().strftime("%d-%m-%Y")
    calc_results = {
        "engineer": engineer_name or "N/A",
        "job_number": job_number or "N/A",
        "Device Type": device_type,
        "Device Details": device_label,
        "Device Rating": auto_in,
        "Device Compliance": "PASS" if compliant_mcb else "FAIL",
        "Cable Type": cable_type,
        "Cable Size": cable_size,
        "Resistance R (mΩ/m)": r,
        "Reactance X (mΩ/m)": x,
        "Length (m)": length,
        "Power Factor": pf,
        "Ib": ib,
        "Iz Base": iz_base,
        "Ca": ca_val,
        "Cg": cg_val,
        "Ci": ci_val,
        "Cd": cd,
        "Iz Corrected": iz_corrected,
        "Thermal Compliance": "PASS" if compliant else "FAIL",
        "Voltage Drop (V)": f"{vd:.2f}",
        "Voltage Drop (%)": f"{vd_percent:.2f}",
        "Voltage Drop Limit": f"{limit} %",
        "Voltage Compliance": "PASS" if vdrop_compliant else "FAIL",
        "Overall Compliance": "PASS" if (compliant and vdrop_compliant and compliant_mcb) else "FAIL"
    }

    temp_dir = tempfile.gettempdir()
    pdf_path = Path(temp_dir) / f"BS7671_Report_{today_str}.pdf"
    generate_pdf(pdf_path, calc_results, logo_file=company_logo)

    with open(pdf_path, "rb") as f:
        st.download_button(
            label="⬇️ Download BS7671 PDF Report",
            data=f,
            file_name=f"BS7671_Report_{job_number or 'Report'}_{today_str}.pdf",
            mime="application/pdf"
        )
