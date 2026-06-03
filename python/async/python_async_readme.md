# Python (async) — AOD-API

This folder contains **6 ready-to-run async Python files**, one for each API step, plus a shared `helper.py`. They do exactly the same thing as the sync version, but use **`httpx`** with `asyncio`, so the "check" steps (2, 4, 6) check many files/jobs/reports **at the same time** — faster when you have a lot of them.

You set your **API key once** in `helper.py`; in the step files you only edit inputs like signed URLs or a file_id.

For the full API reference (every endpoint, request, and response), see the [main README](../../readme.md).

---

## Setup (one time)

1. Make sure **Python 3.8 or newer** is installed. (New to Python? A quick search for "how to install Python" or asking an AI assistant will get you set up in about 10 minutes.)
2. Install the async HTTP library used by these files. In your terminal, inside this folder, run:

   ```bash
   pip install httpx
   ```

3. Open this folder in your editor (e.g. VS Code).
4. Open **`helper.py`** and paste your API key into the `API_KEY` variable at the top:

   ```python
   # ===== EDIT HERE =====
   API_KEY = "aod-xxxxxxxxxxx"   # paste your key from Section 3 of the main README
   ```

That's the only place the key goes. You're now ready to run the steps in order.

---

## The files

| Step | File | What it does |
|------|------|--------------|
| 1 | `1_upload.py`        | Upload your file(s) → save each `file_id` (status starts as `Uploading`) |
| 2 | `2_check_upload.py`  | Check **all** uploads concurrently → update each to `Uploaded` when ready |
| 3 | `3_create_job.py`    | Start processing one file → get a `job_id` |
| 4 | `4_check_job.py`     | Check **all** jobs concurrently → get the tagged-PDF download link |
| 5 | `5_create_report.py` | Request a score report for one file → get a report `job_id` |
| 6 | `6_check_report.py`  | Check **all** reports concurrently → get the score-report PDF download link |

### How values are shared between files

When you run a file, it **prints the result on screen** and **saves the important values into `data.json`** in this folder. The "check" files (steps 2, 4, 6) read from `data.json`, loop through everything, skip anything already finished, and update the rest — so they're safe to run repeatedly until done.

Each file runs through `asyncio.run(main())`, so you start it the normal way: `python <file>`. The API key and Base URL live in `helper.py`; you normally do **not** need to edit anything else in it.

---

## Step 1 — Upload your file(s) → `1_upload.py`

**Edit:** paste your signed URL(s) into the `SIGNED_URLS` list (API key is already set in `helper.py`). *(Need one? See [How to get a signed URL](../../docs/getting-signed-urls.md).)*

```python
# ===== EDIT HERE =====
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

> ⏱️ This endpoint is rate-limited. Sending more URLs means a longer cooldown before your next upload (see the main README, Section 6).

**Next:** run Step 2 to check when they finish uploading.

---

## Step 2 — Check upload status → `2_check_upload.py`

**Edit:** nothing — the API key is already in `helper.py`. The script checks **every** file from Step 1, all at once.

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
FILE_ID = "paste-an-uploaded-file_id-here"
LEVEL   = 1     # 1 or 2
```

**Run:**

```bash
python 3_create_job.py
```

**Result:** a `job_id`, saved to `data.json` under `job_process` with `status: "Queued"`.

> ⏱️ This endpoint is rate-limited based on the number of pages in the file (see the main README, Section 6).

**Next:** check it in Step 4.

---

## Step 4 — Check job & get tagged PDF → `4_check_job.py`

**Edit:** nothing — the script checks **every** job, all at once.

**Run:**

```bash
python 4_check_job.py
```

**Result:** prints the status of each job. When a job is `Completed`, the script saves and prints the **tagged PDF `download_url`**. Jobs already `Completed` are skipped.

> ⏳ The download link expires (see `expires_in_seconds`, e.g. 300 = 5 minutes). Download the PDF soon.

---

## Step 5 — Request a score report → `5_create_report.py`

**Edit:** paste the `file_id` you want a report for.

```python
# ===== EDIT HERE =====
FILE_ID = "paste-a-file_id-here"
```

**Run:**

```bash
python 5_create_report.py
```

**Result:** a **report job_id**, saved to `data.json` under `report_process`.

---

## Step 6 — Get the score report → `6_check_report.py`

**Edit:** nothing — the script checks **every** report, all at once.

**Run:**

```bash
python 6_check_report.py
```

**Result:** prints the status of each report. When `Completed`, the script saves and prints the **score report PDF `download_url`**.

> ⏳ Like the tagged PDF, this link also expires — download it soon before it expire.

---

## Troubleshooting

- **`ModuleNotFoundError: No module named 'httpx'`** — you skipped the install step. Run `pip install httpx`.
- **401 Unauthorized** — your API key is missing, wrong, or has extra spaces. Re-check the `API_KEY` value in `helper.py`.
- **429 Too Many Requests** — you're calling too fast. Wait the `retry-after-sec` seconds shown in the response and try again.
- **A URL failed with "unsupported source"** — only **S3** and **Google Drive** signed URLs are supported.

For the complete list of status codes and error shapes, see Section 9 of the [main README](../../readme.md).
