class RiskAgent:

    def manual_verify(self, report_text):

        return f"""
Manual Verification Guide:

1. Port Scan
   Run: nmap -sS -sV <IP>

2. Service Check
   netstat -an / ss -lntp

3. Firewall Audit
   ufw status / Windows Defender Firewall

4. Patch Validation
   Check OS updates

5. Auth Testing
   Try weak credentials (authorized only)

6. Log Review
   /var/log/auth.log or Event Viewer

7. CVE Cross Check
   Search NVD for detected services

8. Config Review
   Inspect router and server configs

Report Context:
{report_text[:1000]}
"""