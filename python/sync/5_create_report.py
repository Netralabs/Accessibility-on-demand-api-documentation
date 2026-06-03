"""
5_create_report.py (sync)  —  STEP 5: Request an axes4 score report
===================================================================
Asks the API to generate an axes4 accessibility score report for a file.

EDIT NOTHING HERE. Set this in  ../config.json  under "report":
  "report": { "file_id": "<the file_id to generate a report for>" }

How to run:  python 5_create_report.py

What it saves to data.json:
  "report_process": [ {"file_id": "....", "job_id": "....", "status": "Processing"}, ... ]
"""

import requests
from helper import BASE_URL, load_config, api_key, build_headers, get_value, save_value, show_response, log_file_error

cfg = load_config()
key = api_key()
report = cfg.get("report") or {}
FILE_ID = str(report.get("file_id", "")).strip()

if not FILE_ID:
    print('[X] No file_id given. Set "report": {"file_id": ...} in config.json.')
    raise SystemExit

ENDPOINT = f"{BASE_URL}/report/"
payload = {"file_id": FILE_ID}

print(f"Requesting a score report for file_id {FILE_ID} ...")
response = requests.post(ENDPOINT, headers=build_headers(key), json=payload)
show_response(response)

if response.status_code in (200, 201):
    body = response.json()
    data = body.get("data") or {}
    job_id = data.get("job_id")

    if job_id:
        report_process = get_value("report_process", [])
        if not any(r.get("job_id") == job_id for r in report_process):
            report_process.append({"file_id": FILE_ID, "job_id": job_id, "status": "Processing"})
            save_value("report_process", report_process)
        print("\n[OK] Got report job_id:", job_id)
        print("Next: run  python 6_check_report.py")
    else:
        print("\n[!] Could not find 'job_id' in the response. "
              "Check the printed response above and update the key name.")
        log_file_error(FILE_ID, response.status_code, "No job_id in report-create response", body)
else:
    print("\n[X] Could not request the report. Check the file_id and status code above.")
    try:
        raw = response.json()
    except ValueError:
        raw = None
    log_file_error(FILE_ID, response.status_code, "Could not request report", raw)
