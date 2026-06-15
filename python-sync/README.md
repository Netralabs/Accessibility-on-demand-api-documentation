# Python (sync) — AOD-API

This folder contains **6 ready-to-run Python files**, one for each API step, plus a shared `helper.py`. They use **`requests`** the plain, one-at-a-time way (one request after another) — the simplest setup. (Want the "check" steps to check many files/jobs/reports at once for speed? Use the `python-async/` folder instead — same behavior, using `httpx` + `asyncio`.)

The values you edit live in **one shared [config.json](../config.json) at the repo root** — so every language folder (Java, .NET, Node, Python) reads the same config, and you fill it in **once**.

**You only ever edit the root [config.json](../config.json).** The step files read every value (API key, signed URLs, file IDs, level) from [config.json](../config.json). They never need editing.

Each step also writes its progress to a **`data.json` inside this folder** (created automatically) — that file is per-folder and you don't touch it. Anything that **isn't** a clean success (a 207 partial upload, a non-200 response, or a failed job/report) is kept out of `data.json` and written to a separate **`errors.json`** instead, so your tracked data stays clean.

For the full API reference (every endpoint, request, and response), see the [main README](../../readme.md).

---

## Contents

- [Setup (one time)](#setup-one-time)
- [Folder layout](#folder-layout)
- [The one file you edit — `../config.json`](#the-one-file-you-edit--configjson-repo-root)
- [The files](#the-files)
- [How values are shared between files](#how-values-are-shared-between-files)
- [Errors — `errors.json`](#errors--errorsjson)
- [Paths & commands at a glance](#paths--commands-at-a-glance)
- [Step 1 — Upload your file(s)](#step-1--upload-your-files)
- [Step 2 — Check upload status](#step-2--check-upload-status--2_check_uploadpy)
- [Step 3 — Start processing](#step-3--start-processing--3_create_jobpy)
- [Step 4 — Check job & get tagged PDF](#step-4--check-job--get-tagged-pdf--4_check_jobpy)
- [Step 5 — Request a score report](#step-5--request-a-score-report--5_create_reportpy)
- [Step 6 — Get the score report](#step-6--get-the-score-report--6_check_reportpy)
- [Troubleshooting](#troubleshooting)

---

## Setup (one time)

1. Make sure **Python 3.8 or newer** is installed. (New to Python? A quick search for "how to install Python" will get you set up.)
2. Install the HTTP library used by these files. In your terminal, inside this folder, run:

   ```bash
   pip install requests
   ```

3. **Open [config.json](../config.json) and fill in your values** (it sits one level up from this folder — it's the only file you edit; see below).

You're now ready to run the steps in order.

### Folder layout

```
your-project/
├── config.json          ← the ONE file you edit (shared by all languages)
├── python-sync/
│   ├── README.md         (this file)
│   ├── helper.py         (reads ../config.json, writes data.json + errors.json)
│   ├── 1_upload.py            (direct upload from ../uploads/)
│   ├── 1_upload_from_url.py   (upload from signed URLs)
│   ├── 2_check_upload.py … 6_check_report.py
│   ├── data.json         (created automatically — clean tracked items only)
│   └── errors.json       (created only if something errors — see below)
├── python-async/  …      (same, but uses httpx + asyncio for concurrent checks)
├── java/     …           (reads the same ../config.json, its own data.json)
├── dotnet/   …
└── node/     …
```

---

## The one file you edit — [config.json](../config.json) (repo root)

```json
{
  "api_key": "aod-xxxxxxxxxxx",

  "description": "description about batch - optional",

  "sign_urls": [
    "https://your-signed-url-1",
    "https://your-signed-url-2"
  ],

  "process": {
    "file_id": "",
    "level": 1
  },

  "report": {
    "file_id": ""
  }
}
```

| Field | Used by | What to put |
|-------|---------|-------------|
| `api_key`            | every step | Your key from Section 3 of the main README |
| `description`        | Step 1 | Optional text describing the batch (both upload options) |
| `sign_urls`        | Step 1 (Option B) | One or more signed URLs — only if you use `1_upload_from_url.py`. *(Need one? See [How to get a signed URL](../docs/getting-signed-urls.md).)* |
| `process.file_id`    | Step 3 | An **uploaded** `file_id` (from Step 2) to process |
| `process.level`      | Step 3 | `1` or `2` |
| `report.file_id`     | Step 5 | The `file_id` you want a score report for |

You fill these in **as you go** — `sign_urls` before Step 1 (Option B; for Option A just drop PDFs in `uploads/`), `process.file_id` before Step 3, `report.file_id` before Step 5. The steps tell you what to set next.

---

## The files

| Step | File | What it does |
|------|------|--------------|
| 1A | `1_upload.py`            | **Direct upload** — uploads every PDF in the repo-root `uploads/` folder (status starts as `Uploading`) |
| 1B | `1_upload_from_url.py`   | **Signed-URL upload** — uploads from the `sign_urls` in `config.json` (use one *or* the other, not both) |
| 2 | `2_check_upload.py`  | Check **all** uploads → update each to `Uploaded` when ready |
| 3 | `3_create_job.py`    | Start processing one file → get a `job_id` |
| 4 | `4_check_job.py`     | Check **all** jobs → get the tagged-PDF download link |
| 5 | `5_create_report.py` | Request a score report for one file → get a report `job_id` |
| 6 | `6_check_report.py`  | Check **all** reports → get the score-report PDF download link |

### How values are shared between files

- **You → the scripts:** through the root **`../config.json`** (the only file you edit — shared by every language).
- **Between scripts:** through **`data.json` inside this folder**, which the scripts create and update automatically. Each folder keeps its own `data.json`, so runs in different languages don't collide. Each step **prints its result on screen** and **saves the important values into `data.json`**. The "check" files (steps 2, 4, 6) read `data.json`, loop through everything, skip anything already finished, and update the rest — so they're safe to run repeatedly until done.

The Base URL and all the config-reading + error-logging live in `helper.py`. You normally do **not** need to edit it.

### Errors — `errors.json`

`data.json` only ever holds clean, tracked items. Anything else is written to **`errors.json`** in this folder (created the first time something goes wrong). Entries are **grouped by what they relate to** and **appended** (full history — nothing is overwritten), each with a UTC timestamp:

| Section | What lands here | Carries |
|---------|-----------------|---------|
| `url_errors`  | A signed URL that failed to upload (e.g. a 207 partial upload, "unsupported source") | `url` |
| `file_errors` | A problem tied to a `file_id` (can't check upload, 409 conflict, couldn't start job/report) | `file_id` |
| `job_errors`  | A problem tied to a `job_id` (job or report failed, unreadable response) | `job_id` |
| `other`        | Anything not clearly tied to one of the above (e.g. the whole request failed) | — |

Every entry also has `timestamp_utc` (ISO-8601, e.g. `2025-06-03T10:07:42Z`), `status_code`, a short `message`, and the original `raw` response/detail. Example:

```json
{
  "url_errors": [
    {
      "timestamp_utc": "2025-06-03T10:07:42Z",
      "url": "https://your-signed-url-2",
      "status_code": 207,
      "message": "unsupported source",
      "raw": { "url": "https://your-signed-url-2", "detail": "unsupported source" }
    }
  ],
  "file_errors": [ ],
  "job_errors": [ ],
  "other": [ ]
}
```

Because it's append-only, `errors.json` is a running log — safe to re-run steps, and you can delete the file any time to start a fresh log. (This is the same format and section names the other language folders use, so the files are interchangeable.)

---

## Paths & commands at a glance

Everything below assumes you have **opened a terminal and changed into this folder first**:

```bash
cd python-sync
```

All commands are run from inside `python-sync/`. The three files you care about:

| Purpose | File | Path (from inside `python-sync/`) |
|---------|------|--------------------------------|
| **Edit** your inputs (api_key, sign_urls, file ids, level) | `config.json` | `../config.json` (repo root) |
| **View** your tracked results (file_ids, job_ids, download links) | `data.json` | `./data.json` (this folder) |
| **View** anything that failed (207 / errors / failed jobs) | `errors.json` | `./errors.json` (this folder) |

- To **edit** your values, open `../config.json` (one level up from here).
- To **see results**, open `python-sync/data.json` after running a step.
- To **see failures**, open `python-sync/errors.json` (created only when something goes wrong).

A step is always run the same way — `cd` in first, then run, e.g.:

```bash
python 1_upload.py
```

> 🧭 **Getting `can't open file '1_upload.py'`?** You're in the wrong folder. The step files live inside `python-sync/`. Run `cd python-sync` first (you should see the `1_upload.py` file when you type `ls`).

---

## Step 1 — Upload your file(s)

There are **two ways** to upload — pick the one that fits you. Both save the same thing to `data.json`, so Steps 2–6 are identical afterwards. Run **one** of them.

### Option A — Direct upload from your computer → `1_upload.py`

Best if your PDFs are on your laptop and you don't have a cloud account.

1. Drop your PDF file(s) into the **`uploads/`** folder at the repo root.
2. (Optional) set `description` in [config.json](../config.json).
3. Run:

```bash
python 1_upload.py
```

> 🧭 **Getting `can't open file '1_upload.py'`?** You're in the wrong folder. The step files live inside `python-sync/`. Run `cd python-sync` first (you should see the `1_upload.py` file when you type `ls`).

It automatically picks up **every PDF** in `uploads/` — no file paths to type.

**Result:** each accepted file is saved to `data.json` with `status: "Uploading"`. If some files fail (status **207**, e.g. malware detected), those are logged to `errors.json` under `url_errors`; the successful ones are still saved.

### Option B — Upload from signed URLs → `1_upload_from_url.py`

Best if your files already live in S3 or Google Drive, or you already have signed URLs.

**In [config.json](../config.json):** set `api_key` and add your `sign_urls` (and optionally `description`). *(Need a signed URL? See [How to get a signed URL](../docs/getting-signed-urls.md).)*

```bash
python 1_upload_from_url.py
```

> 🧭 **Getting `can't open file '1_upload_from_url.py'`?** You're in the wrong folder. The step files live inside `python-sync/`. Run `cd python-sync` first (you should see the `1_upload_from_url.py` file when you type `ls`).

**Result:** each accepted file is saved to `data.json` with `status: "Uploading"`. If some URLs fail (status **207**), the failures are written to `errors.json` under `url_errors` (the successful ones are still saved).

> ⏱️ Both uploads are rate-limited. Sending more files/URLs means a longer cooldown before your next upload (see the main README, Section 6).

**Next:** run Step 2 to check when they finish uploading.

---

## Step 2 — Check upload status → `2_check_upload.py`

run below to check status of the files added for uploading — it checks **every** file from Step 1.

```bash
python 2_check_upload.py
```

> 🧭 **Getting `can't open file '2_check_upload.py'`?** You're in the wrong folder. The step files live inside `python-sync/`. Run `cd python-sync` first (you should see the `2_check_upload.py` file when you type `ls`).

**Result:** prints the status of each file. Files already `Uploaded` are skipped; the rest are updated. Re-run until all show `Uploaded`.

**Next:** copy an uploaded `file_id` into `config.json` under `process.file_id`, then run Step 3.

---

## Step 3 — Start processing → `3_create_job.py`

**In the root [config.json](../config.json):** set `process.file_id` to an uploaded `file_id`, and `process.level` to `1` or `2`.

```bash
python 3_create_job.py
```

> 🧭 **Getting `can't open file '3_create_job.py'`?** You're in the wrong folder. The step files live inside `python-sync/`. Run `cd python-sync` first (you should see the `3_create_job.py` file when you type `ls`).

**Result:** a `job_id`, saved to `data.json` under `job_process` with `status: "Queued"`.

> ⏱️ This endpoint is rate-limited based on the number of pages in the file (see the main README, Section 6).

**Next:** check it in Step 4.

---

## Step 4 — Check job & get tagged PDF → `4_check_job.py`

run below to check status of the files added for processing — it checks **every** job.

```bash
python 4_check_job.py
```

> 🧭 **Getting `can't open file '4_check_job.py'`?** You're in the wrong folder. The step files live inside `python-sync/`. Run `cd python-sync` first (you should see the `4_check_job.py` file when you type `ls`).

**Result:** prints the status of each job. When a job is `Completed`, the script saves and prints the **tagged PDF `download_url`**. Jobs already `Completed` are skipped. Any job that comes back `Failed` (or whose response can't be read) is logged to `errors.json` under `job_errors`, not `data.json`.

> ⏳ The download link expires (see `expires_in_seconds`, e.g. 300 = 5 minutes). Download the PDF soon.

---

## Step 5 — Request a score report → `5_create_report.py`

**In the root [config.json](../config.json):** set `report.file_id` to the file you want a report for.

```bash
python 5_create_report.py
```

> 🧭 **Getting `can't open file '5_create_report.py'`?** You're in the wrong folder. The step files live inside `python-sync/`. Run `cd python-sync` first (you should see the `5_create_report.py` file when you type `ls`).

**Result:** a **report job_id**, saved to `data.json` under `report_process`.

---

## Step 6 — Get the score report → `6_check_report.py`

run below to check status of the report being generated — it checks **every** report.

```bash
python 6_check_report.py
```

> 🧭 **Getting `can't open file '6_check_report.py'`?** You're in the wrong folder. The step files live inside `python-sync/`. Run `cd python-sync` first (you should see the `6_check_report.py` file when you type `ls`).

**Result:** prints the status of each report. When `Completed`, the script saves and prints the **score report PDF `download_url`**. A `Failed` report (or unreadable response) is logged to `errors.json` under `job_errors`.

> ⏳ Like the tagged PDF, this link also expires — download it soon before it get expire.

---

## Troubleshooting

- **`can't open file '....py': [Errno 2] No such file or directory`** — you're running from the wrong folder. `cd python-async` first, then run the command (type `ls` — you should see the step files).
- **Where did my failures go?** Anything that wasn't a clean success is in **`errors.json`** (this folder), grouped into `url_errors` / `file_errors` / `job_errors` / `other`, newest appended last. `data.json` only keeps clean items.
- **`config.json was not found at ../config.json`** — run these scripts from inside this folder, with `config.json` sitting in the folder above it (the repo root).
- **`Please set your real "api_key"`** — `api_key` in `config.json` is still the placeholder. Paste your real key.
- **`No signed URLs found` / `No file_id given`** — the matching field in `config.json` is still blank or a placeholder. Fill it in.
- **`ModuleNotFoundError: No module named 'requests'`** — you skipped the install step. Run `pip install requests`.
- **401 Unauthorized** — your API key is missing, wrong, or has extra spaces. Re-check `api_key` in `config.json`.
- **429 Too Many Requests** — you're calling too fast. Wait the `retry-after-sec` seconds shown in the response and try again.
- **A URL failed with "unsupported source"** — only **S3** and **Google Drive** signed URLs are supported.

For the complete list of status codes and error shapes, see Section 9 of the [main README](../../readme.md).
