class TroubleshootAgent:

    def diagnose(self, report_text):

        return f"""
Vulnerability Troubleshooting Guide

If Issues Still Exist, Check:

1. Patch Not Applied
   - Verify updates installed
   - Reboot system
   - Check package versions

2. Service Still Running
   - systemctl status <service>
   - tasklist /services
   - netstat -tulpn

3. Firewall Misconfigured
   - ufw status verbose
   - iptables -L
   - Windows Firewall rules

4. Port Reopened by App
   - Check startup services
   - Disable auto-restart

5. False Positive
   - Re-scan manually
   - Cross-check with NVD

6. Config Not Saved
   - Restart service
   - Re-apply configs

7. Network Device Issue
   - Router rules
   - Port forwarding

8. Permission Errors
   - Run as admin/root
   - Check SELinux/AppArmor

Debug Commands:

Linux:
  sudo netstat -tulpn
  sudo ss -lntp
  sudo systemctl status

Windows:
  netstat -ano
  sc query
  Get-Service

Report Context:
{report_text[:1200]}
"""