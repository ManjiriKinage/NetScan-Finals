import os
from openai import OpenAI
from google import genai

client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
genai_client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

SYSTEM_PROMPT = """You are a senior cybersecurity risk analyst integrated into NetScan, a network vulnerability scanner.

Your job is to analyze scan reports and provide:
1. **Risk Assessment** — Overall risk level with justification
2. **Manual Verification Steps** — Specific commands the user should run to manually verify each finding
3. **Priority Matrix** — Which issues to address first and why
4. **False Positive Indicators** — Signs that a finding might be a false positive

Be specific to the actual data provided. Reference specific IPs, ports, services, and CVEs from the report.
Use markdown formatting with headers, bold, and lists for clarity."""


class RiskAgent:

    def manual_verify(self, report_text, context=None):

        if not report_text or report_text.strip() == "":
            return "No scan data available. Please run a scan first or upload a report."

        user_prompt = f"""Analyze this network scan report and provide a detailed risk assessment with manual verification steps.

Scan Report / User Query:
{report_text[:4000]}

Provide specific, actionable risk analysis based on the actual findings above."""

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Include conversation context for follow-up questions
        if context and isinstance(context, list):
            # Add last few messages for context (avoid token overflow)
            for msg in context[-6:]:
                if msg.get("role") in ("user", "assistant"):
                    messages.append(msg)

        messages.append({"role": "user", "content": user_prompt})

        # Try OpenAI first
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
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
        except Exception as e:
            return f"⚠️ AI analysis unavailable: {str(e)}. Please check your API keys."