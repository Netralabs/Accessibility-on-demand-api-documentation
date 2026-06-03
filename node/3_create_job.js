/*
 * 3_create_job.js  —  STEP 3: Start processing the PDF
 * ====================================================
 * Sends an uploaded file for processing (tagging) and gets back a job_id.
 *
 * EDIT NOTHING HERE. Set these in  ../config.json  under "process":
 *   "process": { "file_id": "<an uploaded file_id>", "level": 1 }   // level 1 or 2
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

  if (!fileId) {
    console.log('[X] No file_id given. Set "process": {"file_id": ...} in config.json ' +
      "(use an uploaded file_id from Step 2).");
    return;
  }

  const payload = { file_id: fileId, level };

  console.log(`Starting a job for file_id ${fileId} at level ${level} ...`);
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
        jobProcess.push({ file_id: fileId, job_id: jobId, status: "Queued" });
        saveValue("job_process", jobProcess);
      }
      console.log("\n[OK] Got job_id:", jobId);
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
