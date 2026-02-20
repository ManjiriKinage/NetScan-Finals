from supabase import create_client
import os

SUPA_URL = os.getenv("SUPABASE_URL")
SUPA_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPA_URL or not SUPA_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env")

supabase = create_client(SUPA_URL, SUPA_KEY)

def get_cached_summary(scan_hash):

    res = supabase.table("ai_summary_cache") \
        .select("summary, model_used") \
        .eq("scan_hash", scan_hash) \
        .execute()

    if res.data:
        return res.data[0]

    return None


def save_summary(scan_hash, summary, model, tokens=0):

    supabase.table("ai_summary_cache").insert({
        "scan_hash": scan_hash,
        "model_used": model,
        "summary": summary,
        "token_count": tokens
    }).execute()