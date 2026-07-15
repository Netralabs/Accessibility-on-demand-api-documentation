"""
4_check_job.py (sync)  —  STEP 4: Check the job & get the tagged PDF
===================================================================
Loops through every job saved by Step 3 and checks its status.
  - Jobs already "Completed" are skipped.
  - When a job is Completed, the full "details" block is saved on that job.
  - Failed jobs (or unreadable responses) are logged to errors.json, not data.json.

Manual review case:
  If you started the job with requires_manual_review=true (Step 3), the job may
  come back with API status "Completed" BUT no download_url — the API is holding
  the link until you complete the manual review in the web UI. This script marks
  such jobs locally as "AwaitingManualReview" (not "Completed") so polling keeps
  going. To finish them:
    1. Go to https://app.accessibilityondemand.ai/login and log in
       (you'll also receive an email when the file is ready to review).
    2. Open the batch, select the file, click Review.
    3. On the last page of the review, click the Complete button.
    4. Run this file again — the download_url will now be included.

EDIT NOTHING HERE. Your api_key lives in  ../config.json

How to run:  python 4_check_job.py

Note: the download_url expires after a short time (expires_in_seconds, e.g.
300s = 5 minutes). Download the tagged PDF soon, or re-run this file.
"""

import requests
from helper import BASE_URL, api_key, build_headers, get_value, save_value, log_job_error

# Statuses that mean "no more polling needed". "AwaitingManualReview" is
# deliberately NOT in this set — we want to keep polling until the user finishes
# the review in the UI and the API starts returning a download_url.
FINISHED = {"completed"}


def read_job(body):
    if body.get("success") is False:
        return "Failed", None, body.get("error") or {}
    data = body.get("data") or {}
    return data.get("status"), data.get("details"), None


def is_manual_review_pending(api_status, details):
    """
    The API reports status="Completed" for two very different situations:
      1) Fully done  -> details has a download_url
      2) Waiting for manual review -> details has a "message" but NO download_url
    Detect case 2 so we can label it distinctly and keep polling.
    """
    return (
        str(api_status or "").lower() == "completed"
        and isinstance(details, dict)
        and not details.get("download_url")
        and bool(details.get("message"))
    )


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
        api_status, details, error = read_job(response.json())
    except ValueError:
        print(f"   - {job_id}: could not check (status code {response.status_code})")
        log_job_error(job_id, response.status_code, "Could not read/parse job response", None)
        continue

    api_status = api_status or "unknown"

    # Distinguish the "completed but manual review pending" case locally so it
    # doesn't get bucketed with the fully-done jobs.
    manual_review_pending = is_manual_review_pending(api_status, details)
    local_status = "AwaitingManualReview" if manual_review_pending else api_status

    print(f"   - {job_id}: {local_status}")

    if local_status != entry.get("status"):
        entry["status"] = local_status
        changed = True

    if manual_review_pending:
        # Show a friendly, actionable note so the user knows exactly what to do.
        # We do NOT save details here (there's no download_url yet).
        print(f"     note: {details.get('message')}")
        print( "     -> log in at https://app.accessibilityondemand.ai/login,")
        print( "        open the batch, select the file, click Review,")
        print( "        then click Complete on the last page.")
        print( "        After that, run this file again to get the download_url.")

    if str(local_status).lower() == "completed" and details:
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
awaiting = [j for j in job_process if str(j.get("status", "")).lower() == "awaitingmanualreview"]
still_processing = [
    j for j in job_process
    if str(j.get("status", "")).lower() not in FINISHED
    and str(j.get("status", "")).lower() != "awaitingmanualreview"
]

print("\nSummary:")
print(f"   finished: {len(done)}  |  awaiting manual review: {len(awaiting)}  |  still processing: {len(still_processing)}")

if awaiting:
    print("\nJobs ready for manual review:")
    for j in awaiting:
        print(f"   - job_id: {j.get('job_id')}  |  file_id: {j.get('file_id')}")
    print("   Log in at https://app.accessibilityondemand.ai/login, complete the review,")
    print("   then run  python 4_check_job.py  again to get the download link.")

if still_processing:
    print("\nSome jobs are still processing. Wait a moment and run this file again.")

if not awaiting and not still_processing:
    print('[OK] All jobs finished. To get a score report, put a file_id into config.json '
          '("report": {"file_id": ...}) and run  python 5_create_report.py')
