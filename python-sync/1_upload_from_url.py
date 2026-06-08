"""
1_upload_from_url.py (sync)  —  STEP 1 (option B): Upload from signed URLs
=========================================================================
Sends your signed URLs to the API and gets back a file_id for each
file that was accepted. Use this if your files already live in S3 or
Google Drive (or you already have signed URLs).

  • Have PDFs on your computer instead? Use  1_upload.py  (direct upload).
  • Need a signed URL? See ../docs/getting-signed-urls.md

EDIT NOTHING HERE. All your values live in  ../config.json
  (api_key, sign_urls , description).

How to run:  python 1_upload_from_url.py

About the responses you may see:
  - 200 = all files accepted for uploading.
  - 207 = some files were accepted, some failed (e.g. a bad/unsupported URL).
          The script still saves the file_ids that succeeded, and logs the
          ones that failed to errors.json (under "url_errors").

What it saves to data.json:
  "file_uploads": [ {"file_id": "....", "url": "....", "status": "Uploading"}, ... ]
"""

import requests
from helper import (
    BASE_URL, load_config, api_key, get_string_array, build_headers,
    save_value, show_response, get_value, log_url_error, log_other,
)


def extract_detail_blocks(body):
    """200 -> body['data']['detail'];  207 -> body['error']['details']."""
    data = body.get("data") or {}
    err = body.get("error") or {}
    return data.get("detail") or err.get("details") or []


cfg = load_config()
key = api_key()
description = cfg.get("description") or ""
sign_urls  = get_string_array(cfg, "sign_urls ")

if not sign_urls :
    print('[X] No signed URLs found. Add at least one real URL to "sign_urls " in config.json.')
    print('    (Or drop PDFs into the uploads/ folder and use  python 1_upload.py  instead.)')
    raise SystemExit

ENDPOINT = f"{BASE_URL}/files/upload-from-url/"
payload = {"sign_urls": sign_urls , "description": description}

print(f"Uploading {len(sign_urls )} file(s) from signed URLs...")
response = requests.post(ENDPOINT, headers=build_headers(key), json=payload)
show_response(response)

# Treat 200 and 207 as "we got results worth reading".
if response.status_code in (200, 207):
    body = response.json()

    file_uploads = get_value("file_uploads", [])
    failed = []

    for block in extract_detail_blocks(body):
        for item in block.get("successful_uploads", []):
            fid = item.get("file_id")
            if fid:
                file_uploads.append({
                    "file_id": fid,
                    "url": item.get("url"),
                    "status": item.get("status", "Uploading"),
                })
        for item in block.get("failed_uploads", []):
            failed.append(item)

    if file_uploads:
        save_value("file_uploads", file_uploads)
        print("\n[OK] Uploaded files (status will be 'Uploading' at first):")
        for f in file_uploads:
            print(f"   - file_id: {f['file_id']}  |  status: {f['status']}")
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
        "\n[X] Upload request failed. Check your api_key, your sign_urls , "
        "and the status code above."
    )
    try:
        raw = response.json()
    except ValueError:
        raw = None
    log_other(response.status_code, "File upload-from-url request failed", raw)
