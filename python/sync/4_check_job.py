"""
4_check_job.py (sync)  —  STEP 4: Check the job & get the tagged PDF
===================================================================
Loops through every job saved by Step 3 and checks its status.
  - Jobs already "Completed" are skipped.
  - When a job is Completed, the full "details" block is saved on that job.
  - Failed jobs (or unreadable responses) are logged to errors.json, not data.json.

EDIT NOTHING HERE. Your api_key lives in  ../config.json

How to run:  python 4_check_job.py

Note: the download_url expires after a short time (expires_in_seconds, e.g.
300s = 5 minutes). Download the tagged PDF soon, or re-run this file.
"""

import requests
from helper import BASE_URL, api_key, build_headers, get_value, save_value, log_job_error

FINISHED = {"completed"}


def read_job(body):
    if body.get("success") is False:
        return "Failed", None, body.get("error") or {}
    data = body.get("data") or {}
    return data.get("status"), data.get("details"), None


key = api_key()
job_process = get_value("job_process", [])

if not job_process:
    print("[X] No jobs found. Run 3_create_job.py first.")
    raise SystemExit

headers = build_headers(key)
changed = False

print(f"Checking {len(job_process)} job(s)...\n")

for entry in job_process:
    job_id = entry.get("job_id")
    current = str(entry.get("status", "")).lower()

    if current in FINISHED:
        print(f"   - {job_id}: already {entry.get('status')} (skipped)")
        continue

    response = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)

    try:
        status, details, error = read_job(response.json())
    except ValueError:
        print(f"   - {job_id}: could not check (status code {response.status_code})")
        log_job_error(job_id, response.status_code, "Could not read/parse job response", None)
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
        # Failed jobs are not kept in data.json — they go to errors.json (job_errors).
        code = error.get("code", "")
        detail = error.get("detail", "")
        print(f"     error: {code} - {detail}")
        log_job_error(job_id, response.status_code, f"{code} {detail}".strip(), error)

if changed:
    save_value("job_process", job_process)

done = [j for j in job_process if str(j.get("status", "")).lower() in FINISHED]
pending = [j for j in job_process if str(j.get("status", "")).lower() not in FINISHED]

print("\nSummary:")
print(f"   finished: {len(done)}  |  still processing: {len(pending)}")

if pending:
    print("Some jobs are still processing. Wait a moment and run this file again.")
else:
    print('[OK] All jobs finished. To get a score report, put a file_id into config.json '
          '("report": {"file_id": ...}) and run  python 5_create_report.py')
