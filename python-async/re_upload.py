"""
re_upload.py (async)  —  Retry files whose upload Failed
========================================================
When Step 2 (2_check_upload.py) shows a file's status as "Failed" and
"can_reupload" is true, this script retries the upload for those files by
calling  POST /files/re-upload/{file_id}  for each of them.

It reads the files saved in data.json, picks the ones that failed and can be
re-uploaded, and re-uploads each one concurrently. Re-uploading restarts the
background transfer (the status goes back to "Uploading"), so afterwards run
2_check_upload.py again to see whether it finished.

A file whose status is Failed with "can_reupload": false can't be recovered —
upload a fresh copy with 1_upload.py instead.

EDIT NOTHING HERE. Your api_key lives in  ../config.json

How to run:  python re_upload.py
"""

import asyncio
import httpx
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


async def reupload_one(client, entry, headers):
    """Re-upload one file. Returns True if we changed the entry (worth saving)."""
    file_id = entry.get("file_id")
    try:
        resp = await client.post(f"{BASE_URL}/files/re-upload/{file_id}", headers=headers)
    except httpx.HTTPError as e:
        print(f"   - {file_id}: request error ({e})")
        log_file_error(file_id, 0, f"Re-upload request error: {e}", None)
        return False

    if resp.status_code != 200:
        print(f"   - {file_id}: re-upload failed (status code {resp.status_code})")
        try:
            raw = resp.json()
        except ValueError:
            raw = None
        log_file_error(file_id, resp.status_code, "Re-upload request failed", raw)
        return False

    try:
        body = resp.json()
    except ValueError:
        print(f"   - {file_id}: could not read response")
        log_file_error(file_id, resp.status_code, "Could not read/parse re-upload response", None)
        return False

    new_status = read_data(body).get("uploading_status") or "Uploading"
    # A successful re-upload restarts the background transfer. Reset our tracked
    # status so Step 2 will check it again, and clear the old failure info.
    entry["status"] = str(new_status)
    entry.pop("uploading_error", None)
    entry.pop("can_reupload", None)
    print(f"   - {file_id}: re-upload started (status: {new_status})")
    return True


async def main():
    key = api_key()
    file_uploads = get_value("file_uploads", [])

    if not file_uploads:
        print("[X] No files found. Run 1_upload.py first.")
        return

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
        return

    headers = build_headers_auth_only(key)
    print(f"Re-uploading {len(retryable)} failed file(s) concurrently...\n")

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[reupload_one(client, e, headers) for e in retryable]
        )

    if any(results):
        save_value("file_uploads", file_uploads)

    started = sum(1 for r in results if r)
    line = f"   re-upload started: {started}  |  couldn't start: {len(results) - started}"
    if blocked:
        line += f"  |  not re-uploadable: {len(blocked)}"
    print("\nSummary:")
    print(line)
    if started:
        print("\nNext: run  python 2_check_upload.py  again to see whether they finished uploading.")


if __name__ == "__main__":
    asyncio.run(main())
