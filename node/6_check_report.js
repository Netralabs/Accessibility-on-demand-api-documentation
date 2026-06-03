/*
 * 6_check_report.js  —  STEP 6: Get the score report
 * ===================================================
 * Checks ALL reports saved by Step 5 at the same time (concurrently).
 *   - Reports already "Completed" are skipped.
 *   - For the rest, the status is updated.
 *   - When a report is Completed, the full "details" block (download_url +
 *     expires_in_seconds) is saved.
 *   - Failed reports (or unreadable responses) are logged to errors.json,
 *     not data.json.
 *
 * EDIT NOTHING HERE. Your api_key lives in  ../config.json
 *
 * How to run:  node 6_check_report.js
 *
 * Note: the download_url expires after a short time (expires_in_seconds).
 * Download the score report PDF soon, or re-run this file.
 */

const { BASE_URL, apiKey, buildHeaders, getValue, saveValue, logJobError } = require("./helper");

// Statuses that mean "done, no need to check again".
const FINISHED = new Set(["completed"]);

// Reads the GET /report/{job_id} response.
// Returns [status, details, error].
function readReport(body) {
  if (body.success === false) {
    return ["Failed", null, body.error || {}];
  }
  const data = body.data || {};
  return [data.status, data.details, null];
}

async function checkOne(entry, headers) {
  const jobId = entry.job_id;
  let resp;
  try {
    resp = await fetch(`${BASE_URL}/report/${jobId}`, { headers });
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
    logJobError(jobId, resp.status, "Could not read/parse report response", null);
    return false;
  }

  let [status, details, error] = readReport(body);
  status = status || "unknown";
  console.log(`   - ${jobId}: ${status}`);

  let changed = false;

  if (status !== entry.status) {
    entry.status = status;
    changed = true;
  }

  if (String(status).toLowerCase() === "completed" && details) {
    entry.details = details;
    changed = true;
    console.log(`     download_url: ${details.download_url}`);
    console.log(`     expires_in_seconds: ${details.expires_in_seconds}`);
  }

  if (error) {
    // Failed reports are not kept in data.json — they go to errors.json (job_errors).
    console.log(`     error: ${error.code} - ${error.detail}`);
    logJobError(jobId, resp.status, `${error.code || ""} ${error.detail || ""}`.trim(), error);
  }

  return changed;
}

async function main() {
  const key = apiKey();
  const reportProcess = getValue("report_process", []);

  if (reportProcess.length === 0) {
    console.log("[X] No reports found. Run 5_create_report.js first.");
    return;
  }

  const headers = buildHeaders(key);

  const pending = [];
  for (const entry of reportProcess) {
    if (FINISHED.has(String(entry.status || "").toLowerCase())) {
      console.log(`   - ${entry.job_id}: already ${entry.status} (skipped)`);
    } else {
      pending.push(entry);
    }
  }

  console.log(`\nChecking ${pending.length} report(s) concurrently...\n`);

  let changed = false;
  if (pending.length > 0) {
    const results = await Promise.all(pending.map((e) => checkOne(e, headers)));
    changed = results.some(Boolean);
  }

  if (changed) saveValue("report_process", reportProcess);

  const done = reportProcess.filter((r) =>
    FINISHED.has(String(r.status || "").toLowerCase())
  );
  const stillPending = reportProcess.filter(
    (r) => !FINISHED.has(String(r.status || "").toLowerCase())
  );

  console.log("\nSummary:");
  console.log(`   finished: ${done.length}  |  still generating: ${stillPending.length}`);

  if (stillPending.length > 0) {
    console.log("Some reports are still generating. Wait a moment and run this file again.");
  } else {
    console.log(
      "[OK] All reports finished. Download your score report PDF(s) using the URL(s) above."
    );
  }
}

main();
