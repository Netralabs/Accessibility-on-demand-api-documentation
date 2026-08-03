"""
2_check_upload.py (sync)  —  STEP 2: Check upload status
========================================================
Checks every file saved by Step 1 and updates its status: "uploaded", still
"uploading", or "failed".

A file that comes back "failed" is recorded with its error and a "can_reupload"
flag. If can_reupload is true, retry it with  python re_upload.py  and run this
again; if false, the file can't be recovered — upload a fresh copy with
1_upload.py. Files already "uploaded" or "failed" are skipped on later runs.

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


def st(entry):
    return str(entry.get("status", "")).lower()


key = api_key()
file_uploads = get_value("file_uploads", [])

if not file_uploads:
    print("[X] No files found. Run 1_upload.py first.")
    raise SystemExit

headers = build_headers(key)
changed = False

# Only files that haven't settled yet need checking. Print why the rest are skipped.
pending_entries = []
for entry in file_uploads:
    status = st(entry)
    if status == "uploaded":
        print(f"   - {entry.get('file_id')}: already uploaded (skipped)")
    elif status == "failed":
        hint = "can re-upload" if entry.get("can_reupload") else "cannot re-upload"
        print(f"   - {entry.get('file_id')}: already failed ({hint}, skipped)")
    else:
        pending_entries.append(entry)

print(f"\nChecking {len(pending_entries)} file(s)...\n")

for entry in pending_entries:
    file_id = entry.get("file_id")

    response = requests.get(f"{BASE_URL}/files/status/{file_id}", headers=headers)

    if response.status_code != 200:
        print(f"   - {file_id}: could not check (status code {response.status_code})")
        log_file_error(file_id, response.status_code, "Could not check upload status", None)
        continue

    try:
        body = response.json()
    except ValueError:
        print(f"   - {file_id}: could not read response")
        log_file_error(file_id, response.status_code, "Could not read/parse response body", None)
        continue

    data = body.get("data") if isinstance(body, dict) else {}
    if not isinstance(data, dict):
        data = {}
    new_status = read_status(body) or "unknown"
    status_l = str(new_status).lower()

    if status_l == "uploaded":
        print(f"   - {file_id}: {new_status}")
        entry["status"] = "uploaded"
        entry.pop("uploading_error", None)
        entry.pop("can_reupload", None)
        changed = True

    elif status_l == "failed":
        # The background upload failed. Record why, and whether it can be retried,
        # so re_upload.py knows what to do.
        err = data.get("uploading_error") or "upload failed"
        can = bool(data.get("can_reupload"))
        entry["status"] = "failed"
        entry["uploading_error"] = err
        entry["can_reupload"] = can
        hint = "can re-upload" if can else "cannot re-upload"
        print(f"   - {file_id}: Failed — {err}  ({hint})")
        changed = True

    else:
        # Still uploading (or an unexpected status) — check again next run.
        print(f"   - {file_id}: {new_status}")

if changed:
    save_value("file_uploads", file_uploads)

uploaded = [e["file_id"] for e in file_uploads if st(e) == "uploaded"]
failed = [e for e in file_uploads if st(e) == "failed"]
pending = [e["file_id"] for e in file_uploads if st(e) not in ("uploaded", "failed")]

print("\nSummary:")
print(f"   uploaded: {len(uploaded)}  |  failed: {len(failed)}  |  still uploading: {len(pending)}")

if failed:
    print("\n[!] Some files failed to upload:")
    for e in failed:
        hint = "can re-upload" if e.get("can_reupload") else "cannot re-upload"
        print(f"   - {e.get('file_id')}: {e.get('uploading_error') or 'upload failed'}  ({hint})")
    retryable = [e for e in failed if e.get("can_reupload")]
    blocked = [e for e in failed if not e.get("can_reupload")]
    if retryable:
        print(f"    {len(retryable)} can be retried — run  python re_upload.py")
    if blocked:
        print(f"    {len(blocked)} cannot be re-uploaded — upload a fresh copy with  python 1_upload.py")

if pending:
    print("\nSome files are still uploading. Wait a moment and run this file again.")
elif not failed:
    print('\n[OK] All files uploaded. Next: put an uploaded file_id into config.json '
          '("process": {"file_id": ...}) and run  python 3_create_job.py')
