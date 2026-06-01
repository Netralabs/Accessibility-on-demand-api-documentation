"""
6_check_report.py (async)  —  STEP 6: Get the score report
==========================================================
Checks ALL reports saved by Step 5 at the same time (concurrently).
  - Reports already "Completed" are skipped.
  - For the rest, the status is updated.
  - When a report is Completed, the full "details" block (download_url +
    expires_in_seconds) is saved, and any old error is removed.

How to run:  python 6_check_report.py

Note about the download URL:
  The download_url expires after a short time (expires_in_seconds). Download
  the score report PDF soon, or re-run this file to get a fresh URL.
"""

import asyncio
import httpx
from helper import BASE_URL, build_headers, get_value, save_value

# ============================================================
# ===== EDIT HERE =====
# ============================================================
API_KEY = "aod-xxxxxxxxxxx"   # paste your key from Section 3
# ============================================================
# ===== STOP EDITING (the rest runs by itself) =====
# ============================================================

# Statuses that mean "done, no need to check again".
FINISHED = {"completed"}


def read_report(body):
    """
    Reads the GET /report/{job_id} response.
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
        resp = await client.get(f"{BASE_URL}/report/{job_id}", headers=headers)
    except httpx.HTTPError as e:
        print(f"   - {job_id}: request error ({e})")
        return False

    try:
        status, details, error = read_report(resp.json())
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

    # Save the whole details block when completed; clear any old error.
    if str(status).lower() == "completed" and details:
        entry["details"] = details
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
    report_process = get_value("report_process", [])

    if not report_process:
        print("[X] No reports found. Run 5_create_report.py first.")
        return

    headers = build_headers(API_KEY)

    pending_entries = []
    for entry in report_process:
        if str(entry.get("status", "")).lower() in FINISHED:
            print(f"   - {entry.get('job_id')}: already {entry.get('status')} (skipped)")
        else:
            pending_entries.append(entry)

    print(f"\nChecking {len(pending_entries)} report(s) concurrently...\n")

    changed = False
    if pending_entries:
        async with httpx.AsyncClient(timeout=60) as client:
            results = await asyncio.gather(
                *[check_one(client, e, headers) for e in pending_entries]
            )
        changed = any(results)

    if changed:
        save_value("report_process", report_process)

    # Summary.
    done = [r for r in report_process if str(r.get("status", "")).lower() in FINISHED]
    pending = [r for r in report_process if str(r.get("status", "")).lower() not in FINISHED]

    print("\nSummary:")
    print(f"   finished: {len(done)}  |  still generating: {len(pending)}")

    if pending:
        print("Some reports are still generating. Wait a moment and run this file again.")
    else:
        print(
            "[OK] All reports finished. Download your score report PDF(s) using the URL(s) above."
        )


if __name__ == "__main__":
    asyncio.run(main())
