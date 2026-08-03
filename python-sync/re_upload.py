"""
re_upload.py (sync)  —  Retry files whose upload Failed
=======================================================
When Step 2 (2_check_upload.py) shows a file's status as "failed" and
"can_reupload" is true, this script retries the upload for those files by
calling  POST /files/re-upload/{file_id}  for each of them.

It reads the files saved in data.json, picks the ones that failed and can be
re-uploaded, and re-uploads each one. Re-uploading restarts the background
transfer (the status goes back to "Uploading"), so afterwards run
2_check_upload.py again to see whether it finished.

A file whose status is failed with "can_reupload": false can't be recovered —
upload a fresh copy with 1_upload.py instead.

EDIT NOTHING HERE. Your api_key lives in  ../config.json

How to run:  python re_upload.py
"""

import requests
from helper import (
    BASE_URL, api_key, build_headers_auth_only, get_value, save_value, log_file_error,
)


def read_data(body):
    """The re-upload response wraps the file info in 'data' — return it (or {})."""
    if isinstance(body, dict):
        data = body.get("data")
        if isinstance(data, dict):
            return data
    return {}


key = api_key()
file_uploads = get_value("file_uploads", [])

if not file_uploads:
    print("[X] No files found. Run 1_upload.py first.")
    raise SystemExit

# Split the failed files into 'can retry' vs 'cannot retry'.
retryable, blocked = [], []
for entry in file_uploads:
    if str(entry.get("status", "")).lower() == "failed":
        (retryable if entry.get("can_reupload") else blocked).append(entry)

if not retryable:
    if blocked:
        print("[!] Some files failed but cannot be re-uploaded (can_reupload = false):")
        for e in blocked:
            print(f"   - {e.get('file_id')}: {e.get('uploading_error') or 'upload failed'}")
        print("    These can't be recovered — upload a fresh copy with  python 1_upload.py")
    else:
        print("[OK] No failed files to re-upload.")
        print("    (Run  python 2_check_upload.py  first — it marks a file 'failed' if its upload fails.)")
    raise SystemExit

headers = build_headers_auth_only(key)
print(f"Re-uploading {len(retryable)} failed file(s)...\n")

changed = False
started = 0

for entry in retryable:
    file_id = entry.get("file_id")

    response = requests.post(f"{BASE_URL}/files/re-upload/{file_id}", headers=headers)

    if response.status_code != 200:
        print(f"   - {file_id}: re-upload failed (status code {response.status_code})")
        try:
            raw = response.json()
        except ValueError:
            raw = None
        log_file_error(file_id, response.status_code, "Re-upload request failed", raw)
        continue

    try:
        body = response.json()
    except ValueError:
        print(f"   - {file_id}: could not read response")
        log_file_error(file_id, response.status_code, "Could not read/parse re-upload response", None)
        continue

    new_status = read_data(body).get("uploading_status") or "Uploading"
    # A successful re-upload restarts the background transfer. Reset our tracked
    # status so Step 2 will check it again, and clear the old failure info.
    entry["status"] = str(new_status)
    entry.pop("uploading_error", None)
    entry.pop("can_reupload", None)
    print(f"   - {file_id}: re-upload started (status: {new_status})")
    started += 1
    changed = True

if changed:
    save_value("file_uploads", file_uploads)

line = f"   re-upload started: {started}  |  couldn't start: {len(retryable) - started}"
if blocked:
    line += f"  |  not re-uploadable: {len(blocked)}"
print("\nSummary:")
print(line)
if started:
    print("\nNext: run  python 2_check_upload.py  again to see whether they finished uploading.")
