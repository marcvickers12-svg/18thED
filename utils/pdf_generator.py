from fpdf import FPDF
from PIL import Image
import datetime
import tempfile
import os
import io

def safe_text(text: str) -> str:
    """Ensure text is string-safe for FPDF."""
    if not isinstance(text, str):
        text = str(text)
    return text


class PDF(FPDF):
    def __init__(self, logo_file=None):
        super().__init__()
        self.logo_file = logo_file

    def header(self):
        # --- Company Logo ---
        if self.logo_file:
            temp_path = None
            if isinstance(self.logo_file, io.BytesIO):
                img = Image.open(self.logo_file)
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                img.save(temp_file.name, format="PNG")
                temp_path = temp_file.name
            elif isinstance(self.logo_file, str) and os.path.exists(self.logo_file):
                temp_path = self.logo_file
            if temp_path:
                try:
                    self.image(temp_path, x=165, y=10, w=30)
                except Exception:
                    pass

        # --- Title ---
        self.set_y(20)
        self.set_font("DejaVu", "B", 16)
        self.cell(0, 10, safe_text("BS7671 Calc – Voltage Drop & Compliance Report"), ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        today_str = datetime.date.today().strftime("%d/%m/%Y")
        self.cell(0, 10, safe_text(f"Generated on {today_str} using BS7671 Calc v3"), 0, 0, "C")


def generate_pdf(output_path, data, logo_file=None):
    pdf = PDF(logo_file=logo_file)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.add_font("DejaVu", "B", font_path, uni=True)
    pdf.add_page()
    pdf.set_font("DejaVu", "", 12)

    # --- Project Info ---
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Project Information", ln=True, fill=True)
    pdf.set_font("DejaVu", "", 11)
    today_str = datetime.date.today().strftime("%d/%m/%Y")
    pdf.cell(0, 8, f"Engineer: {safe_text(data.get('engineer', 'N/A'))}", ln=True)
    pdf.cell(0, 8, f"Job Number: {safe_text(data.get('job_number', 'N/A'))}", ln=True)
    pdf.cell(0, 8, f"Date: {today_str}", ln=True)
    pdf.ln(5)

    # --- Protective Device Section ---
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Protective Device Information", ln=True, fill=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 8, f"Device Type: {safe_text(data.get('Device Type', 'N/A'))}", ln=True)
    pdf.cell(0, 8, f"Details: {safe_text(data.get('Device Details', 'N/A'))}", ln=True)
    pdf.cell(0, 8, f"Rating (In): {safe_text(data.get('Device Rating', 'N/A'))} A", ln=True)
    pdf.set_fill_color(200, 255, 200) if data.get("Device Compliance") == "PASS" else pdf.set_fill_color(255, 200, 200)
    pdf.cell(0, 10, f"Device Compliance: {data.get('Device Compliance')}", ln=True, fill=True)
    pdf.ln(5)

    # --- Derating Section ---
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Derating Factors", ln=True, fill=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 8, f"Ca: {data.get('Ca')} | Cg: {data.get('Cg')} | Ci: {data.get('Ci')} | Cd: {data.get('Cd')}", ln=True)
    pdf.cell(0, 8, f"Iz Base: {data.get('Iz Base')} A", ln=True)
    pdf.cell(0, 8, f"Iz Corrected: {data.get('Iz Corrected')} A", ln=True)
    pdf.set_fill_color(200, 255, 200) if data.get("Thermal Compliance") == "PASS" else pdf.set_fill_color(255, 200, 200)
    pdf.cell(0, 10, f"Thermal Compliance: {data.get('Thermal Compliance')}", ln=True, fill=True)
    pdf.ln(5)

    # --- Cable Info ---
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Cable Information", ln=True, fill=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 8, f"Cable Type: {data.get('Cable Type')}", ln=True)
    pdf.cell(0, 8, f"Size: {data.get('Cable Size')}", ln=True)
    pdf.cell(0, 8, f"R: {data.get('Resistance R (mΩ/m)')} mΩ/m | X: {data.get('Reactance X (mΩ/m)')} mΩ/m", ln=True)
    pdf.cell(0, 8, f"Length: {data.get('Length (m)')} m | Power Factor: {data.get('Power Factor')}", ln=True)
    pdf.ln(5)

    # --- Voltage Drop ---
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Voltage Drop Results", ln=True, fill=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 8, f"Voltage Drop (V): {data.get('Voltage Drop (V)')}", ln=True)
    pdf.cell(0, 8, f"Voltage Drop (%): {data.get('Voltage Drop (%)')} (Limit {data.get('Voltage Drop Limit')})", ln=True)
    pdf.set_fill_color(200, 255, 200) if data.get("Voltage Compliance") == "PASS" else pdf.set_fill_color(255, 200, 200)
    pdf.cell(0, 10, f"Voltage Drop Compliance: {data.get('Voltage Compliance')}", ln=True, fill=True)
    pdf.ln(5)

    # --- Overall ---
    overall = data.get("Overall Compliance", "N/A")
    if overall == "PASS":
        pdf.set_fill_color(0, 180, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 12, "✅ OVERALL COMPLIANCE: PASS", ln=True, align="C", fill=True)
    else:
        pdf.set_fill_color(200, 0, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 12, "❌ OVERALL COMPLIANCE: FAIL", ln=True, align="C", fill=True)
    pdf.set_text_color(0, 0, 0)

    pdf.output(str(output_path))
    return output_path
