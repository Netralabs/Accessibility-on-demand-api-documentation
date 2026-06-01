# Python — AOD-API

This folder contains **6 ready-to-run Python files**, one for each API step, plus a shared `helper.py`. You run them in order. The only thing you edit is the `===== EDIT HERE =====` section at the top of each file.

For the full API reference (every endpoint, request, and response), see the [main README](../readme.md).

---

## Setup (one time)

1. Make sure **Python 3.8 or newer** is installed. (New to Python? A quick search for "how to install Python" or asking an AI assistant will get you set up in about 10 minutes.)
2. Install the one helper library used by these files. In your terminal, inside this `python/` folder, run:

   ```bash
   pip install requests
   ```

3. Open this folder in your editor (e.g. VS Code).
4. Open **each** file and paste your API key into the `API_KEY` variable at the top:

   ```python
   # ===== EDIT HERE =====
   API_KEY = "aod-xxxxxxxxxxx"   # paste your key from Section 3 of the main README
   ```

You're now ready to run the steps in order.

---

## The files

| Step | File | What it does |
|------|------|--------------|
| 1 | `1_upload.py`        | Upload your file(s) → save each `file_id` (status starts as `Uploading`) |
| 2 | `2_check_upload.py`  | Check **all** uploads → update each to `Uploaded` when ready |
| 3 | `3_create_job.py`    | Start processing one file → get a `job_id` |
| 4 | `4_check_job.py`     | Check **all** jobs → get the tagged-PDF download link |
| 5 | `5_create_report.py` | Request a score report for one file → get a report `job_id` |
| 6 | `6_check_report.py`  | Check **all** reports → get the score-report PDF download link |

### How values are shared between files

When you run a file, it **prints the result on screen** and **saves the important values into `data.json`** in this folder. The "check" files (steps 2, 4, 6) read from `data.json`, loop through everything, skip anything already finished, and update the rest — so they're safe to run repeatedly until done.

You normally do **not** need to edit `helper.py` — it just holds the Base URL, builds the Authorization header, and reads/writes `data.json`.

---

## Step 1 — Upload your file(s) → `1_upload.py`

**Edit:** your API key, and paste your signed URL(s) into the `SIGNED_URLS` list.

```python
# ===== EDIT HERE =====
API_KEY = "aod-xxxxxxxxxxx"
SIGNED_URLS = [
    "https://your-signed-url-1",
    "https://your-signed-url-2",
]
DESCRIPTION = "description about batch - optional"
```

**Run:**

```bash
python 1_upload.py
```

**Result:** each accepted file is saved to `data.json` with `status: "Uploading"`. If some URLs fail (status **207**), the script lists which ones and why, but still saves the ones that succeeded.

> ⏱️ This endpoint is rate-limited. Sending more URLs means a longer cooldown before your next upload (see the main README, Endpoint 1).

**Next:** run Step 2 to check when they finish uploading.

---

## Step 2 — Check upload status → `2_check_upload.py`

**Edit:** only your API key. The script checks **every** file from Step 1.

```python
# ===== EDIT HERE =====
API_KEY = "aod-xxxxxxxxxxx"
```

**Run:**

```bash
python 2_check_upload.py
```

**Result:** prints the status of each file. Files already `Uploaded` are skipped; the rest are updated. Re-run until all show `Uploaded`.

**Next:** once a file is `Uploaded`, use its `file_id` in Step 3.

---

## Step 3 — Start processing → `3_create_job.py`

**Edit:** paste the `file_id` you want to process, and choose the **level** (1 or 2).

```python
# ===== EDIT HERE =====
API_KEY = "aod-xxxxxxxxxxx"
FILE_ID = "paste-an-uploaded-file_id-here"
LEVEL   = 1     # 1 or 2
```

**Run:**

```bash
python 3_create_job.py
```

**Result:** a `job_id`, saved to `data.json` under `job_process` with `status: "queued"`.

> ⏱️ This endpoint is rate-limited based on the number of pages in the file (see the main README, Endpoint 3).

**Next:** check it in Step 4.

---

## Step 4 — Check job & get tagged PDF → `4_check_job.py`

**Edit:** only your API key. The script checks **every** job.

```python
# ===== EDIT HERE =====
API_KEY = "aod-xxxxxxxxxxx"
```

**Run:**

```bash
python 4_check_job.py
```

**Result:** prints the status of each job. When a job is `Completed`, the script saves and prints the **tagged PDF `download_url`**. Jobs already `Completed` or `Failed` are skipped.

> ⏳ The download link expires (see `expires_in_seconds`, e.g. 300 = 5 minutes). Download the PDF soon, or re-run this file to get a fresh link.

---

## Step 5 — Request a score report → `5_create_report.py`

**Edit:** paste the `file_id` you want a report for.

```python
# ===== EDIT HERE =====
API_KEY = "aod-xxxxxxxxxxx"
FILE_ID = "paste-a-file_id-here"
```

**Run:**

```bash
python 5_create_report.py
```

**Result:** a **report job_id**, saved to `data.json` under `report_process`.

---

## Step 6 — Get the score report → `6_check_report.py`

**Edit:** only your API key. The script checks **every** report.

```python
# ===== EDIT HERE =====
API_KEY = "aod-xxxxxxxxxxx"
```

**Run:**

```bash
python 6_check_report.py
```

**Result:** prints the status of each report. When `Completed`, the script saves and prints the **score report PDF `download_url`**.

> ⏳ Like the tagged PDF, this link also expires — download it soon or re-run this file for a fresh one.

---

## Troubleshooting

- **`ModuleNotFoundError: No module named 'requests'`** — you skipped the install step. Run `pip install requests`.
- **401 Unauthorized** — your API key is missing, wrong, or has extra spaces. Re-check the `API_KEY` value.
- **429 Too Many Requests** — you're calling too fast. Wait the `retry-after-sec` seconds shown in the response and try again.
- **A URL failed with "unsupported source"** — only **s3** and **gdrive** signed URLs are supported.

For the complete list of status codes and error shapes, see Section 8 of the [main README](../readme.md).