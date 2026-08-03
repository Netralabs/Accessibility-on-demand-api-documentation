/*
 * re_upload.js  —  Retry files whose upload Failed
 * ================================================
 * When Step 2 (2_check_upload.js) shows a file's status as "failed" and
 * "can_reupload" is true, this script retries the upload for those files by
 * calling  POST /files/re-upload/{file_id}  for each of them (concurrently).
 *
 * It reads the files saved in data.json, picks the ones that failed and can be
 * re-uploaded, and re-uploads each one. Re-uploading restarts the background
 * transfer (the status goes back to "Uploading"), so afterwards run
 * 2_check_upload.js again to see whether it finished.
 *
 * A file whose status is failed with "can_reupload": false can't be recovered —
 * upload a fresh copy with 1_upload.js instead.
 *
 * EDIT NOTHING HERE. Your api_key lives in  ../config.json
 *
 * How to run:  node re_upload.js
 */

const { BASE_URL, apiKey, buildHeadersAuthOnly, getValue, saveValue, logFileError } = require("./helper");

// The re-upload response wraps the file info in 'data' — return it (or {}).
function readData(body) {
  if (body && typeof body === "object" && body.data && typeof body.data === "object") {
    return body.data;
  }
  return {};
}

async function reuploadOne(entry, headers) {
  const fileId = entry.file_id;
  let resp;
  try {
    resp = await fetch(`${BASE_URL}/files/re-upload/${fileId}`, { method: "POST", headers });
  } catch (e) {
    console.log(`   - ${fileId}: request error (${e.message})`);
    logFileError(fileId, 0, "Re-upload request error: " + e.message, null);
    return false;
  }

  if (resp.status !== 200) {
    console.log(`   - ${fileId}: re-upload failed (status code ${resp.status})`);
    let raw = null;
    try {
      raw = await resp.json();
    } catch (e) {
      raw = null;
    }
    logFileError(fileId, resp.status, "Re-upload request failed", raw);
    return false;
  }

  let body;
  try {
    body = await resp.json();
  } catch (e) {
    console.log(`   - ${fileId}: could not read response`);
    logFileError(fileId, resp.status, "Could not read/parse re-upload response", null);
    return false;
  }

  const newStatus = readData(body).uploading_status || "Uploading";
  // A successful re-upload restarts the background transfer. Reset our tracked
  // status so Step 2 will check it again, and clear the old failure info.
  entry.status = String(newStatus);
  delete entry.uploading_error;
  delete entry.can_reupload;
  console.log(`   - ${fileId}: re-upload started (status: ${newStatus})`);
  return true;
}

async function main() {
  const key = apiKey();
  const fileUploads = getValue("file_uploads", []);

  if (fileUploads.length === 0) {
    console.log("[X] No files found. Run 1_upload.js first.");
    return;
  }

  // Split the failed files into 'can retry' vs 'cannot retry'.
  const retryable = [];
  const blocked = [];
  for (const entry of fileUploads) {
    if (String(entry.status || "").toLowerCase() === "failed") {
      (entry.can_reupload ? retryable : blocked).push(entry);
    }
  }

  if (retryable.length === 0) {
    if (blocked.length > 0) {
      console.log("[!] Some files failed but cannot be re-uploaded (can_reupload = false):");
      for (const e of blocked) {
        console.log(`   - ${e.file_id}: ${e.uploading_error || "upload failed"}`);
      }
      console.log("    These can't be recovered — upload a fresh copy with  node 1_upload.js");
    } else {
      console.log("[OK] No failed files to re-upload.");
      console.log("    (Run  node 2_check_upload.js  first — it marks a file 'failed' if its upload fails.)");
    }
    return;
  }

  const headers = buildHeadersAuthOnly(key);
  console.log(`Re-uploading ${retryable.length} failed file(s) concurrently...\n`);

  const results = await Promise.all(retryable.map((e) => reuploadOne(e, headers)));

  if (results.some(Boolean)) saveValue("file_uploads", fileUploads);

  const started = results.filter(Boolean).length;
  let line = `   re-upload started: ${started}  |  couldn't start: ${results.length - started}`;
  if (blocked.length > 0) line += `  |  not re-uploadable: ${blocked.length}`;
  console.log("\nSummary:");
  console.log(line);
  if (started > 0) {
    console.log("\nNext: run  node 2_check_upload.js  again to see whether they finished uploading.");
  }
}

main();
