import streamlit as st
import math
import pandas as pd
import tempfile
from pathlib import Path

# --- Page Setup ---
st.set_page_config(page_title="BS7671 Calc – 18th Edition", page_icon="⚡", layout="centered")

st.title("⚡ BS7671 Calc – Voltage Drop & Thermal Compliance Tool")
st.caption("Conforms to BS 7671:2018 + A2:2022")

# --- User Inputs ---
st.header("🔌 Circuit Parameters")
ib = st.number_input("Design Current (Ib) [A]", min_value=0.1, step=0.1, value=10.0)
iz_base = st.number_input("Base Cable Capacity (Iz) [A]", min_value=0.1, step=0.1, value=16.0)

# ===================== DERATING SECTION =====================
st.header("⚙️ Derating Factors (Tables 4C1 / 4C2 / 4C3)")

# --- Correction Factors ---
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

# --- Drop-down Inputs ---
ca = st.selectbox("Ambient Temperature Factor (Ca)", ca_dict.keys())
cg = st.selectbox("Grouping Factor (Cg)", cg_dict.keys())
ci = st.selectbox("Thermal Insulation Factor (Ci)", ci_dict.keys())

ca_val, cg_val, ci_val = ca_dict[ca], cg_dict[cg], ci_dict[ci]
cd = round(ca_val * cg_val * ci_val, 3)
iz_corrected = round(iz_base * cd, 2)

# --- Thermal Compliance Check ---
if ib <= iz_corrected:
    compliant = True
    thermal_text = f"✅ PASS — Ib = {ib} A ≤ Iz × Cd = {iz_corrected} A"
    thermal_color = "green"
else:
    compliant = False
    thermal_text = f"❌ FAIL — Ib = {ib} A > Iz × Cd = {iz_corrected} A"
    thermal_color = "red"

st.markdown(f"**Total Derating Factor (Cd):** {cd}")
st.markdown(f"**Corrected Current-Carrying Capacity (Iz × Cd):** {iz_corrected} A")
st.markdown(
    f"""
    <div style="background-color:{thermal_color};padding:15px;border-radius:10px;text-align:center;color:white;font-size:22px;font-weight:bold;">
    {thermal_text}
    </div>
    """,
    unsafe_allow_html=True
)

# --- Reference Tables ---
with st.expander("📘 Show BS7671 Derating Reference Tables"):
    st.markdown("#### Table 4C1 – Ambient Temperature (Ca)")
    st.dataframe(pd.DataFrame({
        "Ambient Temp (°C)": ["25", "30", "35", "40", "45", "50", "55", "60"],
        "Ca (PVC)": ["1.03", "1.00", "0.94", "0.87", "0.79", "0.71", "0.61", "0.50"],
        "Ca (XLPE)": ["1.04", "1.00", "0.96", "0.91", "0.87", "0.82", "0.76", "0.71"]
    }), use_container_width=True)

    st.markdown("#### Table 4C2 – Grouping (Cg)")
    st.dataframe(pd.DataFrame({
        "No. of Circuits": ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
        "Cg": ["1.00", "0.85", "0.70", "0.63", "0.60", "0.57", "0.54", "0.52", "0.50"]
    }), use_container_width=True)

    st.markdown("#### Table 4C3 – Thermal Insulation (Ci)")
    st.dataframe(pd.DataFrame({
        "Installation Condition": [
            "Clipped Direct / Free Air",
            "Touching Wall / Trunking",
            "Enclosed in Conduit (in insulation)",
            "Totally Surrounded by Insulation"
        ],
        "Ci": ["1.00", "0.89", "0.75", "0.63"]
    }), use_container_width=True)

# ===================== VOLTAGE DROP SECTION =====================
st.header("🔋 Voltage Drop Compliance (Appendix 4)")

voltage = st.number_input("System Voltage (V)", min_value=100, max_value=1000, value=230)
length = st.number_input("Cable Length (m)", min_value=1.0, step=1.0, value=20.0)
pf = st.number_input("Power Factor (pf)", min_value=0.1, max_value=1.0, value=0.9)
r = st.number_input("Resistance R (mΩ/m)", min_value=0.01, value=4.61) / 1000
x = st.number_input("Reactance X (mΩ/m)", min_value=0.01, value=0.08) / 1000

vd = ib * (r * math.cos(math.acos(pf)) + x * math.sin(math.acos(pf))) * length
vd_percent = round((vd / voltage) * 100, 2)

usage_type = st.selectbox("Circuit Type", ["Lighting (3%)", "General / Other (5%)"])
limit = 3 if "Lighting" in usage_type else 5

# --- Voltage Drop Compliance ---
if vd_percent <= limit:
    vdrop_compliant = True
    vdrop_text = f"✅ PASS — Voltage Drop = {vd_percent:.2f}% ≤ {limit}% limit"
    v_color = "green"
else:
    vdrop_compliant = False
    vdrop_text = f"❌ FAIL — Voltage Drop = {vd_percent:.2f}% > {limit}% limit"
    v_color = "red"

st.markdown(f"**Voltage Drop (V):** {vd:.2f}")
st.markdown(f"**Voltage Drop (%):** {vd_percent:.2f}%")

st.markdown(
    f"""
    <div style="background-color:{v_color};padding:15px;border-radius:10px;text-align:center;color:white;font-size:22px;font-weight:bold;">
    {vdrop_text}
    </div>
    """,
    unsafe_allow_html=True
)

# ===================== OVERALL SUMMARY =====================
st.header("🧾 Overall BS7671 Compliance Summary")

if compliant and vdrop_compliant:
    overall_text = "✅ PASS — Circuit complies with BS7671 (Thermal & Voltage Drop within limits)"
    overall_color = "green"
elif not compliant and not vdrop_compliant:
    overall_text = "❌ FAIL — Exceeds BS7671 limits for both thermal and voltage drop"
    overall_color = "red"
elif not compliant:
    overall_text = "⚠️ FAIL — Thermal current capacity exceeded"
    overall_color = "orange"
else:
    overall_text = "⚠️ FAIL — Voltage drop exceeds BS7671 limit"
    overall_color = "orange"

st.markdown(
    f"""
    <div style="background-color:{overall_color};padding:18px;border-radius:10px;text-align:center;color:white;font-size:24px;font-weight:bold;">
    {overall_text}
    </div>
    """,
    unsafe_allow_html=True
)
