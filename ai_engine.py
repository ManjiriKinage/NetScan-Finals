# ai_engine.py

import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_KEY"))

model = genai.GenerativeModel("gemini-pro")


def summarize_report(report):

    if not os.getenv("GEMINI_KEY"):
        return "AI summary unavailable (API key not configured)"

    try:
        prompt = f"""
You are a cybersecurity expert.

Analyze this scan report:
{report}

Give:
1. Overall risk
2. Top 3 threats
3. Fix priority
4. Business impact
"""

        resp = model.generate_content(prompt)
        return resp.text

    except Exception as e:
        return f"AI summary failed: {str(e)}"