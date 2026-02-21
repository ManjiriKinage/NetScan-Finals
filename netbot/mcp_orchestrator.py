class MCP:

    def __init__(self, agents):
        self.agents = agents

    def route(self, intent, payload):

        # PDF Summary
        if intent == "pdf":
            text = self.agents["pdf"].analyze(payload["pdf"])
            return text, "pdf"

        # Manual Verify
        if intent == "risk":
            text = self.agents["risk"].manual_verify(
                payload.get("pdf") or payload.get("prompt", "")
            )
            return text, "risk"

        # Remediation
        if intent == "remedy":
            text = self.agents["remedy"].recommend(
                payload.get("pdf") or payload.get("prompt", "")
            )
            return text, "remedy"

        # Troubleshooting
        if intent == "trouble":
            text = self.agents["trouble"].diagnose(
                payload.get("pdf") or payload.get("prompt", "")
            )
            return text, "trouble"

        # START SCAN
        if intent == "scan_start":
            target = payload.get("prompt")
            result = self.agents["scan"].start_scan(target)
            return f"Scan started. Job ID: {result['job_id']}", "scan"

        # STOP SCAN
        if intent == "scan_stop":
            job = payload.get("job_id")
            result = self.agents["scan"].cancel_scan(job)
            return "Scan cancelled.", "scan"

        # SCAN STATUS
        if intent == "scan_status":
            job = payload.get("job_id")
            status = self.agents["scan"].get_status(job)
            return str(status), "scan"

        # Normal chat
        if intent == "chat":
            text, model = self.agents["ai"].chat(payload["context"])
            return text, model

        text, model = self.agents["ai"].chat(payload["context"])
        return text, model