# scanner.py
import nmap
import ipaddress
import shutil
import time
from rules import WEAK_PORTS, check_version
from nvd_api import fetch_cve
from rules import FIX_RECOMMENDATIONS

# Scan profile configurations
SCAN_PROFILES = {
    "quick": {
        "args": "-sV -T4 --top-ports 100",
        "label": "Quick Scan (Top 100 ports)"
    },
    "standard": {
        "args": "-sV -T4 --top-ports 1000",
        "label": "Standard Scan (Top 1000 ports)"
    },
    "deep": {
        "args": "-sV -T4 -p-",
        "label": "Deep Scan (All 65535 ports)"
    }
}

def ensure_nmap_available():
    return bool(shutil.which("nmap") or shutil.which("nmap.exe"))

def build_ip_list(subnet):
    try:
        net = ipaddress.ip_network(subnet, strict=False)
        return [str(ip) for ip in net.hosts()]
    except ValueError:
        try:
             # Try parsing as a single IP
             ip = ipaddress.ip_address(subnet)
             return [str(ip)]
        except ValueError:
             raise ValueError(f"Invalid IP or subnet format: {subnet}")


def scan_network(subnet, progress_callback=None, profile="standard", os_detect=False, cancel_callback=None):
    """
    Runs an nmap scan over the subnet.
    progress_callback(event_type, payload)
      - event_type: 'log' | 'progress' | 'device'
      - payload: string or dict
    profile: 'quick' | 'standard' | 'deep'
    os_detect: if True, adds -O flag for OS detection
    cancel_callback: returns True when the scan should stop after the current host
    """
    # Get scan arguments from profile
    profile_config = SCAN_PROFILES.get(profile, SCAN_PROFILES["standard"])
    scan_args = profile_config["args"]

    # Add OS detection if requested
    if os_detect:
        scan_args += " -O"

    if progress_callback:
        progress_callback('log', f"Starting scan for subnet: {subnet}")
        progress_callback('log', f"Profile: {profile_config['label']}")

    if not ensure_nmap_available():
        raise RuntimeError("nmap_binary_not_found: nmap executable not found in PATH. Install nmap and add to PATH.")

    scanner = nmap.PortScanner()
    ip_list = build_ip_list(subnet)
    total = len(ip_list)
    results = []
    scanned = 0

    for ip in ip_list:
        if cancel_callback and cancel_callback():
            if progress_callback:
                progress_callback('log', "Scan cancellation requested.")
            return results

        try:
            if progress_callback:
                progress_callback('log', f"Scanning {ip}...")
            scanner.scan(ip, arguments=scan_args)
        except Exception as e:
            if progress_callback:
                progress_callback('log', f"Warning: scan failed for {ip}: {e}")
            scanned += 1
            if progress_callback:
                progress_callback('progress', (scanned * 100) // total)
            continue

        if ip not in scanner.all_hosts():
            scanned += 1
            if progress_callback:
                progress_callback('progress', (scanned * 100) // total)
            continue

        device = {
            "host": ip,
            "services": [],
            "vulnerabilities": [],
            "severity_score": 0,
            "os": None
        }

        # Extract OS detection info if available
        try:
            if os_detect and 'osmatch' in scanner[ip]:
                os_matches = scanner[ip]['osmatch']
                if os_matches:
                    best_match = os_matches[0]
                    device["os"] = {
                        "name": best_match.get("name", "Unknown"),
                        "accuracy": best_match.get("accuracy", "0"),
                        "type": best_match.get("osclass", [{}])[0].get("type", "Unknown") if best_match.get("osclass") else "Unknown"
                    }
        except Exception:
            pass

        try:
            for proto in scanner[ip].all_protocols():
                for port in scanner[ip][proto].keys():
                    svc = scanner[ip][proto][port]
                    product = svc.get("product", "") or ""
                    version = svc.get("version", "") or ""

                    device["services"].append({
                        "port": port,
                        "service": product,
                        "version": version
                    })

                    # Fetch CVEs from NVD
                    if product and version:
                        cves = fetch_cve(product, version)

                        for c in cves:
                            msg = f"{c['cve_id']} (CVSS {c['score']}) - {c['description'][:80]}"

                            device["vulnerabilities"].append(msg)

                            if c["score"]:
                                device["severity_score"] += float(c["score"])
                    if port in WEAK_PORTS:
                        fix = FIX_RECOMMENDATIONS.get(port, "Restrict access")

                        device["vulnerabilities"].append(
                            f"Port {port} open -> {WEAK_PORTS[port]} | Fix: {fix}"
                        )

                    outdated = check_version(product, version)
                    if outdated:
                        device["vulnerabilities"].append(outdated)
        except Exception as e:
            if progress_callback:
                progress_callback('log', f"Warning parsing {ip}: {e}")

        # Assign risk level
        score = device["severity_score"]

        if score >= 9:
            device["risk"] = "Critical"
        elif score >= 7:
            device["risk"] = "High"
        elif score >= 4:
            device["risk"] = "Medium"
        else:
            device["risk"] = "Low"

        results.append(device)
        if progress_callback:
            progress_callback('device', device)

        scanned += 1
        if progress_callback:
            progress_callback('progress', (scanned * 100) // total)

        time.sleep(0.05)

    if progress_callback:
        progress_callback('log', "Scan loop finished.")
    return results
