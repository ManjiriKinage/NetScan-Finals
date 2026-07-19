import threading
import time

# Import your existing scanner logic
from scanner import scan_network


class ScanAgent:

    def __init__(self):
        self.jobs = {}   # job_id -> status


    def start_scan(self, target):

        job_id = str(int(time.time() * 1000))

        self.jobs[job_id] = {
            "status": "running",
            "progress": 0,
            "result": [],
            "cancel": False
        }

        t = threading.Thread(
            target=self._run_scan,
            args=(job_id, target),
            daemon=True
        )

        t.start()

        return {
            "job_id": job_id,
            "message": "Scan started"
        }


    def _run_scan(self, job_id, target):
        try:
            def callback(event_type, payload):
                if self.jobs[job_id]["cancel"]:
                    return
                if event_type == 'progress':
                    self.jobs[job_id]["progress"] = payload
                elif event_type == 'device':
                    self.jobs[job_id]["result"].append(payload)

            scan_network(target, progress_callback=callback)

            if self.jobs[job_id]["cancel"]:
                self.jobs[job_id]["status"] = "cancelled"
            else:
                self.jobs[job_id]["status"] = "completed"

        except Exception as e:
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = str(e)


    def cancel_scan(self, job_id):

        if job_id in self.jobs:
            self.jobs[job_id]["cancel"] = True
            return {"status": "cancelled"}

        return {"error": "Invalid job id"}


    def get_status(self, job_id):

        job = self.jobs.get(job_id)

        if not job:
            return {"error": "Job not found"}

        return {
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "result": job["result"]
        }