/*
 * 5_create_report.js  —  STEP 5: Request an axes4 score report
 * ============================================================
 * Asks the API to generate an axes4 accessibility score report for a file.
 * Returns a report job_id.
 *
 * How to run:  node 5_create_report.js
 *
 * What it saves to data.json:
 *   "report_process": [ { "file_id": "....", "job_id": "....", "status": "Processing" }, ... ]
 */

const { BASE_URL, API_KEY, buildHeaders, getValue, saveValue, showResponse } = require("./helper");

// ============================================================
// ===== EDIT HERE =====
// ============================================================

const FILE_ID = ""; // the file_id to generate a report for
// ============================================================
// ===== STOP EDITING (the rest runs by itself) =====
// ============================================================

async function main() {
  if (!FILE_ID) {
    console.log("[X] No file_id given. Paste a FILE_ID above.");
    return;
  }

  const payload = { file_id: FILE_ID };

  console.log(`Requesting a score report for file_id ${FILE_ID} ...`);
  const response = await fetch(`${BASE_URL}/report/`, {
    method: "POST",
    headers: buildHeaders(API_KEY),
    body: JSON.stringify(payload),
  });

  const body = await showResponse(response);

  if ((response.status === 200 || response.status === 201) && body) {
    const data = body.data || {};
    const jobId = data.job_id;

    if (jobId) {
      const reportProcess = getValue("report_process", []);
      if (!reportProcess.some((r) => r.job_id === jobId)) {
        reportProcess.push({ file_id: FILE_ID, job_id: jobId, status: "Processing" });
        saveValue("report_process", reportProcess);
      }
      console.log("\n[OK] Got report job_id:", jobId);
      console.log("Next: run  node 6_check_report.js");
    } else {
      console.log(
        "\n[!] Could not find 'job_id' in the response. " +
          "Check the printed response above and update the key name."
      );
    }
  } else {
    console.log(
      "\n[X] Could not request the report. Check the file_id and status code above."
    );
  }
}

main();
