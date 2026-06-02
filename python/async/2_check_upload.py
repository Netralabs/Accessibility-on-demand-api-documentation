"""
2_check_upload.py (async)  —  STEP 2: Check upload status
=========================================================
Checks ALL files saved by Step 1 at the same time (concurrently).
Files already "uploaded" are skipped; the rest are updated.
Status will be 'Uploading' or 'Uploaded'.

How to run:  python 2_check_upload.py
"""

import asyncio
import httpx
from helper import BASE_URL,API_KEY, build_headers, get_value, save_value



def read_status(body):
    """
    Pulls the status out of the GET /file-upload/{file_id} response.
    Tries a few common locations. If your API nests it differently,
    adjust the lines below.
    """
    # direct: {"status": "..."}
    if isinstance(body, dict) and "status" in body:
        return body["status"]
    # nested under data: {"data": {"uploading_status": "..."}}
    data = body.get("data") if isinstance(body, dict) else None
    if isinstance(data, dict) and "uploading_status" in data:
        return data["uploading_status"]
    return None


async def check_one(client, entry, headers):
    file_id = entry.get("file_id")
    try:
        resp = await client.get(f"{BASE_URL}/file-upload/{file_id}", headers=headers)
    except httpx.HTTPError as e:
        print(f"   - {file_id}: request error ({e})")
        return False

    if resp.status_code != 200:
        print(f"   - {file_id}: could not check (status code {resp.status_code})")
        return False

    new_status = read_status(resp.json()) or "unknown"
    print(f"   - {file_id}: {new_status}")

    # Update only if it has finished uploading.
    if str(new_status).lower() == "uploaded":
        entry["status"] = "uploaded"
        return True
    return False


async def main():
    file_uploads = get_value("file_uploads", [])

    if not file_uploads:
        print("[X] No files found. Run 1_upload.py first.")
        return

    headers = build_headers(API_KEY)

    # Skip ones already finished; check the rest concurrently.
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

    # Save back the updated list only if something changed.
    if changed:
        save_value("file_uploads", file_uploads)

    # Summary.
    uploaded = [
        e["file_id"] for e in file_uploads if str(e.get("status", "")).lower() == "uploaded"
    ]
    pending = [
        e["file_id"] for e in file_uploads if str(e.get("status", "")).lower() != "uploaded"
    ]

    print("\nSummary:")
    print(f"   uploaded: {len(uploaded)}  |  still uploading: {len(pending)}")

    if pending:
        print("Some files are still uploading. Wait a moment and run this file again.")
    else:
        print("[OK] All files uploaded. Next: run  python 3_create_job.py")


if __name__ == "__main__":
    asyncio.run(main())
