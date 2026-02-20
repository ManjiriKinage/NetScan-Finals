class TroubleshootAgent:

    def diagnose(self, report_text):

        if not report_text:
            return "No scan report found. Please upload a report first."

        return f"""
Network Vulnerability Troubleshooting Guide

Based on your scan report, follow these steps if issues still exist.

1. Open Ports Still Visible
   - Run: nmap -sS -sV <IP>
   - Check firewall rules
   - Verify port forwarding on router

2. Service Still Running
   - Linux: systemctl status <service>
   - Windows: sc query <service>
   - Disable unnecessary services

3. Patch Not Applied
   - Verify OS updates
   - Reboot system
   - Check software version

4. Firewall Not Working
   - ufw status verbose
   - iptables -L
   - Windows Firewall rules

5. Weak Authentication
   - Check SSH/RDP configs
   - Disable password login
   - Enable MFA

6. False Positives
   - Re-scan manually
   - Cross-check CVE/NVD
   - Verify banner info

7. Configuration Not Saved
   - Restart service
   - Reload configs
   - Validate syntax

8. Network Device Issues
   - Router ACL rules
   - NAT configuration
   - VPN policies

Useful Commands:

Linux:
  sudo netstat -tulpn
  sudo ss -lntp
  sudo journalctl -xe

Windows:
  netstat -ano
  Get-Service
  Get-NetFirewallRule

Report Context:
{report_text[:1500]}

If problems continue, share specific error messages for deeper analysis.
"""