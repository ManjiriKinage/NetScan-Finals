import re
import requests


class ScanAgent:

    def __init__(self):
        self.base_url = "http://127.0.0.1:5000"

    def _extract_subnet(self, text):
        """Try to extract a subnet/IP from the user's message."""
        # Match CIDR like 192.168.0.0/24
        m = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})', text)
        if m:
            return m.group(1)
        # Match plain IP like 192.168.0.1
        m = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', text)
        if m:
            return m.group(1)
        # Default subnet
        return "192.168.0.0/24"

    def start_scan(self, prompt, cookies=None, subnet=None):
        """Start a scan via the main /scan endpoint."""
        # Priority: explicit subnet from UI > extracted from prompt > default
        if not subnet:
            subnet = self._extract_subnet(prompt or "")
        try:
            res = requests.post(
                f"{self.base_url}/scan",
                json={"subnet": subnet},
                cookies=cookies,
                timeout=10
            )
            data = res.json()
            if res.status_code == 202:
                return {
                    "job_id": data.get("job_id"),
                    "subnet": subnet,
                    "message": "Scan started"
                }
            else:
                return {"error": data.get("error", "Scan failed")}
        except Exception as e:
            return {"error": str(e)}

    def cancel_scan(self, job_id, cookies=None):
        """Cancel a scan via the main /cancel endpoint."""
        if not job_id:
            return {"error": "No active scan to cancel"}
        try:
            res = requests.post(
                f"{self.base_url}/cancel/{job_id}",
                cookies=cookies,
                timeout=10
            )
            return res.json()
        except Exception as e:
            return {"error": str(e)}

    def get_status(self, job_id, cookies=None):
        """Get scan status via the main /status endpoint."""
        if not job_id:
            return {"error": "No active scan"}
        try:
            res = requests.get(
                f"{self.base_url}/status/{job_id}",
                cookies=cookies,
                timeout=10
            )
            data = res.json()
            progress = data.get("progress", 0)
            status = data.get("status", "unknown")
            total = data.get("summary", {})
            devices = total.get("total_devices", 0) if total else 0
            return {
                "status": status,
                "progress": progress,
                "devices_found": devices
            }
        except Exception as e:
            return {"error": str(e)}