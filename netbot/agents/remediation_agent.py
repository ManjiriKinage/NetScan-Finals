import os
from openai import OpenAI
from google import genai

client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
genai_client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

SYSTEM_PROMPT = """You are a cybersecurity remediation specialist integrated into NetScan, a network vulnerability scanner.

Your job is to analyze scan findings and provide:
1. **Priority Remediation Plan** — Ordered list of fixes by severity (Critical → High → Medium → Low)
2. **Specific Fix Commands** — Exact commands to run on each affected system (Linux and Windows variants)
3. **Patch Recommendations** — Which software to update, with version targets
4. **Configuration Hardening** — Specific firewall rules, service configs, and security settings to change
5. **Estimated Effort** — Time estimate for each fix

Be specific to the actual data provided. Reference specific IPs, ports, services, and CVEs from the report.
Use markdown formatting with headers, bold, code blocks, and lists for clarity."""


class RemediationAgent:

    def recommend(self, report_text, context=None):

        if not report_text or report_text.strip() == "":
            return "No scan data available. Please run a scan first or upload a report."

        user_prompt = f"""Based on this network scan report, provide a detailed, prioritized remediation plan with specific fix commands.

Scan Report / User Query:
{report_text[:4000]}

Provide actionable remediation steps specific to the findings above."""

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Include conversation context for follow-up questions
        if context and isinstance(context, list):
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