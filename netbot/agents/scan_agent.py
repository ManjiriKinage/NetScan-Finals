class RemediationAgent:

    def recommend(self, report_text):

        return f"""
Vulnerability Remediation Plan

HIGH PRIORITY (Fix First):
- Open remote access ports (SSH/RDP/FTP)
- Outdated critical services
- Unpatched OS vulnerabilities
- Weak authentication

MEDIUM PRIORITY:
- Minor service misconfigurations
- Legacy protocols (SMBv1, TLS 1.0)
- Unused open ports

LOW PRIORITY (Can Monitor):
- Informational findings
- Low-risk banners
- Local-only services

Recommended Actions:

1. Patch Systems Immediately
   - Run OS and software updates

2. Close Unused Ports
   - Use firewall rules

3. Harden Authentication
   - Strong passwords + MFA

4. Enable Monitoring
   - IDS / logs

5. Backup Before Changes
   - Prevent downtime

Report Context:
{report_text[:1200]}
"""