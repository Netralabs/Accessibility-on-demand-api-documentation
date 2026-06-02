/*
 * 1_upload.js  —  STEP 1: Upload your file(s)
 * ============================================
 * Sends your signed URLs to the API and gets back a file_id for each
 * file that was accepted. Run this first.
 *
 * How to run:  node 1_upload.js
 *
 * About the responses you may see:
 *   - 200 = all files accepted for uploading.
 *   - 207 = some files were accepted, some failed (e.g. a bad/unsupported URL).
 *           The script still saves the file_ids that succeeded and shows you
 *           which URLs failed and why.
 *
 * What it saves to data.json:
 *   "file_uploads": [ { "file_id": "....", "url": "....", "status": "Uploading" }, ... ]
 */

const { BASE_URL, API_KEY, buildHeaders, saveValue, getValue, showResponse } = require("./helper");

const SIGNED_URLS = [ // 👈 paste your signed URL(s) here
  "https://your-signed-url-1",
  "https://your-signed-url-2",
];

const DESCRIPTION = "description about batch - optional"; // 👈 optional text
// ============================================================
// ===== STOP EDITING (the rest runs by itself) =====
// ============================================================

const ENDPOINT = `${BASE_URL}/file-upload`;

const payload = {
  sign_urls: SIGNED_URLS,
  description: DESCRIPTION,
};

// The 'detail' list lives in different places depending on the status:
//   200 -> body.data.detail
//   207 -> body.error.details
function extractDetailBlocks(body) {
  const data = body.data || {};
  const err = body.error || {};
  return data.detail || err.details || [];
}

async function main() {
  console.log("Uploading files...");
  const response = await fetch(ENDPOINT, {
    method: "POST",
    headers: buildHeaders(API_KEY),
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
      console.log("\n[!] Some files failed:");
      for (const f of failed) {
        console.log(`   - URL: ${f.url}`);
        console.log(`     reason: ${f.detail}`);
      }
    }
  } else {
    console.log(
      "\n[X] Upload request failed. Check your API key, your signed URLs, " +
        "and the status code above."
    );
  }
}

main();
