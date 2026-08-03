/*
 * 2_check_upload.js  —  STEP 2: Check upload status
 * =================================================
 * Checks ALL files saved by Step 1 at the same time (concurrently) and updates
 * each one's status: "uploaded", still "uploading", or "failed".
 *
 * A file that comes back "failed" is recorded with its error and a "can_reupload"
 * flag. If can_reupload is true, retry it with  node re_upload.js  and run this
 * again; if false, the file can't be recovered — upload a fresh copy with
 * 1_upload.js. Files already "uploaded" or "failed" are skipped on later runs.
 *
 * EDIT NOTHING HERE. Your api_key lives in  ../config.json
 *
 * How to run:  node 2_check_upload.js
 */

const { BASE_URL, apiKey, buildHeaders, getValue, saveValue, logFileError } = require("./helper");

// Pulls the status out of the GET /files/status/{file_id} response.
function readStatus(body) {
  if (body && typeof body === "object" && "status" in body) return body.status;
  const data = body && body.data;
  if (data && typeof data === "object" && "uploading_status" in data) {
    return data.uploading_status;
  }
  return null;
}

async function checkOne(entry, headers) {
  const fileId = entry.file_id;
  let resp;
  try {
    resp = await fetch(`${BASE_URL}/files/status/${fileId}`, { headers });
  } catch (e) {
    console.log(`   - ${fileId}: request error (${e.message})`);
    logFileError(fileId, 0, "Request error: " + e.message, null);
    return false;
  }

  if (resp.status !== 200) {
    console.log(`   - ${fileId}: could not check (status code ${resp.status})`);
    logFileError(fileId, resp.status, "Could not check upload status", null);
    return false;
  }

  let body;
  try {
    body = await resp.json();
  } catch (e) {
    console.log(`   - ${fileId}: could not read response`);
    logFileError(fileId, resp.status, "Could not read/parse response body", null);
    return false;
  }

  const data = body && typeof body.data === "object" && body.data ? body.data : {};
  const newStatus = readStatus(body) || "unknown";
  const statusL = String(newStatus).toLowerCase();

  if (statusL === "uploaded") {
    console.log(`   - ${fileId}: ${newStatus}`);
    entry.status = "uploaded";
    delete entry.uploading_error;
    delete entry.can_reupload;
    return true;
  }

  if (statusL === "failed") {
    // The background upload failed. Record why, and whether it can be retried,
    // so re_upload.js knows what to do.
    const err = data.uploading_error || "upload failed";
    const can = Boolean(data.can_reupload);
    entry.status = "failed";
    entry.uploading_error = err;
    entry.can_reupload = can;
    const hint = can ? "can re-upload" : "cannot re-upload";
    console.log(`   - ${fileId}: Failed — ${err}  (${hint})`);
    return true;
  }

  // Still uploading (or an unexpected status) — check again next run.
  console.log(`   - ${fileId}: ${newStatus}`);
  return false;
}

async function main() {
  const key = apiKey();
  const fileUploads = getValue("file_uploads", []);

  if (fileUploads.length === 0) {
    console.log("[X] No files found. Run 1_upload.js first.");
    return;
  }

  const headers = buildHeaders(key);

  const pending = [];
  for (const entry of fileUploads) {
    const status = String(entry.status || "").toLowerCase();
    if (status === "uploaded") {
      console.log(`   - ${entry.file_id}: already uploaded (skipped)`);
    } else if (status === "failed") {
      const hint = entry.can_reupload ? "can re-upload" : "cannot re-upload";
      console.log(`   - ${entry.file_id}: already failed (${hint}, skipped)`);
    } else {
      pending.push(entry);
    }
  }

  console.log(`\nChecking ${pending.length} file(s) concurrently...\n`);

  let changed = false;
  if (pending.length > 0) {
    const results = await Promise.all(pending.map((e) => checkOne(e, headers)));
    changed = results.some(Boolean);
  }

  if (changed) saveValue("file_uploads", fileUploads);

  const st = (e) => String(e.status || "").toLowerCase();
  const uploaded = fileUploads.filter((e) => st(e) === "uploaded");
  const failed = fileUploads.filter((e) => st(e) === "failed");
  const stillPending = fileUploads.filter((e) => st(e) !== "uploaded" && st(e) !== "failed");

  console.log("\nSummary:");
  console.log(
    `   uploaded: ${uploaded.length}  |  failed: ${failed.length}  |  still uploading: ${stillPending.length}`
  );

  if (failed.length > 0) {
    console.log("\n[!] Some files failed to upload:");
    for (const e of failed) {
      const hint = e.can_reupload ? "can re-upload" : "cannot re-upload";
      console.log(`   - ${e.file_id}: ${e.uploading_error || "upload failed"}  (${hint})`);
    }
    const retryable = failed.filter((e) => e.can_reupload);
    const blocked = failed.filter((e) => !e.can_reupload);
    if (retryable.length > 0) {
      console.log(`    ${retryable.length} can be retried — run  node re_upload.js`);
    }
    if (blocked.length > 0) {
      console.log(`    ${blocked.length} cannot be re-uploaded — upload a fresh copy with  node 1_upload.js`);
    }
  }

  if (stillPending.length > 0) {
    console.log("\nSome files are still uploading. Wait a moment and run this file again.");
  } else if (failed.length === 0) {
    console.log("\n[OK] All files uploaded. Next: put an uploaded file_id into config.json " +
      '("process": {"file_id": ...}) and run  node 3_create_job.js');
  }
}

main();
