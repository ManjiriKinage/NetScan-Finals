from flask import Blueprint, request, jsonify
from netbot.cache import make_hash, get_cache, save_cache
from netbot.agents.intent_agent import IntentAgent
from netbot.agents.ai_agent import AIAgent
from netbot.agents.pdf_agent import PDFAgent
from netbot.mcp_orchestrator import MCP
from collections import defaultdict
from netbot.agents.risk_agent import RiskAgent
from netbot.agents.remediation_agent import RemediationAgent
from netbot.agents.troubleshoot_agent import TroubleshootAgent
from netbot.agents.scan_agent import ScanAgent

# Session memory
SESSIONS = defaultdict(list)
SCAN_JOBS = {}
netbot_bp = Blueprint("netbot", __name__)

intent = IntentAgent()
scan_agent = ScanAgent()
agents = {
    "ai": AIAgent(),
    "pdf": PDFAgent(),
    "risk": RiskAgent(),
    "remedy": RemediationAgent(),
    "trouble": TroubleshootAgent(),
    "scan": scan_agent  
}

mcp = MCP(agents)


@netbot_bp.route("/netbot/chat", methods=["POST"])
def netbot_chat():

    data = request.json

    prompt = data.get("message")
    session = data.get("session", "default")
    context = SESSIONS[session]
    pdf_path = data.get("pdf_path")
    subnet = data.get("subnet")  # From the UI subnet input field
    frontend_job_id = data.get("job_id")  # From the frontend's currentJob

    cache_key = make_hash(prompt, context)

    cached = get_cache(cache_key)

    if cached:
        return jsonify({"reply": cached})

    mode = intent.detect(prompt)
    context.append({"role": "user", "content": prompt})

    # Use frontend job_id (tracks scans from both UI and netbot) as priority,
    # fall back to server-side SCAN_JOBS
    active_job_id = frontend_job_id or SCAN_JOBS.get(session)

    payload = {
        "context": context,
        "prompt": prompt,
        "pdf": pdf_path,
        "job_id": active_job_id,
        "cookies": {k: v for k, v in request.cookies.items()},
        "subnet": subnet
    }

    reply, model = mcp.route(mode, payload)
    # Save scan job id if present
    if "Job ID:" in reply:
        job_id = reply.split("Job ID:")[-1].strip()
        SCAN_JOBS[session] = job_id

# Force clean string output
    if isinstance(reply, (list, tuple)):
        reply = reply[0]

    reply = str(reply).strip()

    save_cache(cache_key, prompt, reply, model)
    context.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})