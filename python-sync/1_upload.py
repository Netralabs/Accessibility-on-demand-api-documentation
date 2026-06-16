"""
1_upload.py (sync)  —  STEP 1 (option A): Upload files from your computer
=========================================================================
Uploads every PDF in the repo-root  uploads/  folder directly to the API
(multipart/form-data) and gets back a file_id for each accepted file.
Use this if your PDFs are on your computer and you don't have a cloud account.

  • Files already in S3 / Google Drive (or you have signed URLs)?
    Use  1_upload_from_url.py  instead.

HOW TO USE:
  1. Drop your PDF file(s) into the  uploads/  folder at the repo root.
  2. (Optional) set "description" in ../config.json.
  3. Run:  python 1_upload.py

EDIT NOTHING HERE. Your api_key (and optional description) live in ../config.json.

About the responses you may see:
  - 200 = all files accepted for uploading.
  - 207 = some files were accepted, some failed (e.g. a bad/unsupported URL).
          The script still saves the file_ids that succeeded, and logs the
          ones that failed to errors.json (under "url_errors").

What it saves to data.json:
  "file_uploads": [ {"file_id": "....", "filename": "....", "status": "Uploading"}, ... ]
"""

import os
import requests
from helper import (
    BASE_URL, load_config, api_key, find_local_pdfs, build_headers_auth_only,
    save_value, show_response, get_value, log_url_error, log_other, UPLOADS_DIR,
)


def extract_detail_blocks(body):
    """200 -> body['data']['details'];  207 -> body['error']['details']."""
    data = body.get("data") or {}
    err = body.get("error") or {}
    return data.get("details") or err.get("details") or []


cfg = load_config()
key = api_key()
description = cfg.get("description") or ""

pdf_paths = find_local_pdfs()

if not pdf_paths:
    print("[X] No PDF files found to upload.")
    print(f"    Add your PDF file(s) here, then run this again:")
    print(f"      {os.path.abspath(UPLOADS_DIR)}")
    print("    (Copy or move your .pdf files into that uploads/ folder.)")
    print("    Already have files in S3 / Google Drive, or a signed URL?")
    print("    Use signed URLs instead:  python 1_upload_from_url.py")
    raise SystemExit

ENDPOINT = f"{BASE_URL}/files/upload/"

print(f"Uploading {len(pdf_paths)} file(s) from uploads/ ...")
for p in pdf_paths:
    print(f"   - {os.path.basename(p)}")

# Build the multipart payload: the 'files' field is repeated once per file.
# NOTE: do NOT set Content-Type — requests adds the multipart boundary itself.
open_handles = []
try:
    files_param = []
    for p in pdf_paths:
        fh = open(p, "rb")
        open_handles.append(fh)
        files_param.append(("files", (os.path.basename(p), fh, "application/pdf")))

    data_param = {"description": description} if description else None

    response = requests.post(
        ENDPOINT,
        headers=build_headers_auth_only(key),
        files=files_param,
        data=data_param,
    )
finally:
    for fh in open_handles:
        try:
            fh.close()
        except OSError:
            pass

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
                    "filename": item.get("filename"),
                    "status": item.get("status", "Uploading"),
                })
        for item in block.get("failed_uploads", []):
            failed.append(item)

    if file_uploads:
        save_value("file_uploads", file_uploads)
        print("\n[OK] Uploaded files (status will be 'Uploading' at first):")
        for f in file_uploads:
            print(f"   - file_id: {f['file_id']}  |  {f.get('filename')}  |  status: {f['status']}")
        print("\nNext: run  python 2_check_upload.py")
    else:
        print("\n[!] No files were accepted. See the failures below.")

    if failed:
        print("\n[!] Some files failed (logged to errors.json):")
        for f in failed:
            # direct-upload failures carry 'filename' (not 'url').
            name = f.get("filename") or ""
            print(f"   - file: {name}")
            print(f"     reason: {f.get('detail')}")
            # Reuse the url_errors section; pass the filename as the reference value.
            log_url_error(name, response.status_code, f.get("detail") or "", f)
else:
    print(
        "\n[X] Upload request failed. Check your api_key, the files in uploads/, "
        "and the status code above."
    )
    try:
        raw = response.json()
    except ValueError:
        raw = None
    log_other(response.status_code, "Direct file upload request failed", raw)