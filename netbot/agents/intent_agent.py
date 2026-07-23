from difflib import SequenceMatcher


# Synonym groups mapped to intents
INTENT_SYNONYMS = {
    "scan_stop": [
        "stop scan", "cancel scan", "abort scan", "halt scan",
        "kill scan", "terminate scan", "end scan", "stop scanning",
        "cancel the scan", "stop the scan"
    ],
    "scan_status": [
        "scan status", "progress", "how far", "scan progress",
        "is it done", "scan update", "check status", "how is the scan",
        "are we done", "scan percentage", "what percent"
    ],
    "scan_start": [
        "start scan", "scan network", "run scan", "begin scan",
        "launch scan", "initiate scan", "find vulnerabilities",
        "check my network", "security audit", "vulnerability scan",
        "scan my network", "network scan", "scan subnet", "port scan",
        "check for vulnerabilities", "security scan", "discover devices",
        "detect vulnerabilities", "nmap scan", "scan devices"
    ],
    "pdf": [
        "pdf", "report", "analyze report", "read report", "summarize report",
        "analyze pdf", "read pdf", "summarize pdf", "what does the report say",
        "show report", "report summary", "document analysis", "analyze document",
        "uploaded file", "analyze file", "review report"
    ],
    "risk": [
        "risk", "danger", "manual", "verify", "test", "assessment",
        "risk assessment", "risk analysis", "how risky", "threat level",
        "risk level", "how dangerous", "security risk", "risk score",
        "evaluate risk", "risk evaluation", "manual verify", "manual check",
        "penetration test", "pen test"
    ],
    "remedy": [
        "fix", "solution", "priority", "remediate", "remediation",
        "how to fix", "patch", "resolve", "fix this", "what should i do",
        "action plan", "fix vulnerabilities", "security fix", "update",
        "how do i fix", "remediation plan", "mitigation", "countermeasure",
        "fix recommendation", "recommended fixes", "patching"
    ],
    "trouble": [
        "still", "not fixed", "issue", "problem", "troubleshoot",
        "why still", "still open", "still vulnerable", "doesn't work",
        "not working", "help me fix", "can't fix", "failing",
        "persists", "recurring", "keeps happening", "debug",
        "diagnose", "troubleshooting", "what went wrong"
    ]
}

# Flatten for quick keyword checking
INTENT_KEYWORDS = {}
for intent, phrases in INTENT_SYNONYMS.items():
    for phrase in phrases:
        INTENT_KEYWORDS[phrase] = intent


class IntentAgent:

    def detect(self, text):

        t = text.lower().strip()

        # 1. Exact phrase match (highest confidence)
        for phrase, intent in sorted(INTENT_KEYWORDS.items(), key=lambda x: -len(x[0])):
            if phrase in t:
                return intent

        # 2. Scan start — IP/subnet pattern detection
        import re
        if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', t):
            return "scan_start"

        # 3. Fuzzy matching against synonym groups (for typos and close matches)
        best_score = 0
        best_intent = "chat"

        for intent, phrases in INTENT_SYNONYMS.items():
            for phrase in phrases:
                score = SequenceMatcher(None, t, phrase).ratio()
                if score > best_score and score >= 0.6:
                    best_score = score
                    best_intent = intent

        return best_intent