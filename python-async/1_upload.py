"""
1_upload.py (async)  —  STEP 1 (option A): Upload files from your computer
==========================================================================
Uploads every PDF in the repo-root  uploads/  folder directly to the API
(multipart/form-data) and gets back a file_id for each accepted file.
Use this if your PDFs are on your computer and you don't have a cloud account.

  • Files already in S3 / Google Drive (or you have signed URLs)?
    Use  1_upload_from_url.py  instead.

HOW TO USE:
  1. Drop your PDF file(s) into the  uploads/  folder at the repo root.
  2. (Optional) set "description" in ../config.json.
  3. (Optional) set "user_batch_id" + "batch_name" in ../config.json to group
     these files into a specific batch — set BOTH, or leave BOTH blank to have
     the API generate a fresh batch for you. See the README for the pairing rules.
  4. Run:  python 1_upload.py

EDIT NOTHING HERE. All values live in ../config.json.

About the responses you may see:
  - 200 = all files accepted for uploading.
  - 207 = some files were accepted, some failed (e.g. malware detected).
          The script still saves the file_ids that succeeded, and logs the
          ones that failed to errors.json (under "url_errors").
  - 409 = the user_batch_id / batch_name pair partially matches an existing
          batch (e.g. one exists paired with a different value for the other).
          Fix the pair in config.json — or clear both to auto-generate.

What it saves to data.json:
  "file_uploads": [
    { "file_id": "....", "filename": "....", "status": "Uploading",
      "user_batch_id": "....", "batch_name": "...." },  ...
  ]
"""

import os
import asyncio
import httpx
from helper import (
    BASE_URL, load_config, api_key, find_local_pdfs, build_headers_auth_only,
    save_value, show_response, get_value, log_url_error, log_other,
    get_batch_fields, UPLOADS_DIR,
)


def extract_detail_blocks(body):
    """200 -> body['data']['details'];  207 -> body['error']['details']."""
    data = body.get("data") or {}
    err = body.get("error") or {}
    return data.get("details") or err.get("details") or []


async def main():
    cfg = load_config()
    key = api_key()
    description = cfg.get("description") or ""
    # Enforce the "both or neither" rule locally so we don't send a bad pair.
    user_batch_id, batch_name = get_batch_fields(cfg)

    pdf_paths = find_local_pdfs()

    if not pdf_paths:
        print("[X] No PDF files found to upload.")
        print("    Add your PDF file(s) here, then run this again:")
        print(f"      {os.path.abspath(UPLOADS_DIR)}")
        print("    (Copy or move your .pdf files into that uploads/ folder.)")
        print("    Already have files in S3 / Google Drive, or a signed URL?")
        print("    Use signed URLs instead:  python 1_upload_from_url.py")
        return

    endpoint = f"{BASE_URL}/files/upload/"

    # Friendly one-liner so the user can see which batch the files are heading to.
    if user_batch_id and batch_name:
        print(f"Uploading {len(pdf_paths)} file(s) into batch "
              f"'{batch_name}' (user_batch_id: {user_batch_id}) ...")
    else:
        print(f"Uploading {len(pdf_paths)} file(s) (batch will be auto-generated) ...")
    for p in pdf_paths:
        print(f"   - {os.path.basename(p)}")

    # Build the multipart payload: the 'files' field is repeated once per file.
    # Read each file's bytes up front; httpx sends them as multipart/form-data.
    # NOTE: do NOT set Content-Type — httpx adds the multipart boundary itself.
    files_param = []
    for p in pdf_paths:
        with open(p, "rb") as fh:
            files_param.append(("files", (os.path.basename(p), fh.read(), "application/pdf")))

    # Build the non-file form fields. Everything is optional — only include
    # what the user actually set in config.json.
    data_param = {}
    if description:
        data_param["description"] = description
    if user_batch_id and batch_name:
        data_param["user_batch_id"] = user_batch_id
        data_param["batch_name"] = batch_name

    async with httpx.AsyncClient() as client:
        response = await client.post(
            endpoint,
            headers=build_headers_auth_only(key),
            files=files_param,
            data=data_param or None,
        )

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
        log_other(409, "Batch pair conflict on direct upload", raw)
        return

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
                        "filename": item.get("filename"),
                        "status": item.get("status", "Uploading"),
                    }
                    # The server echoes back the batch the file was placed in.
                    # Save it so the user can see it in data.json without checking config.
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
                line = (f"   - file_id: {f['file_id']}  |  {f.get('filename')}"
                        f"  |  status: {f['status']}")
                if f.get("batch_name"):
                    line += f"  |  batch: {f['batch_name']}"
                print(line)
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


if __name__ == "__main__":
    asyncio.run(main())
