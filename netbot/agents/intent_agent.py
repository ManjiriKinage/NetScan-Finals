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
        if "fix" in t or "solution" in t or "priority" in t or "remediate" in t:
            return "remedy"
        if "still" in t or "not fixed" in t or "issue" in t or "problem" in t or "troubleshoot" in t:
            return "trouble"
        # Start scan
        if "scan" in t and ("start" in t or "/" in t or "." in t):
            return "scan_start"

        # Stop scan
        if "stop scan" in t or "cancel scan" in t:
            return "scan_stop"

        # Status
        if "scan status" in t or "progress" in t:
            return "scan_status"

        return "chat"