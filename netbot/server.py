from flask import Blueprint, request, jsonify
from netbot.cache import make_hash, get_cache, save_cache
from netbot.agents.intent_agent import IntentAgent
from netbot.agents.ai_agent import AIAgent
from netbot.agents.pdf_agent import PDFAgent
from netbot.mcp_orchestrator import MCP
from collections import defaultdict
from netbot.agents.risk_agent import RiskAgent

# Session memory
SESSIONS = defaultdict(list)

netbot_bp = Blueprint("netbot", __name__)

intent = IntentAgent()

agents = {
    "ai": AIAgent(),
    "pdf": PDFAgent(),
    "risk": RiskAgent()
}

mcp = MCP(agents)


@netbot_bp.route("/netbot/chat", methods=["POST"])
def netbot_chat():

    data = request.json

    prompt = data.get("message")
    session = data.get("session", "default")
    context = SESSIONS[session]
    pdf_path = data.get("pdf_path")

    cache_key = make_hash(prompt, context)

    cached = get_cache(cache_key)

    if cached:
        return jsonify({"reply": cached})

    mode = intent.detect(prompt)
    context.append({"role": "user", "content": prompt})

    payload = {
        "context": context,
        "prompt": prompt,
        "pdf": pdf_path
    }

    reply, model = mcp.route(mode, payload)

# Force clean string output
    if isinstance(reply, (list, tuple)):
        reply = reply[0]

    reply = str(reply).strip()

    save_cache(cache_key, prompt, reply, model)
    context.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})