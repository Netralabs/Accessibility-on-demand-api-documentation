"""
2_check_upload.py (async)  —  STEP 2: Check upload status
=========================================================
Checks ALL files saved by Step 1 at the same time (concurrently).
Files already "uploaded" are skipped; the rest are updated.

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

    new_status = read_status(body) or "unknown"
    print(f"   - {file_id}: {new_status}")

    if str(new_status).lower() == "uploaded":
        entry["status"] = "uploaded"
        return True
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
        if str(entry.get("status", "")).lower() == "uploaded":
            print(f"   - {entry.get('file_id')}: already uploaded (skipped)")
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

    uploaded = [e["file_id"] for e in file_uploads if str(e.get("status", "")).lower() == "uploaded"]
    pending = [e["file_id"] for e in file_uploads if str(e.get("status", "")).lower() != "uploaded"]

    print("\nSummary:")
    print(f"   uploaded: {len(uploaded)}  |  still uploading: {len(pending)}")

    if pending:
        print("Some files are still uploading. Wait a moment and run this file again.")
    else:
        print('[OK] All files uploaded. Next: put an uploaded file_id into config.json '
              '("process": {"file_id": ...}) and run  python 3_create_job.py')


if __name__ == "__main__":
    asyncio.run(main())
