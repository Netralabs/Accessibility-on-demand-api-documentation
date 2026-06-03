"""
6_check_report.py (sync)  —  STEP 6: Get the score report
=========================================================
Loops through every report saved by Step 5 and checks its status.
  - Reports already "Completed" are skipped.
  - When a report is Completed, the full "details" block is saved.
  - Failed reports (or unreadable responses) are logged to errors.json, not data.json.

EDIT NOTHING HERE. Your api_key lives in  ../config.json

How to run:  python 6_check_report.py

Note: the download_url expires after a short time (expires_in_seconds).
Download the score report PDF soon, or re-run this file.
"""

import requests
from helper import BASE_URL, api_key, build_headers, get_value, save_value, log_job_error

FINISHED = {"completed"}


def read_report(body):
    if body.get("success") is False:
        return "Failed", None, body.get("error") or {}
    data = body.get("data") or {}
    return data.get("status"), data.get("details"), None


key = api_key()
report_process = get_value("report_process", [])

if not report_process:
    print("[X] No reports found. Run 5_create_report.py first.")
    raise SystemExit

headers = build_headers(key)
changed = False

print(f"Checking {len(report_process)} report(s)...\n")

for entry in report_process:
    job_id = entry.get("job_id")
    current = str(entry.get("status", "")).lower()

    if current in FINISHED:
        print(f"   - {job_id}: already {entry.get('status')} (skipped)")
        continue

    response = requests.get(f"{BASE_URL}/report/{job_id}", headers=headers)

    try:
        status, details, error = read_report(response.json())
    except ValueError:
        print(f"   - {job_id}: could not check (status code {response.status_code})")
        log_job_error(job_id, response.status_code, "Could not read/parse report response", None)
        continue

    status = status or "unknown"
    print(f"   - {job_id}: {status}")

    if status != entry.get("status"):
        entry["status"] = status
        changed = True

    if str(status).lower() == "completed" and details:
        entry["details"] = details
        changed = True
        print(f"     download_url: {details.get('download_url')}")
        print(f"     expires_in_seconds: {details.get('expires_in_seconds')}")

    if error:
        # Failed reports are not kept in data.json — they go to errors.json (job_errors).
        code = error.get("code", "")
        detail = error.get("detail", "")
        print(f"     error: {code} - {detail}")
        log_job_error(job_id, response.status_code, f"{code} {detail}".strip(), error)

if changed:
    save_value("report_process", report_process)

done = [r for r in report_process if str(r.get("status", "")).lower() in FINISHED]
pending = [r for r in report_process if str(r.get("status", "")).lower() not in FINISHED]

print("\nSummary:")
print(f"   finished: {len(done)}  |  still generating: {len(pending)}")

if pending:
    print("Some reports are still generating. Wait a moment and run this file again.")
else:
    print("[OK] All reports finished. Download your score report PDF(s) using the URL(s) above.")
