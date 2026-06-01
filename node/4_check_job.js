/*
 * 4_check_job.js  —  STEP 4: Check the job & get the tagged PDF
 * =============================================================
 * Checks ALL jobs saved by Step 3 at the same time (concurrently).
 *   - Jobs already "Completed" are skipped.
 *   - For the rest, the status is updated.
 *   - When a job is Completed, the full "details" block (download_url +
 *     expires_in_seconds) is saved on that job.
 *
 * How to run:  node 4_check_job.js
 *
 * Note: the download_url expires after a short time (expires_in_seconds, e.g.
 * 300s = 5 minutes). Download the tagged PDF soon, or re-run this file.
 */

const { BASE_URL, buildHeaders, getValue, saveValue } = require("./helper");

// ============================================================
// ===== EDIT HERE =====
// ============================================================
const API_KEY = "aod-xxxxxxxxxxx"; // paste your key from Section 3
// ============================================================
// ===== STOP EDITING (the rest runs by itself) =====
// ============================================================

// Statuses that mean "done, no need to check again".
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

async function checkOne(entry, headers) {
  const jobId = entry.job_id;
  let resp;
  try {
    resp = await fetch(`${BASE_URL}/jobs/${jobId}`, { headers });
  } catch (e) {
    console.log(`   - ${jobId}: request error (${e.message})`);
    return false;
  }

  let body;
  try {
    body = await resp.json();
  } catch (e) {
    console.log(`   - ${jobId}: could not check (status code ${resp.status})`);
    return false;
  }

  let [status, details, error] = readJob(body);
  status = status || "unknown";
  console.log(`   - ${jobId}: ${status}`);

  let changed = false;

  if (status !== entry.status) {
    entry.status = status;
    changed = true;
  }

  if (String(status).toLowerCase() === "completed" && details) {
    entry.details = details;
    delete entry.error; // clear any old error
    changed = true;
    console.log(`     download_url: ${details.download_url}`);
    console.log(`     expires_in_seconds: ${details.expires_in_seconds}`);
  }

  if (error) {
    entry.error = error;
    changed = true;
    console.log(`     error: ${error.code} - ${error.detail}`);
  }

  return changed;
}

async function main() {
  const jobProcess = getValue("job_process", []);

  if (jobProcess.length === 0) {
    console.log("[X] No jobs found. Run 3_create_job.js first.");
    return;
  }

  const headers = buildHeaders(API_KEY);

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
  const stillPending = jobProcess.filter(
    (j) => !FINISHED.has(String(j.status || "").toLowerCase())
  );

  console.log("\nSummary:");
  console.log(`   finished: ${done.length}  |  still processing: ${stillPending.length}`);

  if (stillPending.length > 0) {
    console.log("Some jobs are still processing. Wait a moment and run this file again.");
  } else {
    console.log("[OK] All jobs finished. You can now run  node 5_create_report.js");
  }
}

main();
