from fpdf import FPDF
import datetime
import os

def _sanitize(text: str) -> str:
    """
    Make text safe for the default FPDF core fonts (Latin-1 only).
    - Replace Unicode arrows etc.
    - Fallback-encode to latin-1, replacing unsupported chars.
    """
    if text is None:
        return ""
    s = str(text)
    # Replace common problematic chars explicitly
    s = s.replace("→", "->")
    s = s.replace("’", "'")
    s = s.replace("“", '"').replace("”", '"')
    # Final safety: drop/replace anything non-latin-1
    return s.encode("latin-1", "replace").decode("latin-1")

def generate_pdf(report, output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"vulnerability_report_{timestamp}.pdf"
    path = os.path.join(output_dir, filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, txt=_sanitize("Local Vulnerability Scanner Report"), ln=True)
    pdf.cell(0, 8, txt=_sanitize(f"Date: {datetime.datetime.now()}"), ln=True)
    pdf.ln(4)

    for device in report:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, txt=_sanitize(f"Device: {device['host']}"), ln=True)
        pdf.set_font("Arial", size=11)
        if not device["vulnerabilities"]:
            pdf.cell(0, 7, txt=_sanitize("- No major vulnerabilities found"), ln=True)
        else:
            for v in device["vulnerabilities"]:
                pdf.multi_cell(0, 7, txt=_sanitize(f"- {v}"))
        pdf.ln(3)

    pdf.output(path)
    return path
