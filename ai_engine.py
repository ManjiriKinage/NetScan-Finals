from ai_hash import make_scan_hash
from ai_cache_supabase import get_cached_summary, save_summary

import openai
from groq import Groq
from google import genai
import os


OPENAI_KEY = os.getenv("OPENAI_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "openai/gpt-oss-20b")


openai.api_key = OPENAI_KEY
genai_client = genai.Client(api_key=GEMINI_KEY)


def call_groq(prompt, model):
    client = Groq(api_key=GROQ_KEY)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return resp.choices[0].message.content


def call_openai(prompt):
    client = openai.OpenAI(api_key=OPENAI_KEY)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        temperature=0.3
    )

    return resp.choices[0].message.content


def call_gemini(prompt):

    res = genai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return res.text


def summarize_report(report):

    # Create fingerprint
    scan_hash = make_scan_hash(report)

    # Check cache
    cached = get_cached_summary(scan_hash)

    if cached:
        print("[AI] Cache hit")
        return cached["summary"]

    prompt = build_prompt(report)

    # Try Groq first, then its smaller fallback model.
    if GROQ_KEY:
        for model in (GROQ_MODEL, GROQ_FALLBACK_MODEL):
            try:
                print(f"[AI] Using Groq ({model})")

                summary = call_groq(prompt, model)

                save_summary(scan_hash, summary, f"groq:{model}")

                return summary

            except Exception as e:
                print(f"[AI] Groq ({model}) failed:", e)

    # Try OpenAI next
    try:

        print("[AI] Using OpenAI")

        summary = call_openai(prompt)

        save_summary(scan_hash, summary, "openai")

        return summary

    except Exception as e:

        print("[AI] OpenAI failed:", e)


    # Fallback to Gemini
    try:

        print("[AI] Using Gemini")

        summary = call_gemini(prompt)

        save_summary(scan_hash, summary, "gemini")

        return summary

    except Exception as e:

        print("[AI] Gemini failed:", e)

        return "AI summary unavailable due to API limits."


def build_prompt(report):

    return f"""
You are a cybersecurity analyst.

Analyze this scan:

{report}

Give:
1. Risk overview
2. Top threats
3. Priority fixes
4. Business impact

Short and professional.
"""