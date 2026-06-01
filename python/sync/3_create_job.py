"""
3_create_job.py  —  STEP 3: Start processing the PDF
====================================================
Sends an uploaded file for processing (tagging) and gets back a job_id.
You choose the processing LEVEL (1 or 2).

How to run:  python 3_create_job.py

What it saves to data.json:
  "job_process": [
      {"file_id": "....", "job_id": "....", "status": "queued"},
      ...
  ]
Step 4 reads this list, checks each job, and updates the status.
"""

import requests
from python.sync.helper import BASE_URL, build_headers, get_value, save_value, show_response

# ============================================================
# ===== EDIT HERE =====
# ============================================================
API_KEY = "aod-xxxxxxxxxxx"   # 👈 paste your key from Section 3


FILE_ID = ""

LEVEL = 1  # 👈 choose 1 or 2
# ============================================================
# ===== STOP EDITING (the rest runs by itself) =====
# ============================================================

if not FILE_ID:
    print("[X] No file_id given. Paste an uploaded FILE_ID above.")
    raise SystemExit

ENDPOINT = f"{BASE_URL}/jobs"

payload = {
    "file_id": FILE_ID,
    "level": LEVEL,
}

print(f"Starting a job for file_id {FILE_ID} at level {LEVEL} ...")
response = requests.post(ENDPOINT, headers=build_headers(API_KEY), json=payload)
show_response(response)
if response.status_code == 409:
    print("\n[Conflict] This is already processed: changed file id", FILE_ID)

if response.status_code in (200, 201):
    body = response.json()
    data = body.get("data") or {}
    job_id = data.get("job_id")

    if job_id:
        # Add this job to the saved job_process list.
        job_process = get_value("job_process", [])

        # Avoid duplicate entries for the same job_id.
        if not any(j.get("job_id") == job_id for j in job_process):
            job_process.append(
                {
                    "file_id": FILE_ID,
                    "job_id": job_id,
                    "status": "Queued",
                }
            )
            save_value("job_process", job_process)

        print("\n[OK] Got job_id:", job_id)
        print("Next: run  python 4_check_job.py")
    else:
        print(
            "\n[!] Could not find 'job_id' in the response. "
            "Check the printed response above and update the key name."
        )
else:
    print(
        "\n[X] Could not start the job. Check the file_id, level, and status code above."
    )
