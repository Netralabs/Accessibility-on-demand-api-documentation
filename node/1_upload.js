/*
 * 1_upload.js  —  STEP 1 (option A): Upload files from your computer
 * =================================================================
 * Uploads every PDF in the repo-root  uploads/  folder directly to the API
 * (multipart/form-data) and gets back a file_id for each accepted file.
 * Use this if your PDFs are on your computer and you don't have a cloud account.
 *
 *   • Files already in S3 / Google Drive (or you have signed URLs)?
 *     Use  1_upload_from_url.js  instead.
 *
 * HOW TO USE:
 *   1. Drop your PDF file(s) into the  uploads/  folder at the repo root.
 *   2. (Optional) set "description" in ../config.json.
 *   3. (Optional) set "user_batch_id" + "batch_name" in ../config.json to group
 *      these files into a specific batch — set BOTH, or leave BOTH blank to have
 *      the API generate a fresh batch for you. See the README for the pairing rules.
 *   4. Run:  node 1_upload.js
 *
 * EDIT NOTHING HERE. All values live in ../config.json.
 *
 * About the responses you may see:
 *   - 200 = all files accepted for uploading.
 *   - 207 = some files were accepted, some failed (e.g. malware detected).
 *           The script still saves the file_ids that succeeded, and logs the
 *           ones that failed to errors.json (under "url_errors").
 *   - 409 = the user_batch_id / batch_name pair partially matches an existing
 *           batch (e.g. one exists paired with a different value for the other).
 *           Fix the pair in config.json — or clear both to auto-generate.
 *
 * What it saves to data.json:
 *   "file_uploads": [
 *     { "file_id": "....", "filename": "....", "status": "Uploading",
 *       "user_batch_id": "....", "batch_name": "...." }, ...
 *   ]
 */

const fs = require("fs");
const path = require("path");
const {
  BASE_URL, UPLOADS_DIR, loadConfig, apiKey, findLocalPdfs, buildHeadersAuthOnly,
  saveValue, getValue, showResponse, logUrlError, logOther, getBatchFields,
} = require("./helper");

// The upload result blocks live in different places depending on the status:
//   200 -> body.data.details
//   207 -> body.error.details
function extractDetailBlocks(body) {
  const data = body.data || {};
  const err = body.error || {};
  return data.details || err.details || [];
}

async function main() {
  const cfg = loadConfig();
  const key = apiKey();
  const description = cfg.description || "";
  // Enforce the "both or neither" rule locally so we don't send a bad pair.
  const { userBatchId, batchName } = getBatchFields(cfg);

  const pdfPaths = findLocalPdfs();

  if (pdfPaths.length === 0) {
    console.log("[X] No PDF files found to upload.");
    console.log("    Add your PDF file(s) here, then run this again:");
    console.log("      " + path.resolve(UPLOADS_DIR));
    console.log("    (Copy or move your .pdf files into that uploads/ folder.)");
    console.log("    Already have files in S3 / Google Drive, or a signed URL?");
    console.log("    Use signed URLs instead:  node 1_upload_from_url.js");
    return;
  }

  const ENDPOINT = `${BASE_URL}/files/upload/`;

  // Friendly one-liner so the user can see which batch the files are heading to.
  if (userBatchId && batchName) {
    console.log(
      `Uploading ${pdfPaths.length} file(s) into batch ` +
      `'${batchName}' (user_batch_id: ${userBatchId}) ...`
    );
  } else {
    console.log(`Uploading ${pdfPaths.length} file(s) (batch will be auto-generated) ...`);
  }
  for (const p of pdfPaths) {
    console.log("   - " + path.basename(p));
  }

  // Build multipart/form-data. The 'files' field is repeated once per file.
  // fetch sets the multipart boundary itself from the FormData — don't set Content-Type.
  const form = new FormData();
  for (const p of pdfPaths) {
    const bytes = fs.readFileSync(p);
    const blob = new Blob([bytes], { type: "application/pdf" });
    form.append("files", blob, path.basename(p));
  }
  // Non-file form fields — only include what the user actually set.
  if (description) {
    form.append("description", description);
  }
  if (userBatchId && batchName) {
    form.append("user_batch_id", userBatchId);
    form.append("batch_name", batchName);
  }

  const response = await fetch(ENDPOINT, {
    method: "POST",
    headers: buildHeadersAuthOnly(key),
    body: form,
  });

  const body = await showResponse(response);

  if (response.status === 409) {
    // The batch pair partially matches an existing batch — user has to fix config.
    console.log("\n[Conflict] The user_batch_id / batch_name pair doesn't match an existing batch.");
    console.log("           See the response above for the exact reason.");
    console.log("           Fix it in config.json: use the matching partner value, pick a fresh");
    console.log("           unique pair, or clear BOTH fields to have them auto-generated.");
    logOther(409, "Batch pair conflict on direct upload", body);
    return;
  }

  // Treat 200 and 207 as "we got results worth reading".
  if ((response.status === 200 || response.status === 207) && body) {
    const fileUploads = getValue("file_uploads", []);
    const failed = [];

    for (const block of extractDetailBlocks(body)) {
      for (const item of block.successful_uploads || []) {
        if (item.file_id) {
          const saved = {
            file_id: item.file_id,
            filename: item.filename,
            status: item.status || "Uploading",
          };
          // The server echoes back the batch the file was placed in.
          // Save it so the user can see it in data.json without checking config.
          if (item.user_batch_id) saved.user_batch_id = item.user_batch_id;
          if (item.batch_name) saved.batch_name = item.batch_name;
          fileUploads.push(saved);
        }
      }
      for (const item of block.failed_uploads || []) {
        failed.push(item);
      }
    }

    if (fileUploads.length > 0) {
      saveValue("file_uploads", fileUploads);
      console.log("\n[OK] Uploaded files (status will be 'Uploading' at first):");
      for (const f of fileUploads) {
        let line = `   - file_id: ${f.file_id}  |  ${f.filename}  |  status: ${f.status}`;
        if (f.batch_name) line += `  |  batch: ${f.batch_name}`;
        console.log(line);
      }
      console.log("\nNext: run  node 2_check_upload.js");
    } else {
      console.log("\n[!] No files were accepted. See the failures below.");
    }

    if (failed.length > 0) {
      console.log("\n[!] Some files failed (logged to errors.json):");
      for (const f of failed) {
        // direct-upload failures carry 'filename' (not 'url').
        const name = f.filename || "";
        console.log(`   - file: ${name}`);
        console.log(`     reason: ${f.detail}`);
        // Reuse the url_errors section; pass the filename as the reference value.
        logUrlError(name, response.status, f.detail || "", f);
      }
    }
  } else {
    console.log(
      "\n[X] Upload request failed. Check your api_key, the files in uploads/, " +
        "and the status code above."
    );
    // whole-request failure (non-2xx) -> errors.json
    logOther(response.status, "Direct file upload request failed", body);
  }
}

main();
