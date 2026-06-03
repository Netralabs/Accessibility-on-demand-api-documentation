/*
 * 1_upload.js  —  STEP 1: Upload your file(s)
 * ============================================
 * Sends your signed URLs to the API and gets back a file_id for each
 * file that was accepted. Run this first.
 *
 * EDIT NOTHING HERE. All your values live in  ../config.json
 *   (api_key, signed_urls, description).
 *
 * How to run:  node 1_upload.js
 *
 * About the responses you may see:
 *   - 200 = all files accepted for uploading.
 *   - 207 = some files were accepted, some failed (e.g. a bad/unsupported URL).
 *           The script still saves the file_ids that succeeded, and logs the
 *           ones that failed to errors.json (under "url_errors").
 *
 * What it saves to data.json:
 *   "file_uploads": [ { "file_id": "....", "url": "....", "status": "Uploading" }, ... ]
 */

const {
  BASE_URL, loadConfig, apiKey, getStringArray, buildHeaders,
  saveValue, getValue, showResponse, logUrlError, logOther,
} = require("./helper");

// The 'detail' list lives in different places depending on the status:
//   200 -> body.data.detail
//   207 -> body.error.details
function extractDetailBlocks(body) {
  const data = body.data || {};
  const err = body.error || {};
  return data.detail || err.details || [];
}

async function main() {
  // --- read everything from ../config.json ---
  const cfg = loadConfig();
  const key = apiKey();
  const description = cfg.description || "";
  const signedUrls = getStringArray(cfg, "signed_urls");

  if (signedUrls.length === 0) {
    console.log('[X] No signed URLs found. Add at least one real URL to "signed_urls" in config.json.');
    return;
  }

  const ENDPOINT = `${BASE_URL}/file-upload/`;
  const payload = { sign_urls: signedUrls, description };

  console.log(`Uploading ${signedUrls.length} file(s)...`);
  const response = await fetch(ENDPOINT, {
    method: "POST",
    headers: buildHeaders(key),
    body: JSON.stringify(payload),
  });

  const body = await showResponse(response);

  // Treat 200 and 207 as "we got results worth reading".
  if ((response.status === 200 || response.status === 207) && body) {
    const fileUploads = getValue("file_uploads", []);
    const failed = [];

    for (const block of extractDetailBlocks(body)) {
      for (const item of block.successful_uploads || []) {
        if (item.file_id) {
          fileUploads.push({
            file_id: item.file_id,
            url: item.url,
            status: item.status || "Uploading",
          });
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
        console.log(`   - file_id: ${f.file_id}  |  status: ${f.status}`);
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
      "\n[X] Upload request failed. Check your api_key, your signed_urls, " +
        "and the status code above."
    );
    // whole-request failure (non-2xx) -> errors.json
    logOther(response.status, "File-upload request failed", body);
  }
}

main();
