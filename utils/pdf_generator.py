from fpdf import FPDF
from PIL import Image
import datetime
import tempfile
import os


def safe_text(text: str) -> str:
    """Ensure text is a string."""
    if not isinstance(text, str):
        text = str(text)
    return text


class PDF(FPDF):
    def header(self):
        self.set_font("DejaVu", "B", 16)
        self.cell(0, 10, "BS7671 Calc – Voltage Drop & Compliance Report", ln=True, align="C")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.cell(0, 10, f"Generated on {datetime.date.today()} using BS7671 Calc", 0, 0, "C")


def generate_pdf(output_path, data, logo_file=None):
    pdf = PDF()
    pdf.add_page()

    # ✅ Register a Unicode font (you can use built-in DejaVu from fpdf2)
    from fpdf import FontFiles
    from fpdf.ttfonts import TTFont
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.add_font("DejaVu", "B", font_path, uni=True)
        pdf.add_font("DejaVu", "I", font_path, uni=True)
        pdf.set_font("DejaVu", "", 12)
    else:
        pdf.set_font("Helvetica", "", 12)

    # --- Optional logo ---
    if logo_file is not None:
        try:
            img = Image.open(logo_file)
            temp_logo = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            img.save(temp_logo.name, format="PNG")
            pdf.image(temp_logo.name, 160, 8, 35)
            os.unlink(temp_logo.name)
        except Exception:
            pass

    # --- Project Info ---
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Project Information", ln=True, fill=True)
    pdf.set_font("DejaVu", "", 11)

    pdf.cell(95, 8, f"Engineer: {safe_text(data.get('engineer', 'N/A'))}", ln=False)
    pdf.cell(95, 8, f"Job Number: {safe_text(data.get('job_number', 'N/A'))}", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.date.today()}", ln=True)
    pdf.ln(5)

    # --- Circuit Details ---
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Circuit Details", ln=True, fill=True)
    pdf.set_font("DejaVu", "", 11)

    for key, value in data.items():
        if key not in ["engineer", "job_number", "compliant"]:
            label = key.replace("_", " ").title()
            pdf.cell(60, 8, f"{safe_text(label)}:", ln=False)
            pdf.cell(0, 8, safe_text(str(value)), ln=True)

    pdf.ln(5)

    # --- Compliance Section ---
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Compliance", ln=True, fill=True)

    compliant = data.get("compliant", "N/A").lower()
    pdf.set_font("DejaVu", "B", 12)
    if compliant == "yes":
        pdf.set_text_color(0, 128, 0)
        pdf.cell(0, 10, "✅ Compliant – Within BS7671 Voltage Drop Limits", ln=True)
    elif compliant == "no":
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 10, "❌ Not Compliant – Exceeds Voltage Drop Limits", ln=True)
    else:
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Compliance: {safe_text(compliant)}", ln=True)

    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)

    pdf.output(str(output_path))
    return output_path
