/*
 * 3_create_job.js  —  STEP 3: Start processing the PDF
 * ====================================================
 * Sends an uploaded file for processing (tagging) and gets back a job_id.
 *
 * EDIT NOTHING HERE. Set these in  ../config.json  under "process":
 *   "process": {
 *     "file_id": "<an uploaded file_id>",
 *     "level": 1,                          // 1 or 2
 *     "requires_manual_review": false      // optional — see below
 *   }
 *
 * Manual review (optional):
 *   Set "requires_manual_review": true if you'd like to review and refine the
 *   automated tagging in the web UI before the tagged PDF becomes downloadable.
 *   When enabled, Step 4 will report the job as "AwaitingManualReview" until you:
 *     1. Go to https://app.accessibilityondemand.ai/login (you'll also get an
 *        email when the file is ready to review).
 *     2. Open the batch, select the file, click Review.
 *     3. On the last page of the review, click the Complete button.
 *   After that, run Step 4 again and it will return the download_url.
 *
 * How to run:  node 3_create_job.js
 *
 * What it saves to data.json:
 *   "job_process": [ { "file_id": "....", "job_id": "....", "status": "Queued" }, ... ]
 */

const { BASE_URL, loadConfig, apiKey, buildHeaders, getValue, saveValue, showResponse, logFileError } = require("./helper");

async function main() {
  const cfg = loadConfig();
  const key = apiKey();
  const process_ = cfg.process || {};
  const fileId = (process_.file_id || "").trim();
  const level = Number.isInteger(process_.level) ? process_.level : 1;

  // Optional. Only accept a real JSON boolean `true`; anything else
  // (missing, false, "true" as a string, etc.) is treated as false so the
  // default behaviour stays "fully automatic, downloadable right away".
  const requiresManualReview = process_.requires_manual_review === true;

  if (!fileId) {
    console.log('[X] No file_id given. Set "process": {"file_id": ...} in config.json ' +
      "(use an uploaded file_id from Step 2).");
    return;
  }

  const payload = {
    file_id: fileId,
    level,
    requires_manual_review: requiresManualReview,
  };

  const reviewNote = requiresManualReview ? "  (with manual review)" : "";
  console.log(`Starting a job for file_id ${fileId} at level ${level}${reviewNote} ...`);
  const response = await fetch(`${BASE_URL}/jobs/`, {
    method: "POST",
    headers: buildHeaders(key),
    body: JSON.stringify(payload),
  });

  const body = await showResponse(response);

  if (response.status === 409) {
    console.log("\n[Conflict] This is already processed: change the file_id in config.json", fileId);
    logFileError(fileId, 409, "Conflict - file already processed", body);
  }

  if ((response.status === 200 || response.status === 201) && body) {
    const data = body.data || {};
    const jobId = data.job_id;

    if (jobId) {
      const jobProcess = getValue("job_process", []);
      if (!jobProcess.some((j) => j.job_id === jobId)) {
        const entry = { file_id: fileId, job_id: jobId, status: "Queued" };
        // Keep a small marker on the entry so data.json makes it clear
        // this job was started with manual review enabled.
        if (requiresManualReview) entry.requires_manual_review = true;
        jobProcess.push(entry);
        saveValue("job_process", jobProcess);
      }
      console.log("\n[OK] Got job_id:", jobId);
      if (requiresManualReview) {
        console.log("     (manual review enabled — Step 4 will prompt you to review in the UI once tagging finishes)");
      }
      console.log("Next: run  node 4_check_job.js");
    } else {
      console.log(
        "\n[!] Could not find 'job_id' in the response. " +
          "Check the printed response above and update the key name."
      );
      logFileError(fileId, response.status, "No job_id in job-create response", body);
    }
  } else if (response.status !== 409) {
    console.log(
      "\n[X] Could not start the job. Check the file_id, level, and status code above."
    );
    logFileError(fileId, response.status, "Could not start job", body);
  }
}

main();
