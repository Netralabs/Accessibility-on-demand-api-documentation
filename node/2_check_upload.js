/*
 * 2_check_upload.js  —  STEP 2: Check upload status
 * =================================================
 * Checks ALL files saved by Step 1 at the same time (concurrently).
 * Files already "uploaded" are skipped; the rest are updated.
 * Status will be 'Uploading' or 'Uploaded'.
 *
 * How to run:  node 2_check_upload.js
 */

const { BASE_URL, API_KEY, buildHeaders, getValue, saveValue } = require("./helper");


// Pulls the status out of the GET /file-upload/{file_id} response.
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
    resp = await fetch(`${BASE_URL}/file-upload/${fileId}`, { headers });
  } catch (e) {
    console.log(`   - ${fileId}: request error (${e.message})`);
    return false;
  }

  if (resp.status !== 200) {
    console.log(`   - ${fileId}: could not check (status code ${resp.status})`);
    return false;
  }

  let body;
  try {
    body = await resp.json();
  } catch (e) {
    console.log(`   - ${fileId}: could not read response`);
    return false;
  }

  const newStatus = readStatus(body) || "unknown";
  console.log(`   - ${fileId}: ${newStatus}`);

  if (String(newStatus).toLowerCase() === "uploaded") {
    entry.status = "uploaded";
    return true;
  }
  return false;
}

async function main() {
  const fileUploads = getValue("file_uploads", []);

  if (fileUploads.length === 0) {
    console.log("[X] No files found. Run 1_upload.js first.");
    return;
  }

  const headers = buildHeaders(API_KEY);

  const pending = [];
  for (const entry of fileUploads) {
    if (String(entry.status || "").toLowerCase() === "uploaded") {
      console.log(`   - ${entry.file_id}: already uploaded (skipped)`);
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

  const uploaded = fileUploads.filter(
    (e) => String(e.status || "").toLowerCase() === "uploaded"
  );
  const stillPending = fileUploads.filter(
    (e) => String(e.status || "").toLowerCase() !== "uploaded"
  );

  console.log("\nSummary:");
  console.log(`   uploaded: ${uploaded.length}  |  still uploading: ${stillPending.length}`);

  if (stillPending.length > 0) {
    console.log("Some files are still uploading. Wait a moment and run this file again.");
  } else {
    console.log("[OK] All files uploaded. Next: run  node 3_create_job.js");
  }
}

main();
