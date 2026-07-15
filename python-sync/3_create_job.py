"""
3_create_job.py (sync)  —  STEP 3: Start processing the PDF
===========================================================
Sends an uploaded file for processing (tagging) and gets back a job_id.

EDIT NOTHING HERE. Set these in  ../config.json  under "process":
  "process": {
    "file_id": "<an uploaded file_id>",
    "level": 1,                          # 1 or 2
    "requires_manual_review": false      # optional — see below
  }

Manual review (optional):
  Set "requires_manual_review": true if you'd like to review and refine the
  automated tagging in the web UI before the tagged PDF becomes downloadable.
  When enabled, Step 4 will report the job as "AwaitingManualReview" until you:
    1. Go to https://app.accessibilityondemand.ai/login (you'll also get an
       email when the file is ready to review).
    2. Open the batch, select the file, click Review.
    3. On the last page of the review, click the Complete button.
  After that, run Step 4 again and it will return the download_url.

How to run:  python 3_create_job.py

What it saves to data.json:
  "job_process": [ {"file_id": "....", "job_id": "....", "status": "Queued"}, ... ]
"""

import requests
from helper import BASE_URL, load_config, api_key, build_headers, get_value, save_value, show_response, log_file_error

cfg = load_config()
key = api_key()
process = cfg.get("process") or {}
FILE_ID = str(process.get("file_id", "")).strip()
LEVEL = process.get("level", 1)
if not isinstance(LEVEL, int):
    LEVEL = 1

# Optional flag. Only accept a real JSON boolean `true`; anything else
# (missing, false, "true" as a string, etc.) is treated as False so the
# default behaviour stays "fully automatic, downloadable right away".
REQUIRES_MANUAL_REVIEW = process.get("requires_manual_review") is True

if not FILE_ID:
    print('[X] No file_id given. Set "process": {"file_id": ...} in config.json '
          "(use an uploaded file_id from Step 2).")
    raise SystemExit

ENDPOINT = f"{BASE_URL}/jobs/"
payload = {
    "file_id": FILE_ID,
    "level": LEVEL,
    "requires_manual_review": REQUIRES_MANUAL_REVIEW,
}

review_note = "  (with manual review)" if REQUIRES_MANUAL_REVIEW else ""
print(f"Starting a job for file_id {FILE_ID} at level {LEVEL}{review_note} ...")
response = requests.post(ENDPOINT, headers=build_headers(key), json=payload)
show_response(response)

if response.status_code == 409:
    print("\n[Conflict] This is already processed: change the file_id in config.json", FILE_ID)
    try:
        raw = response.json()
    except ValueError:
        raw = None
    log_file_error(FILE_ID, 409, "Conflict - file already processed", raw)

if response.status_code in (200, 201):
    body = response.json()
    data = body.get("data") or {}
    job_id = data.get("job_id")

    if job_id:
        job_process = get_value("job_process", [])
        if not any(j.get("job_id") == job_id for j in job_process):
            entry = {"file_id": FILE_ID, "job_id": job_id, "status": "Queued"}
            # Keep a small marker on the entry so data.json makes it clear
            # this job was started with manual review enabled.
            if REQUIRES_MANUAL_REVIEW:
                entry["requires_manual_review"] = True
            job_process.append(entry)
            save_value("job_process", job_process)
        print("\n[OK] Got job_id:", job_id)
        if REQUIRES_MANUAL_REVIEW:
            print("     (manual review enabled — Step 4 will prompt you to review in the UI once tagging finishes)")
        print("Next: run  python 4_check_job.py")
    else:
        print("\n[!] Could not find 'job_id' in the response. "
              "Check the printed response above and update the key name.")
        log_file_error(FILE_ID, response.status_code, "No job_id in job-create response", body)
elif response.status_code != 409:
    print("\n[X] Could not start the job. Check the file_id, level, and status code above.")
    try:
        raw = response.json()
    except ValueError:
        raw = None
    log_file_error(FILE_ID, response.status_code, "Could not start job", raw)
