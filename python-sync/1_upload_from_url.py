"""
1_upload_from_url.py (sync)  —  STEP 1 (option B): Upload from signed URLs
=========================================================================
Sends your signed URLs to the API and gets back a file_id for each
file that was accepted. Use this if your files already live in S3 or
Google Drive (or you already have signed URLs).

  • Have PDFs on your computer instead? Use  1_upload.py  (direct upload).
  • Need a signed URL? See ../docs/getting-signed-urls.md

EDIT NOTHING HERE. All your values live in  ../config.json
  - api_key
  - sign_urls
  - description (optional)
  - user_batch_id + batch_name (optional pair; set BOTH to target a specific
    batch, or leave BOTH blank to have the API generate one for you)

How to run:  python 1_upload_from_url.py

About the responses you may see:
  - 200 = all files accepted for uploading.
  - 207 = some files were accepted, some failed (e.g. a bad/unsupported URL).
          The script still saves the file_ids that succeeded, and logs the
          ones that failed to errors.json (under "url_errors").
  - 409 = the user_batch_id / batch_name pair partially matches an existing
          batch. Fix the pair in config.json — or clear both to auto-generate.

What it saves to data.json:
  "file_uploads": [
    { "file_id": "....", "url": "....", "status": "Uploading",
      "user_batch_id": "....", "batch_name": "...." },  ...
  ]
"""

import requests
from helper import (
    BASE_URL, load_config, api_key, get_string_array, build_headers,
    save_value, show_response, get_value, log_url_error, log_other,
    get_batch_fields,
)


def extract_detail_blocks(body):
    """200 -> body['data']['details'];  207 -> body['error']['details']."""
    data = body.get("data") or {}
    err = body.get("error") or {}
    return data.get("details") or err.get("details") or []


cfg = load_config()
key = api_key()
description = cfg.get("description") or ""
sign_urls = get_string_array(cfg, "sign_urls")
# Enforce the "both or neither" rule locally so we don't send a bad pair.
USER_BATCH_ID, BATCH_NAME = get_batch_fields(cfg)

if not sign_urls:
    print('[X] No signed URLs found. Add at least one real URL to "sign_urls" in config.json.')
    print('    (Or drop PDFs into the uploads/ folder and use  python 1_upload.py  instead.)')
    raise SystemExit

ENDPOINT = f"{BASE_URL}/files/upload-from-url/"

# Build the JSON body — only include fields the user actually set.
payload = {"sign_urls": sign_urls}
if description:
    payload["description"] = description
if USER_BATCH_ID and BATCH_NAME:
    payload["user_batch_id"] = USER_BATCH_ID
    payload["batch_name"] = BATCH_NAME

if USER_BATCH_ID and BATCH_NAME:
    print(f"Uploading {len(sign_urls)} file(s) from signed URLs into batch "
          f"'{BATCH_NAME}' (user_batch_id: {USER_BATCH_ID}) ...")
else:
    print(f"Uploading {len(sign_urls)} file(s) from signed URLs (batch will be auto-generated) ...")

response = requests.post(ENDPOINT, headers=build_headers(key), json=payload)
show_response(response)

if response.status_code == 409:
    # The batch pair partially matches an existing batch — user has to fix config.
    print("\n[Conflict] The user_batch_id / batch_name pair doesn't match an existing batch.")
    print("           See the response above for the exact reason.")
    print("           Fix it in config.json: use the matching partner value, pick a fresh")
    print("           unique pair, or clear BOTH fields to have them auto-generated.")
    try:
        raw = response.json()
    except ValueError:
        raw = None
    log_other(409, "Batch pair conflict on upload-from-url", raw)
    raise SystemExit

# Treat 200 and 207 as "we got results worth reading".
if response.status_code in (200, 207):
    body = response.json()

    file_uploads = get_value("file_uploads", [])
    failed = []

    for block in extract_detail_blocks(body):
        for item in block.get("successful_uploads", []):
            fid = item.get("file_id")
            if fid:
                saved = {
                    "file_id": fid,
                    "url": item.get("url"),
                    "status": item.get("status", "Uploading"),
                }
                # The server echoes back the batch the file was placed in.
                if item.get("user_batch_id"):
                    saved["user_batch_id"] = item.get("user_batch_id")
                if item.get("batch_name"):
                    saved["batch_name"] = item.get("batch_name")
                file_uploads.append(saved)
        for item in block.get("failed_uploads", []):
            failed.append(item)

    if file_uploads:
        save_value("file_uploads", file_uploads)
        print("\n[OK] Uploaded files (status will be 'Uploading' at first):")
        for f in file_uploads:
            line = f"   - file_id: {f['file_id']}  |  status: {f['status']}"
            if f.get("batch_name"):
                line += f"  |  batch: {f['batch_name']}"
            print(line)
        print("\nNext: run  python 2_check_upload.py")
    else:
        print("\n[!] No files were accepted. See the failures below.")

    if failed:
        print("\n[!] Some files failed (logged to errors.json):")
        for f in failed:
            print(f"   - URL: {f.get('url')}")
            print(f"     reason: {f.get('detail')}")
            # 207 partial-failure item -> errors.json under url_errors
            log_url_error(f.get("url") or "", response.status_code, f.get("detail") or "", f)
else:
    print(
        "\n[X] Upload request failed. Check your api_key, your sign_urls, "
        "and the status code above."
    )
    try:
        raw = response.json()
    except ValueError:
        raw = None
    log_other(response.status_code, "File upload-from-url request failed", raw)
