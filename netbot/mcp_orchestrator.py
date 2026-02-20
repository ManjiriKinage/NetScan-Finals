class MCP:

    def __init__(self, agents):
        self.agents = agents

    def route(self, intent, payload):

        if intent == "pdf":
            text = self.agents["pdf"].analyze(payload["pdf"])
            return text, "pdf"

        if intent == "risk":
            text = self.agents["risk"].manual_verify(
                payload.get("pdf") or payload.get("prompt", "")
            )
            return text, "risk"

        if intent == "chat":
            text, model = self.agents["ai"].chat(payload["context"])
            return text, model

        text, model = self.agents["ai"].chat(payload["context"])
        return text, model