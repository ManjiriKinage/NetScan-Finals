# app.py
import os
import uuid
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory, current_app
from dotenv import load_dotenv
load_dotenv() 
from netbot.server import netbot_bp
from report_generator import generate_pdf
from scanner import scan_network, SCAN_PROFILES
 # updated scanner that supports progress_callback
from ai_engine import summarize_report
from emailer import send_report

from supabase import create_client
from flask import session, redirect, url_for

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = Flask(__name__, static_folder="static", template_folder="templates")
app.register_blueprint(netbot_bp)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Simple in-memory job store for local/dev use
jobs = {}

# Scan history: stores completed scans keyed by subnet for diff feature
scan_history = {}

# Scheduled scans store
scheduled_scans = {}

@app.route("/")
def index():
    if not session.get("role"):
        return redirect("/login")
    return render_template("index.html")

def run_scan_job(job_id, subnet, role, profile="standard", os_detect=False):
    # YAHI SE CONTEXT DENA HAI
    with app.app_context():
        try:
            def progress_callback(event_type, payload):
                job = jobs.get(job_id)
                if not job:
                    return
                if event_type == 'log':
                    job['logs'].append(payload)
                elif event_type == 'progress':
                    job['progress'] = int(payload)
                elif event_type == 'device':
                    job['results'].append(payload)

            # run scanner (this will call progress_callback)
            report = []
            was_cancelled = False

            for item in scan_network(subnet, progress_callback=progress_callback, profile=profile, os_detect=os_detect):

                # Check cancel flag
                if jobs[job_id].get("cancel"):
                    jobs[job_id]["logs"].append("Scan cancelled by user. Generating partial report...")
                    was_cancelled = True
                    break

                report.append(item)

            # Generate AI summary (works for both full and partial reports)
            if report and len(report) > 0:
                jobs[job_id]["logs"].append(f"Generating AI summary for {len(report)} device(s)...")
                ai_summary = summarize_report(report)
            else:
                ai_summary = "No devices were scanned. AI summary unavailable."
            jobs[job_id]["ai_summary"] = ai_summary

            # Generate PDF (works for both full and partial reports)
            pdf_path = None
            if report and len(report) > 0:
                pdf_path = generate_pdf(report, output_dir=OUTPUT_DIR)
                filename = os.path.basename(pdf_path)
                jobs[job_id]["pdf"] = f"/outputs/{filename}"
            else:
                jobs[job_id]["pdf"] = None
                
            if role == "admin" and pdf_path and not was_cancelled:
                sender = os.getenv("MAIL_USER")
                password = os.getenv("MAIL_PASS")
                receiver = os.getenv("MAIL_TO")

                if sender and password and receiver:
                    try:
                        send_report(sender, password, receiver, pdf_path)
                        jobs[job_id]['logs'].append("Report emailed successfully.")
                    except Exception as e:
                        jobs[job_id]['logs'].append(f"Email failed: {str(e)}")
            # Calculate overall risk
            critical = sum(1 for d in report if d.get("risk") == "Critical")

            jobs[job_id]['summary'] = {
                "critical_devices": critical,
                "total_devices": len(report)
            }

            jobs[job_id]['results'] = report
            jobs[job_id]['progress'] = 100

            if was_cancelled:
                jobs[job_id]['status'] = 'cancelled'
                jobs[job_id]['logs'].append(f"Partial report ready ({len(report)} devices scanned).")
            else:
                jobs[job_id]['status'] = 'done'
                jobs[job_id]['logs'].append("Scan finished successfully.")

            # Save to scan history for diff feature
            scan_history[subnet] = scan_history.get(subnet, [])
            scan_history[subnet].append({
                "job_id": job_id,
                "timestamp": time.time(),
                "results": report,
                "profile": profile,
                "pdf": jobs[job_id].get("pdf")
            })

        except Exception as e:
            app.logger.exception("Scan job failed")
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = str(e)
            jobs[job_id]['logs'].append(f"Error: {str(e)}")


@app.route("/scan", methods=["POST"])
def start_scan():
    role = session.get("role")

    if role != "admin":
        return jsonify({"error": "Unauthorized. Only admins can start scans."}), 403
    data = request.get_json(silent=True) or {}
    subnet = data.get("subnet")
    if not subnet:
        return jsonify({"error": "subnet required"}), 400

    profile = data.get("profile", "standard")
    os_detect = data.get("os_detect", False)

    # Validate profile
    if profile not in SCAN_PROFILES:
        profile = "standard"

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'running',
        'progress': 0,
        'logs': [f"Job {job_id} queued. Profile: {SCAN_PROFILES[profile]['label']}"],
        'results': [],
        'pdf': None,
        'error': None,
        'started_at': time.time(),
        "cancel": False,
        "subnet": subnet,
        "profile": profile
    }

    # start background thread
    role = session.get("role")
    thread = threading.Thread(target=run_scan_job, args=(job_id, subnet, role, profile, os_detect), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id}), 202

