/*
 * 1_upload_from_url.js  —  STEP 1 (option B): Upload from signed URLs
 * ==================================================================
 * Sends your signed URLs to the API and gets back a file_id for each
 * file that was accepted. Use this if your files already live in S3 or
 * Google Drive (or you already have signed URLs).
 *
 *   • Have PDFs on your computer instead? Use  1_upload.js  (direct upload).
 *   • Need a signed URL? See ../docs/getting-signed-urls.md
 *
 * EDIT NOTHING HERE. All your values live in  ../config.json
 *   - api_key
 *   - sign_urls
 *   - description (optional)
 *   - user_batch_id + batch_name (optional pair; set BOTH to target a specific
 *     batch, or leave BOTH blank to have the API generate one for you)
 *
 * How to run:  node 1_upload_from_url.js
 *
 * About the responses you may see:
 *   - 200 = all files accepted for uploading.
 *   - 207 = some files were accepted, some failed (e.g. a bad/unsupported URL).
 *           The script still saves the file_ids that succeeded, and logs the
 *           ones that failed to errors.json (under "url_errors").
 *   - 409 = the user_batch_id / batch_name pair partially matches an existing
 *           batch. Fix the pair in config.json — or clear both to auto-generate.
 *
 * What it saves to data.json:
 *   "file_uploads": [
 *     { "file_id": "....", "url": "....", "status": "Uploading",
 *       "user_batch_id": "....", "batch_name": "...." }, ...
 *   ]
 */

const {
  BASE_URL, loadConfig, apiKey, getStringArray, buildHeaders,
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
  // --- read everything from ../config.json ---
  const cfg = loadConfig();
  const key = apiKey();
  const description = cfg.description || "";
  const signedUrls = getStringArray(cfg, "sign_urls");
  // Enforce the "both or neither" rule locally so we don't send a bad pair.
  const { userBatchId, batchName } = getBatchFields(cfg);

  if (signedUrls.length === 0) {
    console.log('[X] No signed URLs found. Add at least one real URL to "sign_urls" in config.json.');
    console.log("    (Or drop PDFs into the uploads/ folder and run  node 1_upload.js  instead.)");
    return;
  }

  const ENDPOINT = `${BASE_URL}/files/upload-from-url/`;

  // Build the JSON body — only include fields the user actually set.
  const payload = { sign_urls: signedUrls };
  if (description) payload.description = description;
  if (userBatchId && batchName) {
    payload.user_batch_id = userBatchId;
    payload.batch_name = batchName;
  }

  if (userBatchId && batchName) {
    console.log(
      `Uploading ${signedUrls.length} file(s) from signed URLs into batch ` +
      `'${batchName}' (user_batch_id: ${userBatchId}) ...`
    );
  } else {
    console.log(
      `Uploading ${signedUrls.length} file(s) from signed URLs (batch will be auto-generated) ...`
    );
  }
  const response = await fetch(ENDPOINT, {
    method: "POST",
    headers: buildHeaders(key),
    body: JSON.stringify(payload),
  });

  const body = await showResponse(response);

  if (response.status === 409) {
    // The batch pair partially matches an existing batch — user has to fix config.
    console.log("\n[Conflict] The user_batch_id / batch_name pair doesn't match an existing batch.");
    console.log("           See the response above for the exact reason.");
    console.log("           Fix it in config.json: use the matching partner value, pick a fresh");
    console.log("           unique pair, or clear BOTH fields to have them auto-generated.");
    logOther(409, "Batch pair conflict on upload-from-url", body);
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
            url: item.url,
            status: item.status || "Uploading",
          };
          // The server echoes back the batch the file was placed in.
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
        let line = `   - file_id: ${f.file_id}  |  status: ${f.status}`;
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
        console.log(`   - URL: ${f.url}`);
        console.log(`     reason: ${f.detail}`);
        // 207 partial-failure item -> errors.json under url_errors
        logUrlError(f.url || "", response.status, f.detail || "", f);
      }
    }
  } else {
    console.log(
      "\n[X] Upload request failed. Check your api_key, your sign_urls, " +
        "and the status code above."
    );
    // whole-request failure (non-2xx) -> errors.json
    logOther(response.status, "File upload-from-url request failed", body);
  }
}

main();
