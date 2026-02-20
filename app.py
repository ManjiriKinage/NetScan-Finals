# app.py
import os
import uuid
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory, current_app
from report_generator import generate_pdf
from scanner import scan_network  # updated scanner that supports progress_callback

app = Flask(__name__, static_folder="static", template_folder="templates")
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Simple in-memory job store for local/dev use
jobs = {}

@app.route("/")
def index():
    return render_template("index.html")

def run_scan_job(job_id, subnet):
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
            report = scan_network(subnet, progress_callback=progress_callback)
            # generate pdf
            pdf_path = generate_pdf(report, output_dir=OUTPUT_DIR)

            # THREAD FIX: url_for mat use karo, direct path banao
            filename = os.path.basename(pdf_path)
            pdf_url = f"/outputs/{filename}"
            jobs[job_id]['pdf'] = pdf_url
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
        'started_at': time.time()
    }

    # start background thread
    thread = threading.Thread(target=run_scan_job, args=(job_id, subnet), daemon=True)
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
        'error': job['error']
    })

@app.route("/outputs/<path:filename>")
def download_report(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
