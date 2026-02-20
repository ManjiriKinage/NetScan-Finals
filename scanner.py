# scanner.py
import nmap
import ipaddress
import shutil
import time
from rules import WEAK_PORTS, check_version

def ensure_nmap_available():
    return bool(shutil.which("nmap") or shutil.which("nmap.exe"))

def build_ip_list(subnet):
    try:
        net = ipaddress.ip_network(subnet, strict=False)
        return [str(ip) for ip in net.hosts()]
    except Exception:
        base = subnet.split("/")[0].strip()
        parts = base.split(".")
        if len(parts) == 4:
            prefix = ".".join(parts[:3]) + "."
            return [f"{prefix}{i}" for i in range(1, 255)]
        return [base]

def scan_network(subnet, progress_callback=None):
    """
    Runs an nmap -sV scan over the subnet.
    progress_callback(event_type, payload)
      - event_type: 'log' | 'progress' | 'device'
      - payload: string or dict
    """
    if progress_callback:
        progress_callback('log', f"Starting scan for subnet: {subnet}")

    if not ensure_nmap_available():
        raise RuntimeError("nmap_binary_not_found: nmap executable not found in PATH. Install nmap and add to PATH.")

    scanner = nmap.PortScanner()
    ip_list = build_ip_list(subnet)
    total = len(ip_list)
    results = []
    scanned = 0

    for ip in ip_list:
        try:
            if progress_callback:
                progress_callback('log', f"Scanning {ip}...")
            scanner.scan(ip, arguments='-sV -T4')
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

        device = {"host": ip, "vulnerabilities": []}

        try:
            for proto in scanner[ip].all_protocols():
                for port in scanner[ip][proto].keys():
                    svc = scanner[ip][proto][port]
                    product = svc.get("product", "") or ""
                    version = svc.get("version", "") or ""

                    if port in WEAK_PORTS:
                        device["vulnerabilities"].append(f"Port {port} open -> {WEAK_PORTS[port]}")

                    outdated = check_version(product, version)
                    if outdated:
                        device["vulnerabilities"].append(outdated)
        except Exception as e:
            if progress_callback:
                progress_callback('log', f"Warning parsing {ip}: {e}")

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
