"""
1_upload.py  —  STEP 1: Upload your file(s)
============================================
Sends your signed URLs to the API and gets back a file_id for each
file that was accepted. Run this first.

How to run:  python 1_upload.py

About the responses you may see:
  - 200 = all files accepted for uploading.
  - 207 = some files were accepted, some failed (e.g. a bad/unsupported URL).
          The script still saves the file_ids that succeeded and shows you
          which URLs failed and why.

What it saves to data.json:
  "file_uploads": [
      {"file_id": "....", "status": "Uploading"},
      ...
  ]
Each accepted file starts with status "Uploading". Step 2 updates these
to "uploaded" once the upload finishes.
"""

import requests
from helper import API_KEY, BASE_URL, build_headers, save_value, show_response, get_value

# ============================================================
# ===== EDIT HERE =====
# ============================================================

SIGNED_URLS = [  # 👈 paste your signed URL(s) here
    "https://your-signed-url-2",
    "https://your-signed-url-2",
]

DESCRIPTION = "description about batch - optional"  # 👈 optional text
# ============================================================
# ===== STOP EDITING (the rest runs by itself) =====
# ============================================================

ENDPOINT = f"{BASE_URL}/file-upload"

payload = {
    "sign_urls": SIGNED_URLS,
    "description": DESCRIPTION,
}


def extract_detail_blocks(body):
    """
    The 'detail' list lives in different places depending on the status:
      - 200 -> body["data"]["detail"]
      - 207 -> body["error"]["details"]
    Returns whichever list is present (or an empty list).
    """
    data = body.get("data") or {}
    err = body.get("error") or {}
    return data.get("detail") or err.get("details") or []


print("Uploading files...")
response = requests.post(ENDPOINT, headers=build_headers(API_KEY), json=payload)
show_response(response)

# Treat 200 and 207 as "we got results worth reading".
if response.status_code in (200, 207):
    body = response.json()

    file_uploads = get_value("file_uploads", [])
    failed = []

    for block in extract_detail_blocks(body):
        for item in block.get("successful_uploads", []):
            fid = item.get("file_id")
            url = item.get("url")
            if fid:
                # store the id with its status ("Uploading" at this point)
                file_uploads.append(
                    {
                        "file_id": fid,
                        "url": url,
                        "status": item.get("status", "Uploading"),
                    }
                )
        for item in block.get("failed_uploads", []):
            failed.append(item)

    # Report what succeeded.
    if file_uploads:
        save_value("file_uploads", file_uploads)
        print("\n[OK] Uploaded files (status will be 'Uploading' at first):")
        for f in file_uploads:
            print(f"   - file_id: {f['file_id']}  |  status: {f['status']}")
        print("\nNext: run  python 2_check_upload.py")
    else:
        print("\n[!] No files were accepted. See the failures below.")

    # Report what failed (only happens on 207).
    if failed:
        print("\n[!] Some files failed:")
        for f in failed:
            print(f"   - URL: {f.get('url')}")
            print(f"     reason: {f.get('detail')}")
else:
    print(
        "\n[X] Upload request failed. Check your API key, your signed URLs, "
        "and the status code above."
    )
