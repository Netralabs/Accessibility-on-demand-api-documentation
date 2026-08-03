"""
2_check_upload.py (async)  —  STEP 2: Check upload status
=========================================================
Checks ALL files saved by Step 1 at the same time (concurrently) and updates
each one's status: "uploaded", still "uploading", or "failed".

A file that comes back "failed" is recorded with its error and a "can_reupload"
flag. If can_reupload is true, retry it with  python re_upload.py  and run this
again; if false, the file can't be recovered — upload a fresh copy with
1_upload.py. Files already "uploaded" or "failed" are skipped on later runs.

EDIT NOTHING HERE. Your api_key lives in  ../config.json

How to run:  python 2_check_upload.py
"""

import asyncio
import httpx
from helper import BASE_URL, api_key, build_headers, get_value, save_value, log_file_error


def read_status(body):
    if isinstance(body, dict) and "status" in body:
        return body["status"]
    data = body.get("data") if isinstance(body, dict) else None
    if isinstance(data, dict) and "uploading_status" in data:
        return data["uploading_status"]
    return None


async def check_one(client, entry, headers):
    file_id = entry.get("file_id")
    try:
        resp = await client.get(f"{BASE_URL}/files/status/{file_id}", headers=headers)
    except httpx.HTTPError as e:
        print(f"   - {file_id}: request error ({e})")
        log_file_error(file_id, 0, f"Request error: {e}", None)
        return False

    if resp.status_code != 200:
        print(f"   - {file_id}: could not check (status code {resp.status_code})")
        log_file_error(file_id, resp.status_code, "Could not check upload status", None)
        return False

    try:
        body = resp.json()
    except ValueError:
        print(f"   - {file_id}: could not read response")
        log_file_error(file_id, resp.status_code, "Could not read/parse response body", None)
        return False

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
        return True

    if status_l == "failed":
        # The background upload failed. Record why, and whether it can be retried,
        # so re_upload.py knows what to do.
        err = data.get("uploading_error") or "upload failed"
        can = bool(data.get("can_reupload"))
        entry["status"] = "failed"
        entry["uploading_error"] = err
        entry["can_reupload"] = can
        hint = "can re-upload" if can else "cannot re-upload"
        print(f"   - {file_id}: Failed — {err}  ({hint})")
        return True

    # Still uploading (or an unexpected status) — check again next run.
    print(f"   - {file_id}: {new_status}")
    return False


async def main():
    key = api_key()
    file_uploads = get_value("file_uploads", [])

    if not file_uploads:
        print("[X] No files found. Run 1_upload.py first.")
        return

    headers = build_headers(key)

    pending_entries = []
    for entry in file_uploads:
        status = str(entry.get("status", "")).lower()
        if status == "uploaded":
            print(f"   - {entry.get('file_id')}: already uploaded (skipped)")
        elif status == "failed":
            hint = "can re-upload" if entry.get("can_reupload") else "cannot re-upload"
            print(f"   - {entry.get('file_id')}: already failed ({hint}, skipped)")
        else:
            pending_entries.append(entry)

    print(f"\nChecking {len(pending_entries)} file(s) concurrently...\n")

    changed = False
    if pending_entries:
        async with httpx.AsyncClient() as client:
            results = await asyncio.gather(
                *[check_one(client, e, headers) for e in pending_entries]
            )
        changed = any(results)

    if changed:
        save_value("file_uploads", file_uploads)

    def st(e):
        return str(e.get("status", "")).lower()

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


if __name__ == "__main__":
    asyncio.run(main())
