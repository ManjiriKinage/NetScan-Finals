# NetScan – Local Vulnerability Scanner

NetScan is a simple web-based tool that scans a local network for open ports and potential vulnerabilities.  
It uses Nmap for scanning and provides results through a clean web interface with real-time logs and PDF report generation.

## Features
- Scan a subnet (e.g., 192.168.1.0/24)
- Detect open ports and weak services
- Identify outdated software versions
- View live logs and scan progress
- Download automatically generated PDF reports

## Requirements
- Python 3.10+
- Flask
- python-nmap
- FPDF
- Nmap installed and added to PATH

## Installation
```bash
git clone <repository-url>
cd NetScan
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
