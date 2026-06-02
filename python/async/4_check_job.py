"""
4_check_job.py (async)  —  STEP 4: Check the job & get the tagged PDF
====================================================================
Checks ALL jobs saved by Step 3 at the same time (concurrently).
  - Jobs already "Completed" are skipped.
  - For the rest, the status is updated.
  - When a job is Completed, the full "details" block (download_url +
    expires_in_seconds) is saved on that job.

How to run:  python 4_check_job.py

Note about the download URL:
  The download_url expires after a short time (expires_in_seconds, e.g. 300s
  = 5 minutes). Download the tagged PDF soon, or re-run this file to get a
  fresh URL.
"""

import asyncio
import httpx
from helper import BASE_URL,API_KEY, build_headers, get_value, save_value



# Statuses that mean "done, no need to check again".
FINISHED = {"completed"}


def read_job(body):
    """
    Reads the GET /jobs/{job_id} response.
    Success shape:  {"success": true,  "data": {"status": "...", "details": {...}}}
    Error shape:    {"success": false, "error": {"code": "...", "detail": "..."}}

    Returns (status, details_dict, error_dict).
    """
    if body.get("success") is False:
        err = body.get("error") or {}
        return "Failed", None, err

    data = body.get("data") or {}
    return data.get("status"), data.get("details"), None


async def check_one(client, entry, headers):
    job_id = entry.get("job_id")
    try:
        resp = await client.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
    except httpx.HTTPError as e:
        print(f"   - {job_id}: request error ({e})")
        return False

    try:
        status, details, error = read_job(resp.json())
    except ValueError:
        print(f"   - {job_id}: could not check (status code {resp.status_code})")
        return False

    status = status or "unknown"
    print(f"   - {job_id}: {status}")

    changed = False

    # Update status if it changed.
    if status != entry.get("status"):
        entry["status"] = status
        changed = True

    # Save the whole details block when completed.
    if str(status).lower() == "completed" and details:
        entry["details"] = details
        # Remove any old error left over from a previous failed check.
        entry.pop("error", None)
        changed = True
        print(f"     download_url: {details.get('download_url')}")
        print(f"     expires_in_seconds: {details.get('expires_in_seconds')}")

    # Save the error info if it failed.
    if error:
        entry["error"] = error
        changed = True
        print(f"     error: {error.get('code')} - {error.get('detail')}")

    return changed


async def main():
    job_process = get_value("job_process", [])

    if not job_process:
        print("[X] No jobs found. Run 3_create_job.py first.")
        return

    headers = build_headers(API_KEY)

    pending_entries = []
    for entry in job_process:
        if str(entry.get("status", "")).lower() in FINISHED:
            print(f"   - {entry.get('job_id')}: already {entry.get('status')} (skipped)")
        else:
            pending_entries.append(entry)

    print(f"\nChecking {len(pending_entries)} job(s) concurrently...\n")

    changed = False
    if pending_entries:
        async with httpx.AsyncClient() as client:
            results = await asyncio.gather(
                *[check_one(client, e, headers) for e in pending_entries]
            )
        changed = any(results)

    if changed:
        save_value("job_process", job_process)

    # Summary.
    done = [j for j in job_process if str(j.get("status", "")).lower() in FINISHED]
    pending = [j for j in job_process if str(j.get("status", "")).lower() not in FINISHED]

    print("\nSummary:")
    print(f"   finished: {len(done)}  |  still processing: {len(pending)}")

    if pending:
        print("Some jobs are still processing. Wait a moment and run this file again.")
    else:
        print("[OK] All jobs finished. You can now run  python 5_create_report.py")


if __name__ == "__main__":
    asyncio.run(main())
