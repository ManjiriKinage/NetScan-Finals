import os
import pdfplumber
from flask import current_app

class PDFAgent:

    def analyze(self, path):

        if not path:
            return "No report attached."

        try:

            filename = os.path.basename(path)

            base = os.path.join(current_app.root_path, "outputs")

            full_path = os.path.abspath(os.path.join(base, filename))

            if not full_path.startswith(base):
                return "Invalid file path."

            if not os.path.isfile(full_path):
                return "PDF not found."

            text = ""

            with pdfplumber.open(full_path) as pdf:
                for p in pdf.pages:
                    text += p.extract_text() or ""

            if not text.strip():
                return "PDF has no readable text."

            return f"""
    Report Summary:

    {text[:4000]}

    Security Actions:
    - Patch systems
    - Close ports
    - Harden firewall
    - Monitor logs
    """

        except Exception as e:
            return f"PDF Error: {str(e)}"