/*
 * 3_create_job.js  —  STEP 3: Start processing the PDF
 * ====================================================
 * Sends an uploaded file for processing (tagging) and gets back a job_id.
 * You choose the processing LEVEL (1 or 2).
 *
 * How to run:  node 3_create_job.js
 *
 * What it saves to data.json:
 *   "job_process": [ { "file_id": "....", "job_id": "....", "status": "Queued" }, ... ]
 */

const { BASE_URL, API_KEY, buildHeaders, getValue, saveValue, showResponse } = require("./helper");

// ============================================================
// ===== EDIT HERE =====
// ============================================================
const FILE_ID = "";

const LEVEL = 1; // 👈 choose 1 or 2
// ============================================================
// ===== STOP EDITING (the rest runs by itself) =====
// ============================================================

async function main() {
  if (!FILE_ID) {
    console.log("[X] No file_id given. Paste an uploaded FILE_ID above.");
    return;
  }

  const payload = { file_id: FILE_ID, level: LEVEL };

  console.log(`Starting a job for file_id ${FILE_ID} at level ${LEVEL} ...`);
  const response = await fetch(`${BASE_URL}/jobs`, {
    method: "POST",
    headers: buildHeaders(API_KEY),
    body: JSON.stringify(payload),
  });

  const body = await showResponse(response);

  if (response.status === 409) {
    console.log("\n[Conflict] This is already processed: changed file id", FILE_ID);
  }

  if ((response.status === 200 || response.status === 201) && body) {
    const data = body.data || {};
    const jobId = data.job_id;

    if (jobId) {
      const jobProcess = getValue("job_process", []);
      if (!jobProcess.some((j) => j.job_id === jobId)) {
        jobProcess.push({ file_id: FILE_ID, job_id: jobId, status: "Queued" });
        saveValue("job_process", jobProcess);
      }
      console.log("\n[OK] Got job_id:", jobId);
      console.log("Next: run  node 4_check_job.js");
    } else {
      console.log(
        "\n[!] Could not find 'job_id' in the response. " +
          "Check the printed response above and update the key name."
      );
    }
  } else {
    console.log(
      "\n[X] Could not start the job. Check the file_id, level, and status code above."
    );
  }
}

main();
