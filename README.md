# 🛡️ NetScan — Autonomous Network Vulnerability Assessment & Multi-Agent Remediation

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python Version" />
  <img src="https://img.shields.io/badge/Flask-Web%20Framework-lightgrey?style=for-the-badge&logo=flask" alt="Flask" />
  <img src="https://img.shields.io/badge/Nmap-Network%20Scanner-red?style=for-the-badge" alt="Nmap" />
  <img src="https://img.shields.io/badge/Supabase-Auth%20%26%20Cache-emerald?style=for-the-badge&logo=supabase" alt="Supabase" />
  <img src="https://img.shields.io/badge/MCP-Multi--Agent%20Architecture-purple?style=for-the-badge" alt="Model Context Protocol" />
</p>

---

## 📌 Overview

**NetScan** is an autonomous network vulnerability scanning and remediation platform designed for modern security teams and system administrators. It combines port scanning with live **NIST National Vulnerability Database (NVD) CVE v2.0** enrichment and pairs it with **NetBot** — a multi-agent AI framework orchestrated via the **Model Context Protocol (MCP)**.

With real-time scan logging, automated PDF compliance reports, vulnerability delta tracking (diffing), scheduled scans, and a multi-tier LLM fallback cascade (Groq LPUs, OpenAI, and Google Gemini), NetScan reduces Mean-Time-to-Triage (MTTT) and delivers grounded, actionable remediation guidance.

---

## ✨ Key Features

### 🔍 1. Multi-Profile Port & Vulnerability Scanning
- **Scanning Profiles**:
  - **Quick Scan**: Scans top 100 ports (`-sV -T4 --top-ports 100`) for rapid reconnaissance.
  - **Standard Scan**: Scans top 1000 ports (`-sV -T4 --top-ports 1000`) for standard posture evaluation.
  - **Deep Scan**: Comprehensive scan across all 65,535 ports (`-sV -T4 -p-`).
- **OS Fingerprinting**: Optional TCP/IP stack OS detection (`-O`).
- **Live Stream & Graceful Cancellation**: Real-time progress updates and thread-safe cancellation callbacks.

### 🛡️ 2. NIST NVD CVE v2.0 Integration
- Real-time vulnerability enrichment for discovered services.
- Rate-limited and cached requests to avoid API throttling.
- Zero-hallucination CVSS scoring with official severity metrics (Critical, High, Medium, Low).

### 🤖 3. NetBot: MCP Multi-Agent Intelligence
An intelligent conversational assistant powered by a modular multi-agent architecture:
- **`IntentAgent`**: Classifies query intent and routes to specialized sub-agents.
- **`ScanAgent`**: Interacts with the scanning engine directly from the chat interface.
- **`RiskAgent`**: Evaluates security posture and categorizes threat priorities.
- **`RemediationAgent`**: Provides exact firewall commands, patch strategies, and hardening steps.
- **`TroubleshootAgent`**: Diagnoses network anomalies and connection bottlenecks.
- **`PDFAgent`**: Ingests, parses, and answers natural language questions over uploaded scan PDF reports.

### ⚡ 4. Multi-Tier LLM Cascade & SHA-256 Caching
- **Fallback Hierarchy**: Automatic failover from **Groq (Fast LPU inference)** $\rightarrow$ **OpenAI (GPT-4o-mini)** $\rightarrow$ **Google Gemini (2.5 Flash)**.
- **Supabase Cache**: Scans and queries are fingerprinted using SHA-256 hashes to deliver $O(1)$ duplicate query resolution at zero token cost.

### 📊 5. Scan History & Vulnerability Diffing
- Compare successive scans of the same subnet to detect:
  - 🔴 **New Vulnerabilities**: Newly exposed ports or unpatched services.
  - 🟢 **Resolved Vulnerabilities**: Mitigated or closed attack vectors.
  - ⚪ **Unchanged Surface**: Consistent baseline devices.

### ⏰ 6. Scheduled Scans & Automation
- Schedule automated background scans with configurable delay timers.
- Monitor active schedules, view pending runs, or cancel jobs on demand.

### 📑 7. Reporting & Notification
- **PDF Generation**: Detailed vulnerability audit reports generated via `fpdf2`.
- **Automated Email Dispatch**: Email reports directly to security administrators upon scan completion.

### 🔐 8. Role-Based Access & Security
- **Authentication**: Built on Supabase Auth with password strength validation.
- **RBAC**: Admin mode (full scan controls & email notifications) and Guest mode (read-only exploration).

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Frontend["Web Interface & Dashboard"]
        UI[Interactive UI / Controls]
        Chat[NetBot Conversational Assistant]
        Logs[Live SSE Log Stream]
    end

    subgraph Backend["Flask Core Service (app.py)"]
        Auth[Supabase Auth / RBAC]
        Scheduler[Scan Scheduler / Worker]
        Diff[Vulnerability Diff Engine]
        Reporter[PDF Generator & Mailer]
    end

    subgraph ScanningEngine["Scanner & Enrichment (scanner.py)"]
        Nmap[Nmap Engine (python-nmap)]
        NVD[NIST NVD API v2.0]
        Rules[Rule-Based Vulnerability Matcher]
    end

    subgraph NetBotEngine["NetBot MCP Framework (netbot/)"]
        MCP[MCP Orchestrator]
        Intent[Intent Agent]
        Agents[Risk / Remediation / Troubleshoot / Scan / PDF Agents]
    end

    subgraph Intelligence["AI Engine & Persistence (ai_engine.py)"]
        Cache[(Supabase SHA-256 Cache)]
        Groq[Groq LPU]
        OpenAI[OpenAI GPT-4o-mini]
        Gemini[Google Gemini 2.5]
    end

    UI --> Auth
    UI --> Backend
    Chat --> NetBotEngine
    Backend --> ScanningEngine
    ScanningEngine --> Nmap
    ScanningEngine --> NVD
    ScanningEngine --> Rules
    NetBotEngine --> MCP
    MCP --> Intent --> Agents
    Agents --> Intelligence
    Backend --> Intelligence
    Intelligence --> Cache
    Intelligence --> Groq --> OpenAI --> Gemini
    Backend --> Reporter
    Backend --> Logs
