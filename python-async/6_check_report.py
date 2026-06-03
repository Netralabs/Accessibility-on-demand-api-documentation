"""
6_check_report.py (async)  —  STEP 6: Get the score report
==========================================================
Checks ALL reports saved by Step 5 at the same time (concurrently).
  - Reports already "Completed" are skipped.
  - When a report is Completed, the full "details" block is saved.
  - Failed reports (or unreadable responses) are logged to errors.json, not data.json.

EDIT NOTHING HERE. Your api_key lives in  ../config.json

How to run:  python 6_check_report.py

Note: the download_url expires after a short time (expires_in_seconds).
Download the score report PDF soon, or re-run this file.
"""

import asyncio
import httpx
from helper import BASE_URL, api_key, build_headers, get_value, save_value, log_job_error

FINISHED = {"completed"}


def read_report(body):
    if body.get("success") is False:
        return "Failed", None, body.get("error") or {}
    data = body.get("data") or {}
    return data.get("status"), data.get("details"), None


async def check_one(client, entry, headers):
    job_id = entry.get("job_id")
    try:
        resp = await client.get(f"{BASE_URL}/report/{job_id}", headers=headers)
    except httpx.HTTPError as e:
        print(f"   - {job_id}: request error ({e})")
        log_job_error(job_id, 0, f"Request error: {e}", None)
        return False

    try:
        status, details, error = read_report(resp.json())
    except ValueError:
        print(f"   - {job_id}: could not check (status code {resp.status_code})")
        log_job_error(job_id, resp.status_code, "Could not read/parse report response", None)
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
        # Failed reports are not kept in data.json — they go to errors.json (job_errors).
        code = error.get("code", "")
        detail = error.get("detail", "")
        print(f"     error: {code} - {detail}")
        log_job_error(job_id, resp.status_code, f"{code} {detail}".strip(), error)

    return changed


async def main():
    key = api_key()
    report_process = get_value("report_process", [])

    if not report_process:
        print("[X] No reports found. Run 5_create_report.py first.")
        return

    headers = build_headers(key)

    pending_entries = []
    for entry in report_process:
        if str(entry.get("status", "")).lower() in FINISHED:
            print(f"   - {entry.get('job_id')}: already {entry.get('status')} (skipped)")
        else:
            pending_entries.append(entry)

    print(f"\nChecking {len(pending_entries)} report(s) concurrently...\n")

    changed = False
    if pending_entries:
        async with httpx.AsyncClient() as client:
            results = await asyncio.gather(
                *[check_one(client, e, headers) for e in pending_entries]
            )
        changed = any(results)

    if changed:
        save_value("report_process", report_process)

    done = [r for r in report_process if str(r.get("status", "")).lower() in FINISHED]
    pending = [r for r in report_process if str(r.get("status", "")).lower() not in FINISHED]

    print("\nSummary:")
    print(f"   finished: {len(done)}  |  still generating: {len(pending)}")

    if pending:
        print("Some reports are still generating. Wait a moment and run this file again.")
    else:
        print("[OK] All reports finished. Download your score report PDF(s) using the URL(s) above.")


if __name__ == "__main__":
    asyncio.run(main())
