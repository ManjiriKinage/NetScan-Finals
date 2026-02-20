WEAK_PORTS = {
    21: "FTP (No encryption)",
    23: "Telnet (Very insecure)",
    80: "HTTP (Use HTTPS)",
    3389: "RDP exposed",
    5900: "VNC exposed",
}

OUTDATED_SOFTWARE = {
    "apache": 2.4,
    "openssh": 8.0,
    "nginx": 1.20,
}

def check_version(service, version):
    service = (service or "").lower()
    if service in OUTDATED_SOFTWARE:
        try:
            if float(version) < OUTDATED_SOFTWARE[service]:
                return f"{service} version outdated (Installed: {version})"
        except Exception:
            pass
    return None

