import os
from openai import OpenAI
from google import genai

client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
genai_client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

SYSTEM_PROMPT = """You are a network troubleshooting expert integrated into NetScan, a network vulnerability scanner.

Your job is to help users troubleshoot issues found in their scan reports:
1. **Issue Diagnosis** — Identify the root cause of each finding
2. **Step-by-Step Resolution** — Provide exact commands and procedures to fix each issue
3. **Verification Steps** — How to confirm the issue is resolved after applying fixes
4. **Common Pitfalls** — Mistakes to avoid during troubleshooting
5. **Escalation Guidance** — When to involve other teams or specialists

Provide platform-specific commands (Linux/Windows) where applicable.
Be specific to the actual data provided. Reference specific IPs, ports, services, and CVEs from the report.
Use markdown formatting with headers, bold, code blocks, and lists for clarity."""


class TroubleshootAgent:

    def diagnose(self, report_text, context=None):

        if not report_text or report_text.strip() == "":
            return "No scan data available. Please run a scan first or upload a report."

        user_prompt = f"""Based on this network scan report, provide detailed troubleshooting guidance for the issues found.

Scan Report / User Query:
{report_text[:4000]}

If the user mentions specific issues still persisting after remediation, focus on those. Otherwise, provide comprehensive troubleshooting for all findings."""

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