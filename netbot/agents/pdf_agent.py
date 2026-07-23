import os
import pdfplumber
from flask import current_app
from openai import OpenAI
from google import genai

client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
genai_client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

SYSTEM_PROMPT = """You are a cybersecurity report analyst integrated into NetScan. 
You receive raw text extracted from a network scan PDF report.

Your job is to provide:
1. **Executive Summary** — One paragraph overview of the scan findings
2. **Key Findings** — Bullet list of the most important vulnerabilities and risks discovered
3. **Affected Assets** — Which IPs/hosts are most at risk and why
4. **Risk Rating** — Overall risk level (Critical/High/Medium/Low) with justification
5. **Recommended Actions** — Top 3-5 prioritized next steps

Be concise but thorough. Use markdown formatting."""


class PDFAgent:

    def analyze(self, path):

        if not path:
            return "No report attached. Please upload a PDF scan report using the 📎 button."

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

            # Use AI to generate an intelligent summary
            user_prompt = f"""Analyze this network scan report and provide an intelligent security summary:

{text[:6000]}"""

            # Try OpenAI first
            try:
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3
                )
                return res.choices[0].message.content.strip()
            except Exception:
                pass

            # Fallback to Gemini
            try:
                r = genai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_prompt
                )
                return r.text.strip()
            except Exception:
                pass

            # Final fallback: return raw text with basic formatting
            return f"""📄 **Report Extracted** (AI summary unavailable)

{text[:4000]}

> AI-powered analysis requires valid API keys. Raw text shown above."""

        except Exception as e:
            return f"PDF Error: {str(e)}"