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
        # --- Company Logo (top-right corner) ---
        if self.logo_file:
            temp_path = None
            if isinstance(self.logo_file, io.BytesIO):  # Handle uploaded file
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
        self.cell(0, 10, safe_text(f"Generated on {datetime.date.today()} using BS7671 Calc v2"), 0, 0, "C")


def generate_pdf(output_path, data, logo_file=None):
    pdf = PDF(logo_file=logo_file)

    # --- Register Unicode-capable font ---
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.add_font("DejaVu", "B", font_path, uni=True)
        pdf.add_font("DejaVu", "I", font_path, uni=True)
    else:
        pdf.set_font("Helvetica", "", 12)

    pdf.add_page()
    pdf.set_font("DejaVu", "", 12)

    # --- Section: Project Info ---
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Project Information", ln=True, fill=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 8, f"Engineer: {safe_text(data.get('engineer', 'N/A'))}", ln=True)
    pdf.cell(0, 8, f"Job Number: {safe_text(data.get('job_number', 'N/A'))}", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.date.today()}", ln=True)
    pdf.ln(5)

    # --- Section: Derating Factors ---
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Derating Factors (BS7671 Tables 4C1–4C3)", ln=True, fill=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(95, 8, f"Ca (Temperature): {safe_text(data.get('Ca', 'N/A'))}", ln=False)
    pdf.cell(95, 8, f"Cg (Grouping): {safe_text(data.get('Cg', 'N/A'))}", ln=True)
    pdf.cell(95, 8, f"Ci (Insulation): {safe_text(data.get('Ci', 'N/A'))}", ln=False)
    pdf.cell(95, 8, f"Cd (Total): {safe_text(data.get('Cd', 'N/A'))}", ln=True)
    pdf.cell(0, 8, f"Iz Base: {safe_text(data.get('Iz Base', 'N/A'))} A", ln=True)
    pdf.cell(0, 8, f"Iz Corrected (Iz × Cd): {safe_text(data.get('Iz Corrected', 'N/A'))} A", ln=True)
    pdf.ln(5)

    # --- Thermal Compliance Section ---
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_fill_color(180, 255, 180) if data.get("Thermal Compliance") == "PASS" else pdf.set_fill_color(255, 200, 200)
    pdf.cell(0, 10,
              f"Thermal Compliance: {safe_text(data.get('Thermal Compliance', 'N/A'))}",
              ln=True, fill=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 8, f"Design Current (Ib): {safe_text(data.get('Ib', 'N/A'))} A", ln=True)
    pdf.cell(0, 8, f"Corrected Capacity (Iz × Cd): {safe_text(data.get('Iz Corrected', 'N/A'))} A", ln=True)
    pdf.ln(5)

    # --- Voltage Drop Section ---
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_fill_color(180, 255, 180) if data.get("Voltage Compliance") == "PASS" else pdf.set_fill_color(255, 200, 200)
    pdf.cell(0, 10, "Voltage Drop Compliance", ln=True, fill=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 8, f"Voltage Drop (V): {safe_text(data.get('Voltage Drop (V)', 'N/A'))}", ln=True)
    pdf.cell(0, 8, f"Voltage Drop (%): {safe_text(data.get('Voltage Drop (%)', 'N/A'))}", ln=True)
    pdf.cell(0, 8, f"Limit: {safe_text(data.get('Voltage Drop Limit', 'N/A'))}", ln=True)
    pdf.cell(0, 8, f"Compliance: {safe_text(data.get('Voltage Compliance', 'N/A'))}", ln=True)
    pdf.ln(5)

    # --- Overall Compliance ---
    pdf.set_font("DejaVu", "B", 14)
    overall = safe_text(data.get("Overall Compliance", "N/A"))
    if overall == "PASS":
        pdf.set_fill_color(0, 180, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 12, "✅ OVERALL COMPLIANCE: PASS", ln=True, align="C", fill=True)
    elif overall == "FAIL":
        pdf.set_fill_color(200, 0, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 12, "❌ OVERALL COMPLIANCE: FAIL", ln=True, align="C", fill=True)
    else:
        pdf.set_fill_color(255, 255, 150)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 12, f"⚠️ OVERALL STATUS: {overall}", ln=True, align="C", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)

    # --- Footer Note ---
    pdf.set_font("DejaVu", "I", 9)
    pdf.cell(0, 8, "All calculations are based on BS7671:2018+A2:2022.", ln=True, align="C")

    # --- Save PDF ---
    pdf.output(str(output_path))
    return output_path
