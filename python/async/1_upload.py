"""
1_upload.py (async)  —  STEP 1: Upload your file(s)
===================================================
Sends your signed URLs to the API and gets back a file_id for each
file that was accepted. Run this first.

EDIT NOTHING HERE. All your values live in  ../config.json
  (api_key, signed_urls, description).

How to run:  python 1_upload.py

About the responses you may see:
  - 200 = all files accepted for uploading.
  - 207 = some files were accepted, some failed (e.g. a bad/unsupported URL).
          The script still saves the file_ids that succeeded, and logs the
          ones that failed to errors.json (under "url_errors").

What it saves to data.json:
  "file_uploads": [ {"file_id": "....", "url": "....", "status": "Uploading"}, ... ]
"""

import asyncio
import httpx
from helper import (
    BASE_URL, load_config, api_key, get_string_array, build_headers,
    save_value, show_response, get_value, log_url_error, log_other,
)


def extract_detail_blocks(body):
    """200 -> body['data']['detail'];  207 -> body['error']['details']."""
    data = body.get("data") or {}
    err = body.get("error") or {}
    return data.get("detail") or err.get("details") or []


async def main():
    cfg = load_config()
    key = api_key()
    description = cfg.get("description") or ""
    signed_urls = get_string_array(cfg, "signed_urls")

    if not signed_urls:
        print('[X] No signed URLs found. Add at least one real URL to "signed_urls" in config.json.')
        return

    endpoint = f"{BASE_URL}/file-upload/"
    payload = {"sign_urls": signed_urls, "description": description}

    print(f"Uploading {len(signed_urls)} file(s)...")
    async with httpx.AsyncClient() as client:
        response = await client.post(endpoint, headers=build_headers(key), json=payload)

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
            "\n[X] Upload request failed. Check your api_key, your signed_urls, "
            "and the status code above."
        )
        # whole-request failure (non-2xx) -> errors.json
        try:
            raw = response.json()
        except ValueError:
            raw = None
        log_other(response.status_code, "File-upload request failed", raw)


if __name__ == "__main__":
    asyncio.run(main())
