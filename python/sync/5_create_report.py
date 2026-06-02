"""
5_create_report.py  —  STEP 5: Request an axes4 score report
============================================================
Asks the API to generate an axes4 accessibility score report for a file.
Returns a report job_id.

How to run:  python 5_create_report.py

What it saves to data.json:
  "report_process": [
      {"file_id": "....", "job_id": "....", "status": "queued"},
      ...
  ]
Step 6 reads this list, checks each report, and updates the status.
"""

import requests
from helper import BASE_URL, API_KEY, build_headers, get_value, save_value, show_response

# ============================================================
# ===== EDIT HERE =====
# ============================================================

FILE_ID = ""  # the file_id to generate a report for
# ============================================================
# ===== STOP EDITING (the rest runs by itself) =====
# ============================================================

if not FILE_ID:
    print("[X] No file_id given. Paste a FILE_ID above.")
    raise SystemExit

ENDPOINT = f"{BASE_URL}/report"

payload = {
    "file_id": FILE_ID,
}

print(f"Requesting a score report for file_id {FILE_ID} ...")
response = requests.post(ENDPOINT, headers=build_headers(API_KEY), json=payload)
show_response(response)

if response.status_code in (200, 201):
    body = response.json()
    data = body.get("data") or {}
    job_id = data.get("job_id")

    if job_id:
        report_process = get_value("report_process", [])

        # Avoid duplicate entries for the same report job_id.
        if not any(r.get("job_id") == job_id for r in report_process):
            report_process.append(
                {
                    "file_id": FILE_ID,
                    "job_id": job_id,
                    "status": "Processing",
                }
            )
            save_value("report_process", report_process)

        print("\n[OK] Got report job_id:", job_id)
        print("Next: run  python 6_check_report.py")
    else:
        print(
            "\n[!] Could not find 'job_id' in the response. "
            "Check the printed response above and update the key name."
        )
else:
    print(
        "\n[X] Could not request the report. Check the file_id and status code above."
    )
