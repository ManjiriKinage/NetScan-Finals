class IntentAgent:

    def detect(self, text):

        t = text.lower()

        if "scan" in t:
            return "scan"

        if "pdf" in t or "report" in t:
            return "pdf"

        if "risk" in t or "danger" in t:
            return "risk"
        
        if "manual" in t or "verify" in t or "test" in t:
            return "risk"

        return "chat"