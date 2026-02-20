# app.py
import os
import uuid
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory, current_app
from report_generator import generate_pdf
from scanner import scan_network  # updated scanner that supports progress_callback
from ai_engine import summarize_report
from emailer import send_report

from dotenv import load_dotenv
load_dotenv()
from supabase import create_client
from flask import session, redirect, url_for

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Simple in-memory job store for local/dev use
jobs = {}

@app.route("/")
def index():
    if not session.get("role"):
        return redirect("/login")
    return render_template("index.html")

def run_scan_job(job_id, subnet,role):
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

            for item in scan_network(subnet, progress_callback=progress_callback):

                # Check cancel flag
                if jobs[job_id].get("cancel"):
                    jobs[job_id]["logs"].append("Scan cancelled by user.")
                    break

                report.append(item)
            # Generate AI summary
            ai_summary = summarize_report(report)
            jobs[job_id]["ai_summary"] = ai_summary
            # generate pdf
            pdf_path = generate_pdf(report, output_dir=OUTPUT_DIR)
            
            if role == "admin":
                sender = os.getenv("MAIL_USER")
                password = os.getenv("MAIL_PASS")
                receiver = os.getenv("MAIL_TO")

                if sender and password and receiver:
                    try:
                        send_report(sender, password, receiver, pdf_path)
                        jobs[job_id]['logs'].append("Report emailed successfully.")
                    except Exception as e:
                        jobs[job_id]['logs'].append(f"Email failed: {str(e)}")

            if sender and password and receiver:
                try:
                    send_report(sender, password, receiver, pdf_path)
                    jobs[job_id]['logs'].append("Report emailed successfully.")
                except Exception as e:
                    jobs[job_id]['logs'].append(f"Email failed: {str(e)}")

            # THREAD FIX: url_for mat use karo, direct path banao
            filename = os.path.basename(pdf_path)
            pdf_url = f"/outputs/{filename}"
            jobs[job_id]['pdf'] = pdf_url
            # Calculate overall risk
            critical = sum(1 for d in report if d.get("risk") == "Critical")

            jobs[job_id]['summary'] = {
                "critical_devices": critical,
                "total_devices": len(report)
            }

            jobs[job_id]['results'] = report
            jobs[job_id]['progress'] = 100
            jobs[job_id]['status'] = 'done'
            jobs[job_id]['logs'].append("Scan finished successfully.")
        except Exception as e:
            app.logger.exception("Scan job failed")
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = str(e)
            jobs[job_id]['logs'].append(f"Error: {str(e)}")


@app.route("/scan", methods=["POST"])
def start_scan():
    role = session.get("role")

    if not role:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    subnet = data.get("subnet")
    if not subnet:
        return jsonify({"error": "subnet required"}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'running',
        'progress': 0,
        'logs': [f"Job {job_id} queued."],
        'results': [],
        'pdf': None,
        'error': None,
        'started_at': time.time(),
        "cancel": False
    }

    # start background thread
    role = session.get("role")
    thread = threading.Thread(target=run_scan_job, args=(job_id, subnet, role), daemon=True)
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
    job["status"] = "cancelled"

    return jsonify({"status": "cancelled"})

@app.route("/outputs/<path:filename>")
def download_report(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

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
@app.route("/admin/register", methods=["POST"])
def admin_register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    res = supabase.auth.sign_up({
        "email": email,
        "password": password
    })

    if res.user:
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
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