@app.route("/status/<job_id>", methods=["GET"])
def job_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "job_not_found"}), 404
    return jsonify({
        'status': job['status'],
        'progress': job['progress'],
        'logs': job['logs'],
        'results': job['results'],
        'pdf': job['pdf'],
        'summary': job.get('summary'),
        'ai_summary': job.get('ai_summary'),
        'error': job['error']
    })

@app.route("/cancel/<job_id>", methods=["POST"])
def cancel_job(job_id):

    job = jobs.get(job_id)

    if not job:
        return jsonify({"error": "not found"}), 404

    job["cancel"] = True
    # Don't set status here — let the background thread finish generating
    # the partial AI summary + PDF, then it will set status to 'cancelled'

    return jsonify({"status": "cancelled"})

@app.route("/outputs/<path:filename>")
def download_report(filename):
    if not session.get("role"):
        return jsonify({"error": "Unauthorized"}), 401
    from werkzeug.utils import secure_filename
    filename = secure_filename(filename)
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


# ──────────────────────────────────────────────
# Scan History API (item 2.1)
# ──────────────────────────────────────────────

@app.route("/scan-history", methods=["GET"])
def get_scan_history():
    """Return all completed/cancelled jobs as a list."""
    if not session.get("role"):
        return jsonify({"error": "Unauthorized"}), 401

    history = []
    for jid, job in jobs.items():
        if job["status"] in ("done", "cancelled", "error"):
            history.append({
                "job_id": jid,
                "status": job["status"],
                "subnet": job.get("subnet", "unknown"),
                "profile": job.get("profile", "standard"),
                "started_at": job.get("started_at"),
                "total_devices": job.get("summary", {}).get("total_devices", 0) if job.get("summary") else 0,
                "critical_devices": job.get("summary", {}).get("critical_devices", 0) if job.get("summary") else 0,
                "pdf": job.get("pdf")
            })

    # Sort by start time descending
    history.sort(key=lambda x: x.get("started_at", 0), reverse=True)
    return jsonify(history)


# ──────────────────────────────────────────────
# Scan Diff API (item 3.3)
# ──────────────────────────────────────────────

@app.route("/scan-diff/<job_id>", methods=["GET"])
def scan_diff(job_id):
    """Compare a scan against the previous scan of the same subnet."""
    if not session.get("role"):
        return jsonify({"error": "Unauthorized"}), 401

    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    subnet = job.get("subnet", "")
    history = scan_history.get(subnet, [])

    if len(history) < 2:
        return jsonify({"error": "No previous scan to compare against", "diff": None}), 200

    # Find the current and previous scan
    current = None
    previous = None
    for i, entry in enumerate(history):
        if entry["job_id"] == job_id:
            current = entry
            if i > 0:
                previous = history[i - 1]
            break

    if not current or not previous:
        return jsonify({"error": "Could not find comparison scan", "diff": None}), 200

    # Build diff
    current_vulns = set()
    previous_vulns = set()

    for dev in current.get("results", []):
        for v in dev.get("vulnerabilities", []):
            current_vulns.add(f"{dev['host']}: {v}")

    for dev in previous.get("results", []):
        for v in dev.get("vulnerabilities", []):
            previous_vulns.add(f"{dev['host']}: {v}")

    new_vulns = list(current_vulns - previous_vulns)
    resolved_vulns = list(previous_vulns - current_vulns)
    unchanged = list(current_vulns & previous_vulns)

    return jsonify({
        "diff": {
            "new": new_vulns,
            "resolved": resolved_vulns,
            "unchanged_count": len(unchanged),
            "previous_job": previous["job_id"],
            "previous_timestamp": previous["timestamp"]
        }
    })


# ──────────────────────────────────────────────
# Scheduled Scans API (item 3.1)
# ──────────────────────────────────────────────

