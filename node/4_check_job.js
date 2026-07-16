/*
 * 4_check_job.js  —  STEP 4: Check the job & get the tagged PDF
 * =============================================================
 * Checks ALL jobs saved by Step 3 at the same time (concurrently).
 *   - Jobs already "Completed" are skipped.
 *   - For the rest, the status is updated.
 *   - When a job is Completed, the full "details" block (download_url +
 *     expires_in_seconds) is saved on that job.
 *   - Failed jobs (or unreadable responses) are logged to errors.json,
 *     not data.json.
 *
 * Manual review case:
 *   If you started the job with requires_manual_review=true (Step 3), the job
 *   may come back with API status "Completed" BUT no download_url — the API is
 *   holding the link until you complete the manual review in the web UI. This
 *   script marks such jobs locally as "AwaitingManualReview" (not "Completed")
 *   so polling keeps going. To finish them:
 *     1. Go to https://app.accessibilityondemand.ai/login and log in
 *        (you'll also receive an email when the file is ready to review).
 *     2. Open the batch, select the file, click Review.
 *     3. On the last page of the review, click the Complete button.
 *     4. Run this file again — the download_url will now be included.
 *
 * EDIT NOTHING HERE. Your api_key lives in  ../config.json
 *
 * How to run:  node 4_check_job.js
 *
 * Note: the download_url expires after a short time (expires_in_seconds, e.g.
 * 300s = 5 minutes). Download the tagged PDF soon, or re-run this file.
 */

const { BASE_URL, apiKey, buildHeaders, getValue, saveValue, logJobError } = require("./helper");

// Statuses that mean "done, no need to check again". "awaitingmanualreview" is
// deliberately NOT in this set — we want to keep polling until the user finishes
// the review in the UI and the API starts returning a download_url.
const FINISHED = new Set(["completed"]);

// Reads the GET /jobs/{job_id} response.
// Returns [status, details, error].
function readJob(body) {
  if (body.success === false) {
    return ["Failed", null, body.error || {}];
  }
  const data = body.data || {};
  return [data.status, data.details, null];
}

/*
 * The API reports status="Completed" for two very different situations:
 *   1) Fully done  -> details has a download_url
 *   2) Waiting for manual review -> details has a "message" but NO download_url
 * Detect case 2 so we can label it distinctly and keep polling.
 */
function isManualReviewPending(apiStatus, details) {
  if (!apiStatus || String(apiStatus).toLowerCase() !== "completed") return false;
  if (!details || typeof details !== "object") return false;
  const hasDownload = typeof details.download_url === "string" && details.download_url.length > 0;
  const hasMessage = typeof details.message === "string" && details.message.length > 0;
  return !hasDownload && hasMessage;
}

async function checkOne(entry, headers) {
  const jobId = entry.job_id;
  let resp;
  try {
    resp = await fetch(`${BASE_URL}/jobs/${jobId}`, { headers });
  } catch (e) {
    console.log(`   - ${jobId}: request error (${e.message})`);
    logJobError(jobId, 0, "Request error: " + e.message, null);
    return false;
  }

  let body;
  try {
    body = await resp.json();
  } catch (e) {
    console.log(`   - ${jobId}: could not check (status code ${resp.status})`);
    logJobError(jobId, resp.status, "Could not read/parse job response", null);
    return false;
  }

  let [apiStatus, details, error] = readJob(body);
  apiStatus = apiStatus || "unknown";

  // Distinguish the "completed but manual review pending" case locally so it
  // doesn't get bucketed with the fully-done jobs.
  const manualReviewPending = isManualReviewPending(apiStatus, details);
  const status = manualReviewPending ? "AwaitingManualReview" : apiStatus;

  console.log(`   - ${jobId}: ${status}`);

  let changed = false;

  if (status !== entry.status) {
    entry.status = status;
    changed = true;
  }

  if (manualReviewPending) {
    // Show a friendly, actionable note so the user knows exactly what to do.
    // We do NOT save details here (there's no download_url yet).
    console.log(`     note: ${details.message}`);
    console.log("     -> log in at https://app.accessibilityondemand.ai/login,");
    console.log("        open the batch, select the file, click Review,");
    console.log("        then click Complete on the last page.");
    console.log("        After that, run this file again to get the download_url.");
  }

  if (String(status).toLowerCase() === "completed" && details && details.download_url) {
    entry.details = details;
    changed = true;
    console.log(`     download_url: ${details.download_url}`);
    console.log(`     expires_in_seconds: ${details.expires_in_seconds}`);
  }

  if (error) {
    // Failed jobs are not kept in data.json — they go to errors.json (job_errors).
    console.log(`     error: ${error.code} - ${error.detail}`);
    logJobError(jobId, resp.status, `${error.code || ""} ${error.detail || ""}`.trim(), error);
  }

  return changed;
}

async function main() {
  const key = apiKey();
  const jobProcess = getValue("job_process", []);

  if (jobProcess.length === 0) {
    console.log("[X] No jobs found. Run 3_create_job.js first.");
    return;
  }

  const headers = buildHeaders(key);

  const pending = [];
  for (const entry of jobProcess) {
    if (FINISHED.has(String(entry.status || "").toLowerCase())) {
      console.log(`   - ${entry.job_id}: already ${entry.status} (skipped)`);
    } else {
      pending.push(entry);
    }
  }

  console.log(`\nChecking ${pending.length} job(s) concurrently...\n`);

  let changed = false;
  if (pending.length > 0) {
    const results = await Promise.all(pending.map((e) => checkOne(e, headers)));
    changed = results.some(Boolean);
  }

  if (changed) saveValue("job_process", jobProcess);

  const done = jobProcess.filter((j) =>
    FINISHED.has(String(j.status || "").toLowerCase())
  );
  const awaiting = jobProcess.filter(
    (j) => String(j.status || "").toLowerCase() === "awaitingmanualreview"
  );
  const stillProcessing = jobProcess.filter((j) => {
    const s = String(j.status || "").toLowerCase();
    return !FINISHED.has(s) && s !== "awaitingmanualreview";
  });

  console.log("\nSummary:");
  console.log(
    `   finished: ${done.length}  |  awaiting manual review: ${awaiting.length}` +
    `  |  still processing: ${stillProcessing.length}`
  );

  if (awaiting.length > 0) {
    console.log("\nJobs ready for manual review:");
    for (const j of awaiting) {
      console.log(`   - job_id: ${j.job_id}  |  file_id: ${j.file_id}`);
    }
    console.log("   Log in at https://app.accessibilityondemand.ai/login, complete the review,");
    console.log("   then run  node 4_check_job.js  again to get the download link.");
  }

  if (stillProcessing.length > 0) {
    console.log("\nSome jobs are still processing. Wait a moment and run this file again.");
  }

  if (awaiting.length === 0 && stillProcessing.length === 0) {
    console.log("[OK] All jobs finished. To get a score report, put a file_id into config.json " +
      '("report": {"file_id": ...}) and run  node 5_create_report.js');
  }
}

main();
