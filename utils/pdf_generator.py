from fpdf import FPDF
from PIL import Image
import datetime
import io
import tempfile
import os


class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "BS7671 Calc – Voltage Drop & Compliance Report", ln=True, align="C")
        self.ln(10)


def generate_pdf(output_path, data, logo_file=None):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # ---- Optional company logo ----
    if logo_file is not None:
        try:
            image = Image.open(logo_file)
            temp_logo = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            image.save(temp_logo.name)
            pdf.image(temp_logo.name, 10, 8, 30)
            os.unlink(temp_logo.name)
        except Exception as e:
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 10, f"⚠️ Logo load error: {e}", ln=True)
            pdf.set_text_color(0, 0, 0)
        pdf.ln(25)
    else:
        pdf.ln(10)

    # ---- Header info ----
    pdf.cell(0, 10, f"Engineer: {data.get('engineer','N/A')}", ln=True)
    pdf.cell(0, 10, f"Job Number: {data.get('job_number','N/A')}", ln=True)
    pdf.cell(0, 10, f"Date: {datetime.date.today()}", ln=True)
    pdf.ln(8)

    # ---- Data table ----
    for key, value in data.items():
        if key not in ["engineer", "job_number"]:
            pdf.cell(0, 10, f"{key.replace('_', ' ').title()}: {value}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "Generated using BS7671 Calc", ln=True, align="C")

    # ---- Write PDF ----
    pdf.output(str(output_path))
    return output_path
