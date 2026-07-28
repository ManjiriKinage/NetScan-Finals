class MCP:

    def __init__(self, agents):
        self.agents = agents

    def route(self, intent, payload):

        context = payload.get("context", [])

        # PDF Summary
        if intent == "pdf":
            text = self.agents["pdf"].analyze(payload["pdf"])
            return text, "pdf"

        # Manual Verify / Risk Assessment
        if intent == "risk":
            text = self.agents["risk"].manual_verify(
                payload.get("pdf") or payload.get("prompt", ""),
                context=context
            )
            return text, "risk"

        # Remediation
        if intent == "remedy":
            text = self.agents["remedy"].recommend(
                payload.get("pdf") or payload.get("prompt", ""),
                context=context
            )
            return text, "remedy"

        # Troubleshooting
        if intent == "trouble":
            text = self.agents["trouble"].diagnose(
                payload.get("pdf") or payload.get("prompt", ""),
                context=context
            )
            return text, "trouble"

        # START SCAN
        if intent == "scan_start":
            target = payload.get("prompt")
            cookies = payload.get("cookies")
            subnet = payload.get("subnet")  # From UI input field
            result = self.agents["scan"].start_scan(target, cookies=cookies, subnet=subnet)
            if "error" in result:
                return f"⚠️ Could not start scan: {result['error']}", "scan"
            subnet = result.get("subnet", "unknown")
            return f"✅ Scan started for **{subnet}**! Job ID: {result['job_id']}\n\nYou can see live progress in the main dashboard. Type 'scan status' to check progress here.", "scan"

        # STOP SCAN
        if intent == "scan_stop":
            job = payload.get("job_id")
            cookies = payload.get("cookies")
            result = self.agents["scan"].cancel_scan(job, cookies=cookies)
            if "error" in result:
                return f"⚠️ {result['error']}", "scan"
            return "🛑 Scan cancelled.", "scan"

        # SCAN STATUS
        if intent == "scan_status":
            job = payload.get("job_id")
            cookies = payload.get("cookies")
            status = self.agents["scan"].get_status(job, cookies=cookies)
            if "error" in status:
                return f"⚠️ {status['error']}", "scan"
            return f"📊 Scan Status: **{status['status']}** | Progress: {status['progress']}% | Devices Found: {status['devices_found']}", "scan"

        # Normal chat
        if intent == "chat":
            text, model = self.agents["ai"].chat(payload["context"])
            return text, model

        text, model = self.agents["ai"].chat(payload["context"])
        return text, model