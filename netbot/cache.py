import hashlib, json, os
from supabase import create_client

SUPA_URL = os.getenv("SUPABASE_URL")
SUPA_KEY = os.getenv("SUPABASE_ANON_KEY")

db = create_client(SUPA_URL, SUPA_KEY)


def make_hash(prompt, ctx):
    raw = json.dumps([prompt, ctx], sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()

def get_cache(h):

    r = db.table("netbot_ai_cache") \
        .select("response") \
        .eq("request_hash", h) \
        .execute()

    if r.data:
        return r.data[0]["response"]

    return None


def save_cache(h, prompt, resp, model, tokens=0):

    db.table("netbot_ai_cache").insert({
        "request_hash": h,
        "user_prompt": prompt,
        "response": resp,
        "model_used": model,
        "token_used": tokens
    }).execute()

