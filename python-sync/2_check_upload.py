"""
2_check_upload.py (sync)  —  STEP 2: Check upload status
========================================================
Checks every file saved by Step 1 and updates its status.
Status will be 'uploading' or 'uploaded'.

EDIT NOTHING HERE. Your api_key lives in  ../config.json

How to run:  python 2_check_upload.py
"""

import requests
from helper import BASE_URL, api_key, build_headers, get_value, save_value, log_file_error


def read_status(body):
    if isinstance(body, dict) and "status" in body:
        return body["status"]
    data = body.get("data") if isinstance(body, dict) else None
    if isinstance(data, dict) and "uploading_status" in data:
        return data["uploading_status"]
    return None


key = api_key()
file_uploads = get_value("file_uploads", [])

if not file_uploads:
    print("[X] No files found. Run 1_upload.py first.")
    raise SystemExit

headers = build_headers(key)
changed = False

print(f"Checking {len(file_uploads)} file(s)...\n")

for entry in file_uploads:
    file_id = entry.get("file_id")
    current = entry.get("status", "")

    if str(current).lower() == "uploaded":
        print(f"   - {file_id}: already uploaded (skipped)")
        continue

    response = requests.get(f"{BASE_URL}/files/status/{file_id}", headers=headers)

    if response.status_code != 200:
        print(f"   - {file_id}: could not check (status code {response.status_code})")
        log_file_error(file_id, response.status_code, "Could not check upload status", None)
        continue

    try:
        new_status = read_status(response.json()) or "unknown"
    except ValueError:
        print(f"   - {file_id}: could not read response")
        log_file_error(file_id, response.status_code, "Could not read/parse response body", None)
        continue

    print(f"   - {file_id}: {new_status}")

    if str(new_status).lower() == "uploaded":
        entry["status"] = "uploaded"
        changed = True

if changed:
    save_value("file_uploads", file_uploads)

uploaded = [e["file_id"] for e in file_uploads if str(e.get("status", "")).lower() == "uploaded"]
pending = [e["file_id"] for e in file_uploads if str(e.get("status", "")).lower() != "uploaded"]

print("\nSummary:")
print(f"   uploaded: {len(uploaded)}  |  still uploading: {len(pending)}")

if pending:
    print("Some files are still uploading. Wait a moment and run this file again.")
else:
    print('[OK] All files uploaded. Next: put an uploaded file_id into config.json '
          '("process": {"file_id": ...}) and run  python 3_create_job.py')
