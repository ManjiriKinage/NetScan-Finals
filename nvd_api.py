import requests

API_KEY = "d28d1ffe-ebf0-4523-b3a0-9b7969c6d719"

def fetch_cve(service, version):
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    headers = {"apiKey": API_KEY}
    params = {
        "keywordSearch": f"{service} {version}",
        "resultsPerPage": 2
    }

    try:
        r = requests.get(url, headers=headers, params=params)
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

        return results
    except:
        return []