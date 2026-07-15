"""
4_check_job.py (async)  —  STEP 4: Check the job & get the tagged PDF
====================================================================
Checks ALL jobs saved by Step 3 at the same time (concurrently).
  - Jobs already "Completed", "Warning", or "Failed" are skipped on re-run.
  - When a job is Completed, the full "details" block (with the download_url) is saved on that job.
  - When a job is "Warning", some pages failed but a tagged PDF is still produced (with the download_url):
    the download_url is saved like a success, and the list of failed pages is
    also recorded in errors.json (job_errors) for your reference.
  - Failed jobs (or unreadable responses) are logged to errors.json, not data.json.

Manual review case:
  If you started the job with requires_manual_review=true (Step 3), the job may
  come back with API status "Completed" BUT no download_url — the API is holding
  the link until you complete the manual review in the web UI. This script marks
  such jobs locally as "AwaitingManualReview" (not "Completed") so polling keeps
  going. To finish them:
    1. Go to https://app.accessibilityondemand.ai/login and log in
       (you'll also receive an email when the file is ready to review).
    2. Open the batch, select the file, click Review.
    3. On the last page of the review, click the Complete button.
    4. Run this file again — the download_url will now be included.

EDIT NOTHING HERE. Your api_key lives in  ../config.json

How to run:  python 4_check_job.py

Note: the download_url expires after a short time (expires_in_seconds, e.g.
300s = 5 minutes; or links may last longer). Download the tagged PDF soon, or re-run this file.
"""

import asyncio
import httpx
from helper import BASE_URL, api_key, build_headers, get_value, save_value, log_job_error

# Statuses that mean "no more polling needed". "AwaitingManualReview" is
# deliberately NOT in this set — we want to keep polling until the user finishes
# the review in the UI and the API starts returning a download_url.
FINISHED = {"completed", "warning", "failed"}


def read_job(body):
    if body.get("success") is False:
        # On failure the reason may sit in data.details.error or in a top-level error object.
        data = body.get("data") or {}
        details = data.get("details") or {}
        error = body.get("error") or {}
        if details.get("error") and not error:
            error = {"code": data.get("status", "Failed"), "detail": details.get("error")}
        return data.get("status", "Failed"), None, error
    data = body.get("data") or {}
    return data.get("status"), data.get("details"), None


def is_manual_review_pending(api_status, details):
    """
    The API reports status="Completed" for two very different situations:
      1) Fully done  -> details has a download_url
      2) Waiting for manual review -> details has a "message" but NO download_url
    Detect case 2 so we can label it distinctly and keep polling.
    """
    return (
        str(api_status or "").lower() == "completed"
        and isinstance(details, dict)
        and not details.get("download_url")
        and bool(details.get("message"))
    )


async def check_one(client, entry, headers):
    job_id = entry.get("job_id")
    try:
        resp = await client.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
    except httpx.HTTPError as e:
        print(f"   - {job_id}: request error ({e})")
        log_job_error(job_id, 0, f"Request error: {e}", None)
        return False

    try:
        api_status, details, error = read_job(resp.json())
    except ValueError:
        print(f"   - {job_id}: could not check (status code {resp.status_code})")
        log_job_error(job_id, resp.status_code, "Could not read/parse job response", None)
        return False

    api_status = api_status or "unknown"

    # Distinguish the "completed but manual review pending" case locally so it
    # doesn't get bucketed with the fully-done jobs.
    manual_review_pending = is_manual_review_pending(api_status, details)
    local_status = "AwaitingManualReview" if manual_review_pending else api_status

    print(f"   - {job_id}: {local_status}")

    changed = False

    if local_status != entry.get("status"):
        entry["status"] = local_status
        changed = True

    if manual_review_pending:
        # Show a friendly, actionable note so the user knows exactly what to do.
        # We do NOT save details here (there's no download_url yet).
        print(f"     note: {details.get('message')}")
        print( "     -> log in at https://app.accessibilityondemand.ai/login,")
        print( "        open the batch, select the file, click Review,")
        print( "        then click Complete on the last page.")
        print( "        After that, run this file again to get the download_url.")

    # Completed AND Warning both carry a download_url — save and print it either way.
    if details and details.get("download_url"):
        entry["details"] = details
        changed = True
        print(f"     download_url: {details.get('download_url')}")
        print(f"     expires_in_seconds: {details.get('expires_in_seconds')}")

        # Warning = partial success: the link is good, but some pages failed.
        # Keep the link in data.json AND record which pages failed in errors.json.
        if str(local_status).lower() == "warning" and details.get("error"):
            note = details.get("error")
            print(f"     note (partial — some pages failed): {note}")
            log_job_error(job_id, resp.status_code, f"Warning: {note}", details)  # delete this line if you don't want Warning logged

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
    awaiting = [j for j in job_process if str(j.get("status", "")).lower() == "awaitingmanualreview"]
    still_processing = [
        j for j in job_process
        if str(j.get("status", "")).lower() not in FINISHED
        and str(j.get("status", "")).lower() != "awaitingmanualreview"
    ]

    print("\nSummary:")
    print(f"   finished: {len(done)}  |  awaiting manual review: {len(awaiting)}  |  still processing: {len(still_processing)}")

    if awaiting:
        print("\nJobs ready for manual review:")
        for j in awaiting:
            print(f"   - job_id: {j.get('job_id')}  |  file_id: {j.get('file_id')}")
        print("   Log in at https://app.accessibilityondemand.ai/login, complete the review,")
        print("   then run  python 4_check_job.py  again to get the download link.")

    if still_processing:
        print("\nSome jobs are still processing. Wait a moment and run this file again.")

    if not awaiting and not still_processing:
        print('[OK] All jobs finished. To get a score report, put a file_id into config.json '
              '("report": {"file_id": ...}) and run  python 5_create_report.py')


if __name__ == "__main__":
    asyncio.run(main())
