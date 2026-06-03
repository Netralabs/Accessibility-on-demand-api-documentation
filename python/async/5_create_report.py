"""
5_create_report.py (async)  —  STEP 5: Request an axes4 score report
====================================================================
Asks the API to generate an axes4 accessibility score report for a file.

EDIT NOTHING HERE. Set this in  ../config.json  under "report":
  "report": { "file_id": "<the file_id to generate a report for>" }

How to run:  python 5_create_report.py

What it saves to data.json:
  "report_process": [ {"file_id": "....", "job_id": "....", "status": "Processing"}, ... ]
"""

import asyncio
import httpx
from helper import BASE_URL, load_config, api_key, build_headers, get_value, save_value, show_response, log_file_error


async def main():
    cfg = load_config()
    key = api_key()
    report = cfg.get("report") or {}
    file_id = str(report.get("file_id", "")).strip()

    if not file_id:
        print('[X] No file_id given. Set "report": {"file_id": ...} in config.json.')
        return

    payload = {"file_id": file_id}

    print(f"Requesting a score report for file_id {file_id} ...")
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/report/", headers=build_headers(key), json=payload)

    show_response(response)

    if response.status_code in (200, 201):
        body = response.json()
        data = body.get("data") or {}
        job_id = data.get("job_id")

        if job_id:
            report_process = get_value("report_process", [])
            if not any(r.get("job_id") == job_id for r in report_process):
                report_process.append({"file_id": file_id, "job_id": job_id, "status": "Processing"})
                save_value("report_process", report_process)
            print("\n[OK] Got report job_id:", job_id)
            print("Next: run  python 6_check_report.py")
        else:
            print("\n[!] Could not find 'job_id' in the response. "
                  "Check the printed response above and update the key name.")
            log_file_error(file_id, response.status_code, "No job_id in report-create response", body)
    else:
        print("\n[X] Could not request the report. Check the file_id and status code above.")
        try:
            raw = response.json()
        except ValueError:
            raw = None
        log_file_error(file_id, response.status_code, "Could not request report", raw)


if __name__ == "__main__":
    asyncio.run(main())
