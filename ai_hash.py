import hashlib
import json

def make_scan_hash(report):

    payload = json.dumps(report, sort_keys=True)

    return hashlib.sha256(payload.encode()).hexdigest()