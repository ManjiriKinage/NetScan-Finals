import requests
import os
import time
import threading

API_KEY = os.getenv("NVD_API_KEY")

# Rate limiting: max 5 requests per 30 seconds (NVD free tier)
_lock = threading.Lock()
_request_times = []
_MAX_REQUESTS = 5
_WINDOW_SECONDS = 30

# In-memory cache to avoid duplicate lookups
_cache = {}


def _rate_limit():
    """Block until we're within the rate limit window."""
    with _lock:
        now = time.time()
        # Remove timestamps outside the window
        while _request_times and _request_times[0] < now - _WINDOW_SECONDS:
            _request_times.pop(0)

        if len(_request_times) >= _MAX_REQUESTS:
            # Wait until the oldest request falls outside the window
            sleep_time = _WINDOW_SECONDS - (now - _request_times[0]) + 0.5
            if sleep_time > 0:
                time.sleep(sleep_time)

        _request_times.append(time.time())


def fetch_cve(service, version):
    cache_key = f"{service}:{version}".lower()

    # Check cache first
    if cache_key in _cache:
        return _cache[cache_key]

    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    headers = {"apiKey": API_KEY}
    params = {
        "keywordSearch": f"{service} {version}",
        "resultsPerPage": 2
    }

    try:
        # Apply rate limiting before making the request
        _rate_limit()

        r = requests.get(url, headers=headers, params=params, timeout=10)
        data = r.json()
        vulns = data.get("vulnerabilities", [])
        results = []

        for v in vulns:
            cve = v["cve"]
            cve_id = cve["id"]
            desc = cve["descriptions"][0]["value"]
            score = None

            metrics = cve.get("metrics", {})
            if "cvssMetricV31" in metrics:
                score = metrics["cvssMetricV31"][0]["cvssData"]["baseScore"]

            results.append({
                "cve_id": cve_id,
                "description": desc,
                "score": score
            })

        # Cache the result
        _cache[cache_key] = results
        return results
    except:
        return []