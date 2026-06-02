"""
2_check_upload.py  —  STEP 2: Check upload status
=================================================
Checks whether a file has finished uploading.
Status will be 'uploading' or 'uploaded'.

How to run:  python 2_check_upload.py
"""

import requests
from helper import BASE_URL,API_KEY, build_headers, get_value, show_response, save_value



def read_status(body):
    """
    Pulls the status out of the GET /file-upload/{file_id} response.
    Tries a few common locations. If your API nests it differently,
    adjust the lines below.
    """
    # direct: {"status": "..."}
    if isinstance(body, dict) and "status" in body:
        return body["status"]
    # nested under data: {"data": {"status": "..."}}
    data = body.get("data") if isinstance(body, dict) else None
    if isinstance(data, dict) and "uploading_status" in data:
        return data["uploading_status"]
    return None


file_uploads = get_value("file_uploads", [])

if not file_uploads:
    print("[X] No files found. Run 1_upload.py first.")
    raise SystemExit

headers = build_headers(API_KEY)
changed = False

print(f"Checking {len(file_uploads)} file(s)...\n")

for entry in file_uploads:
    file_id = entry.get("file_id")
    current = entry.get("status", "")

    # Skip ones already finished.
    if str(current).lower() == "uploaded":
        print(f"   - {file_id}: already uploaded (skipped)")
        continue

    response = requests.get(f"{BASE_URL}/file-upload/{file_id}", headers=headers)

    if response.status_code != 200:
        print(f"   - {file_id}: could not check (status code {response.status_code})")
        continue

    new_status = read_status(response.json()) or "unknown"
    print(f"   - {file_id}: {new_status}")

    # Update only if it has finished uploading.
    if str(new_status).lower() == "uploaded":
        entry["status"] = "uploaded"
        changed = True

# Save back the updated list only if something changed.
if changed:
    save_value("file_uploads", file_uploads)

# Summary.
uploaded = [
    e["file_id"] for e in file_uploads if str(e.get("status", "")).lower() == "uploaded"
]
pending = [
    e["file_id"] for e in file_uploads if str(e.get("status", "")).lower() != "uploaded"
]

print("\nSummary:")
print(f"   uploaded: {len(uploaded)}  |  still uploading: {len(pending)}")

if pending:
    print("Some files are still uploading. Wait a moment and run this file again.")
else:
    print("[OK] All files uploaded. Next: run  python 3_create_job.py")
