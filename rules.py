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
FIX_RECOMMENDATIONS = {
    21: "Disable FTP and use SFTP/SSH",
    23: "Disable Telnet and use SSH",
    80: "Enable HTTPS with TLS",
    3389: "Restrict RDP using firewall/VPN",
    5900: "Restrict VNC to private network"
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

