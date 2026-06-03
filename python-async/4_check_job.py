"""
4_check_job.py (async)  —  STEP 4: Check the job & get the tagged PDF
====================================================================
Checks ALL jobs saved by Step 3 at the same time (concurrently).
  - Jobs already "Completed" are skipped.
  - When a job is Completed, the full "details" block is saved on that job.
  - Failed jobs (or unreadable responses) are logged to errors.json, not data.json.

EDIT NOTHING HERE. Your api_key lives in  ../config.json

How to run:  python 4_check_job.py

Note: the download_url expires after a short time (expires_in_seconds, e.g.
300s = 5 minutes). Download the tagged PDF soon, or re-run this file.
"""

import asyncio
import httpx
from helper import BASE_URL, api_key, build_headers, get_value, save_value, log_job_error

FINISHED = {"completed"}


def read_job(body):
    if body.get("success") is False:
        return "Failed", None, body.get("error") or {}
    data = body.get("data") or {}
    return data.get("status"), data.get("details"), None


async def check_one(client, entry, headers):
    job_id = entry.get("job_id")
    try:
        resp = await client.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
    except httpx.HTTPError as e:
        print(f"   - {job_id}: request error ({e})")
        log_job_error(job_id, 0, f"Request error: {e}", None)
        return False

    try:
        status, details, error = read_job(resp.json())
    except ValueError:
        print(f"   - {job_id}: could not check (status code {resp.status_code})")
        log_job_error(job_id, resp.status_code, "Could not read/parse job response", None)
        return False

    status = status or "unknown"
    print(f"   - {job_id}: {status}")

    changed = False

    if status != entry.get("status"):
        entry["status"] = status
        changed = True

    if str(status).lower() == "completed" and details:
        entry["details"] = details
        changed = True
        print(f"     download_url: {details.get('download_url')}")
        print(f"     expires_in_seconds: {details.get('expires_in_seconds')}")

    if error:
        # Failed jobs are not kept in data.json — they go to errors.json (job_errors).
        code = error.get("code", "")
        detail = error.get("detail", "")
        print(f"     error: {code} - {detail}")
        log_job_error(job_id, resp.status_code, f"{code} {detail}".strip(), error)

    return changed


async def main():
    key = api_key()
    job_process = get_value("job_process", [])

    if not job_process:
        print("[X] No jobs found. Run 3_create_job.py first.")
        return

    headers = build_headers(key)

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

    done = [j for j in job_process if str(j.get("status", "")).lower() in FINISHED]
    pending = [j for j in job_process if str(j.get("status", "")).lower() not in FINISHED]

    print("\nSummary:")
    print(f"   finished: {len(done)}  |  still processing: {len(pending)}")

    if pending:
        print("Some jobs are still processing. Wait a moment and run this file again.")
    else:
        print('[OK] All jobs finished. To get a score report, put a file_id into config.json '
              '("report": {"file_id": ...}) and run  python 5_create_report.py')


if __name__ == "__main__":
    asyncio.run(main())
