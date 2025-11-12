from fpdf import FPDF
from PIL import Image
import datetime
import tempfile
import os

def safe_text(text: str) -> str:
    """Convert text to Latin-1 safe encoding."""
    if not isinstance(text, str):
        text = str(text)
    return text.encode("latin-1", "replace").decode("latin-1")


class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, safe_text("BS7671 Calc – Voltage Drop & Compliance Report"), ln=True, align="C")
        self.ln(10)


def generate_pdf(output_path, data, logo_file=None):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # --- Optional logo section ---
    if logo_file is not None:
        try:
            img = Image.open(logo_file)
            temp_logo = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            img.save(temp_logo.name, format="PNG")
            pdf.image(temp_logo.name, 10, 8, 30)
            pdf.ln(25)
            os.unlink(temp_logo.name)
        except Exception as e:
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 10, safe_text(f"⚠️ Logo Error: {e}"), ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(10)

    # --- Project info ---
    pdf.cell(0, 10, safe_text(f"Engineer: {data.get('engineer', 'N/A')}"), ln=True)
    pdf.cell(0, 10, safe_text(f"Job Number: {data.get('job_number', 'N/A')}"), ln=True)
    pdf.cell(0, 10, safe_text(f"Date: {datetime.date.today()}"), ln=True)
    pdf.ln(5)

    # --- Circuit data ---
    for key, value in data.items():
        if key not in ["engineer", "job_number"]:
            pdf.cell(0, 10, safe_text(f"{key.replace('_', ' ').title()}: {value}"), ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, safe_text("Report generated using BS7671 Calc"), ln=True, align="C")

    # --- Save PDF safely ---
    pdf.output(str(output_path))
    return output_path