```

---

## 📁 Repository Structure

```text
NetScan-Finals/
├── app.py                      # Core Flask application, routing, auth, & API endpoints
├── scanner.py                  # Nmap network scanner & scan profile orchestrator
├── ai_engine.py                # Multi-tier LLM fallback engine (Groq, OpenAI, Gemini)
├── ai_cache_supabase.py        # Supabase caching adapter for AI scan summaries
├── ai_hash.py                  # Deterministic SHA-256 fingerprinting for scan payloads
├── nvd_api.py                  # NIST NVD API v2.0 integration & rate-limited client
├── rules.py                    # Static vulnerability definitions & remediation database
├── report_generator.py         # Automated PDF audit report generation (fpdf2)
├── emailer.py                  # SMTP email notification module
├── requirements.txt            # Python dependencies
├── netbot/                     # NetBot MCP multi-agent subsystem
│   ├── server.py               # NetBot Blueprint & session handling
│   ├── mcp_orchestrator.py     # Model Context Protocol dispatcher
│   ├── cache.py                # In-memory and persisted query cache
│   └── agents/                 # Specialized sub-agents
│       ├── intent_agent.py     # User intent classifier
│       ├── scan_agent.py       # Scan trigger and status inspection agent
│       ├── risk_agent.py       # Risk prioritization agent
│       ├── remediation_agent.py# Actionable fix and patch generator
│       ├── troubleshoot_agent.py# Network troubleshooting agent
│       └── pdf_agent.py        # PDF document extraction and query agent
├── static/                     # Frontend assets (CSS, JavaScript, Icons)
├── templates/                  # Jinja2 HTML templates (Dashboard, Login, Register)
└── outputs/                    # Generated PDF audit reports
```

---

## ⚙️ Prerequisites

1. **Python 3.10+** installed on your system.
2. **Nmap** installed and accessible in your system's `PATH`:
   - **Linux (Debian/Ubuntu)**: `sudo apt update && sudo apt install nmap`
   - **macOS**: `brew install nmap`
   - **Windows**: Download and install from [nmap.org](https://nmap.org/download.html) and ensure the installation directory is added to system environment variables.
3. **API Keys** for AI providers and Supabase (configured in `.env`).

---

## 🚀 Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/sarveshvarode092704/NetScan-Finals.git
cd NetScan-Finals
```

### 2. Create and Activate a Virtual Environment
- **Linux/macOS**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
- **Windows (PowerShell)**:
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory (see [Environment Configuration](#-environment-configuration)).

### 5. Run the Application
```bash
python app.py
```
The server will start at `http://localhost:5000`.

---

## 🔧 Environment Configuration

Create a `.env` file in the root project directory with the following configuration:

```env
# Flask Settings
FLASK_DEBUG=1
SECRET_KEY=your_flask_secret_key

# Supabase Credentials (Auth & AI Fingerprint Caching)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key

# LLM Providers (Multi-tier Fallback Cascade)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
GROQ_FALLBACK_MODEL=openai/gpt-oss-20b

OPENAI_KEY=your_openai_api_key
GEMINI_KEY=your_gemini_api_key

# NIST National Vulnerability Database
NVD_API_KEY=your_nvd_api_key

# SMTP Email Dispatch (Optional - for admin reports)
MAIL_USER=your_email@gmail.com
MAIL_PASS=your_app_password
MAIL_TO=admin_recipient@gmail.com
```

---

## 🔌 API Reference

| Endpoint | Method | Role | Description |
|---|---|---|---|
| `/scan` | `POST` | Admin | Initiates a network scan with subnet, profile, and OS detection settings. |
| `/status/<job_id>` | `GET` | All | Retrieves real-time status, logs, progress, and AI summary of a scan job. |
| `/cancel/<job_id>` | `POST` | All | Cancels an ongoing scan and compiles partial results. |
| `/scan-history` | `GET` | Authenticated | Lists all previous scan executions with summaries. |
| `/scan-diff/<job_id>` | `GET` | Authenticated | Compares current scan against the previous scan of the same subnet. |
| `/schedule-scan` | `POST` | Admin | Schedules a scan to trigger automatically after a specified delay. |
| `/scheduled-scans` | `GET` | Authenticated | Lists all scheduled and pending scan tasks. |
| `/cancel-schedule/<id>` | `POST` | Admin | Cancels a pending scheduled scan job. |
| `/scan-profiles` | `GET` | Public | Returns available scan profiles (`quick`, `standard`, `deep`). |
| `/netbot/chat` | `POST` | All | Interacts with the NetBot multi-agent conversational engine. |
| `/netbot/upload` | `POST` | All | Uploads a PDF audit report for contextual Q&A. |
| `/outputs/<filename>` | `GET` | Authenticated | Downloads generated PDF audit reports. |
| `/health` | `GET` | Public | Returns service health status and API connectivity checks. |

---

## 🔒 Security & Responsible Use

> [!WARNING]
> **Authorized Use Only**: Port scanning and vulnerability probing without explicit permission from network owners may violate local and international cyber laws. Ensure you only scan networks and subnets you own or are explicitly authorized to assess.

---

## 📄 License

This project is licensed under the MIT License — see the repository for full details.