@app.route("/schedule-scan", methods=["POST"])
def schedule_scan():
    """Schedule a scan to run after a delay."""
    role = session.get("role")
    if role != "admin":
        return jsonify({"error": "Unauthorized. Only admins can schedule scans."}), 403

    data = request.get_json(silent=True) or {}
    subnet = data.get("subnet")
    delay_minutes = data.get("delay_minutes", 5)
    profile = data.get("profile", "standard")

    if not subnet:
        return jsonify({"error": "subnet required"}), 400

    schedule_id = str(uuid.uuid4())[:8]
    run_at = time.time() + (delay_minutes * 60)

    def scheduled_run():
        with app.app_context():
            job_id = str(uuid.uuid4())
            jobs[job_id] = {
                'status': 'running',
                'progress': 0,
                'logs': [f"Scheduled job {job_id} started (scheduled {delay_minutes}m ago). Profile: {SCAN_PROFILES.get(profile, SCAN_PROFILES['standard'])['label']}"],
                'results': [],
                'pdf': None,
                'error': None,
                'started_at': time.time(),
                "cancel": False,
                "subnet": subnet,
                "profile": profile
            }
            scheduled_scans[schedule_id]["job_id"] = job_id
            scheduled_scans[schedule_id]["status"] = "running"
            run_scan_job(job_id, subnet, "admin", profile=profile)

    timer = threading.Timer(delay_minutes * 60, scheduled_run)
    timer.daemon = True
    timer.start()

    scheduled_scans[schedule_id] = {
        "schedule_id": schedule_id,
        "subnet": subnet,
        "profile": profile,
        "delay_minutes": delay_minutes,
        "run_at": run_at,
        "status": "pending",
        "job_id": None,
        "timer": timer
    }

    return jsonify({
        "schedule_id": schedule_id,
        "subnet": subnet,
        "run_at": run_at,
        "delay_minutes": delay_minutes
    }), 202


@app.route("/scheduled-scans", methods=["GET"])
def list_scheduled_scans():
    """List all scheduled scans."""
    if not session.get("role"):
        return jsonify({"error": "Unauthorized"}), 401

    result = []
    for sid, sched in scheduled_scans.items():
        result.append({
            "schedule_id": sid,
            "subnet": sched["subnet"],
            "profile": sched["profile"],
            "delay_minutes": sched["delay_minutes"],
            "run_at": sched["run_at"],
            "status": sched["status"],
            "job_id": sched.get("job_id")
        })

    return jsonify(result)


@app.route("/cancel-schedule/<schedule_id>", methods=["POST"])
def cancel_scheduled_scan(schedule_id):
    """Cancel a pending scheduled scan."""
    sched = scheduled_scans.get(schedule_id)
    if not sched:
        return jsonify({"error": "Not found"}), 404

    if sched["status"] == "pending":
        sched["timer"].cancel()
        sched["status"] = "cancelled"

    return jsonify({"status": "cancelled"})


# ──────────────────────────────────────────────
# Scan Profiles API (item 3.2)
# ──────────────────────────────────────────────

@app.route("/scan-profiles", methods=["GET"])
def get_scan_profiles():
    """Return available scan profiles."""
    profiles = {}
    for key, val in SCAN_PROFILES.items():
        profiles[key] = val["label"]
    return jsonify(profiles)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "ai": bool(os.getenv("GEMINI_KEY")),
        "email": bool(os.getenv("MAIL_USER")),
        "nvd": bool(os.getenv("NVD_API_KEY"))
    })  
@app.route("/login")
def login_page():
    return render_template("login.html")
@app.route("/register")
def register_page():
    return render_template("register.html")

import re

def is_strong_password(password):
    """
    Password rules:
    - At least 8 characters
    - At least 1 uppercase
    - At least 1 lowercase
    - At least 1 digit
    - At least 1 special character
    """
    if len(password) < 8:
        return False

    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).+$'
    return re.match(pattern, password)

@app.route("/admin/register", methods=["POST"])
def admin_register():
    data = request.get_json()
    invite_code = data.get("invite_code")
    expected_code = os.getenv("ADMIN_INVITE_CODE", "default_secret_code")
    
    if invite_code != expected_code:
        return jsonify({"error": "Invalid invite code"}), 403
        
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")
    phone = data.get("phone")
     #  Password strength check
    if not is_strong_password(password):
        return jsonify({
            "error": "Password must be 8+ chars, include uppercase, lowercase, number and special character."
        }), 400
        
    res = supabase.auth.sign_up({
        "email": email,
        "password": password
    })

    if res.user:  
        session["name"] = name
        session["role"] = "admin" 
        return jsonify({"status": "registered"})

    return jsonify({"error": "Registration failed"}), 400
@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    res = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

    if res.user:
        session["user"] = email
        session["role"] = "admin"
        session["token"] = res.session.access_token
        
        session["name"] = email.split("@")[0]
        return jsonify({"status": "ok"})
       
        

    return jsonify({"error": "Invalid credentials"}), 401
@app.route("/guest")
def guest_mode():
    session["role"] = "guest"
    return redirect(url_for("index"))
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

UPLOAD_DIR = os.path.join(app.root_path, "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route("/netbot/upload", methods=["POST"])
def upload_netbot_pdf():

    if "file" not in request.files:
        return {"error": "No file"}, 400

    file = request.files["file"]

    if file.filename == "":
        return {"error": "Empty file"}, 400

    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)
    
    if not filename.endswith('.pdf'):
         return {"error": "Only PDF files are allowed"}, 400

    save_path = os.path.join(UPLOAD_DIR, filename)

    file.save(save_path)

    return {
        "path": f"/outputs/{filename}"
    }
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
