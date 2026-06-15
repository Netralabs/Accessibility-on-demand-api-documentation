# Java — AOD-API

This folder contains **6 ready-to-run Java files**, one for each API step. The values you edit live in **one shared `config.json` at the repo root** — so every language folder (Java, .NET, Node, Python) reads the same config, and you fill it in **once**. Each `.java` file is self-contained (it includes a small built-in `AOD` helper at the bottom), so you run it directly with `java` — no build tool, no project setup.

**You only ever edit the root `config.json`.** The six step files read every value (API key, signed URLs, file IDs, level) from [config.json](../config.json). They never need editing.

Each step also writes its progress to a **`data.json` inside this `java/` folder** (created automatically) — that file is per-language and you don't touch it. Anything that **isn't** a clean success (a 207 partial upload, a non-200 response, or a failed job/report) is kept out of `data.json` and written to a separate **`errors.json`** instead, so your tracked data stays clean.

These files need **one library — Gson** — for reading and writing JSON. It's a single jar you download once.

For the full API reference (every endpoint, request, and response), see the [main README](../readme.md).

---

## Contents

- [Setup (one time)](#setup-one-time)
- [Folder layout](#folder-layout)
- [The one file you edit — `../config.json`](#the-one-file-you-edit--configjson-repo-root)
- [The files](#the-files)
- [How values are shared between files](#how-values-are-shared-between-files)
- [Errors — `errors.json`](#errors--errorsjson)
- [Paths & commands at a glance](#paths--commands-at-a-glance)
- [How to run](#how-to-run)
- [Step 1 — Upload your file(s)](#step-1--upload-your-files)
- [Step 2 — Check upload status](#step-2--check-upload-status--step2checkuploadjava)
- [Step 3 — Start processing](#step-3--start-processing--step3createjobjava)
- [Step 4 — Check job & get tagged PDF](#step-4--check-job--get-tagged-pdf--step4checkjobjava)
- [Step 5 — Request a score report](#step-5--request-a-score-report--step5createreportjava)
- [Step 6 — Get the score report](#step-6--get-the-score-report--step6checkreportjava)
- [Troubleshooting](#troubleshooting)

---

## Setup (one time)

**1. Check Java 11 or newer is installed** (Java 11+ runs a single `.java` file directly, no compile step):

```bash
java -version
```

(New to Java? A quick search for "how to install Java JDK" will get you set up.)

**2. Download Gson into a `lib` folder — run these from inside the `java/` folder.**
First `cd` into `java/`, then download. This creates `java/lib/gson.jar`, exactly where the run commands look for it.

**Mac / Linux:**
```bash
cd java
mkdir -p lib && curl -L -o lib/gson.jar https://repo1.maven.org/maven2/com/google/code/gson/gson/2.11.0/gson-2.11.0.jar
```

**Windows (PowerShell):**
```powershell
cd java
mkdir lib -Force; curl.exe -L -o lib/gson.jar https://repo1.maven.org/maven2/com/google/code/gson/gson/2.11.0/gson-2.11.0.jar
```

> Prefer to download by hand? Inside the `java/` folder, create a new folder named `lib`, save [this jar](https://repo1.maven.org/maven2/com/google/code/gson/gson/2.11.0/gson-2.11.0.jar) into it, and rename it to `gson.jar` (so the path is `java/lib/gson.jar`).

**3. Open  [config.json](../config.json) and fill in your values** (it sits one level up from this `java/` folder — it's the only file you edit; see the next section).

You're now ready to run the steps in order.

### Folder layout

```
your-project/
├── config.json          ← the ONE file you edit (shared by all languages)
├── java/
│   ├── README.md         (this file)
│   ├── lib/gson.jar      (you download this)
│   ├── Step1Upload.java        (direct upload from ../uploads/)
│   ├── Step1UploadFromUrl.java (upload from signed URLs)
│   ├── Step2CheckUpload.java … Step6CheckReport.java
│   ├── data.json         (created automatically — clean tracked items only)
│   └── errors.json       (created only if something errors — see below)
├── dotnet/   …           (reads the same ../config.json, its own data.json)
├── node/     …
├── python-sync/   …
└── python-async/  …
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
| `sign_urls`        | Step 1 (Option B) | One or more signed URLs — only if you use `Step1UploadFromUrl.java`. *(Need one? See [How to get a signed URL](../docs/getting-signed-urls.md).)* |
| `process.file_id`    | Step 3 | An **uploaded** `file_id` (from Step 2) to process |
| `process.level`      | Step 3 | `1` or `2` |
| `report.file_id`     | Step 5 | The `file_id` you want a score report for |

You fill these in **as you go** — `sign_urls` before Step 1 (Option B; for Option A just drop PDFs in `uploads/`), `process.file_id` before Step 3, `report.file_id` before Step 5. The steps tell you what to set next.

---

## The files

| Step | File | What it does |
|------|------|--------------|
| 1A | `Step1Upload.java`        | **Direct upload** — uploads every PDF in the repo-root `uploads/` folder (status starts as `Uploading`) |
| 1B | `Step1UploadFromUrl.java` | **Signed-URL upload** — uploads from `sign_urls` in `config.json` (use one *or* the other) |
| 2 | `Step2CheckUpload.java`  | Check **all** uploads → update each to `Uploaded` when ready |
| 3 | `Step3CreateJob.java`    | Start processing one file → get a `job_id` |
| 4 | `Step4CheckJob.java`     | Check **all** jobs → get the tagged-PDF download link |
| 5 | `Step5CreateReport.java` | Request a score report for one file → get a report `job_id` |
| 6 | `Step6CheckReport.java`  | Check **all** reports → get the score-report PDF download link |

### How values are shared between files

- **You → the scripts:** through the root **`../config.json`** (the only file you edit — shared by every language).
- **Between scripts:** through **`data.json` inside this `java/` folder**, which the scripts create and update automatically. Each language keeps its own `data.json`, so runs in different languages don't collide. Each step **prints its result on screen** and **saves the important values into `data.json`**. The "check" files (steps 2, 4, 6) read `data.json`, loop through everything, skip anything already finished, and update the rest — so they're safe to run repeatedly until done.

Each file has a small `AOD` helper class at the bottom (Base URL, headers, reads `../config.json`, reads/writes the local `data.json`, and logs problems to `errors.json`). You do **not** need to edit it.

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
  "file_errors": [
    {
      "timestamp_utc": "2025-06-03T10:09:10Z",
      "file_id": "file_abc",
      "status_code": 409,
      "message": "Conflict - file already processed",
      "raw": { "error": { "code": "CONFLICT" } }
    }
  ],
  "job_errors": [ ],
  "other": [ ]
}
```

Because it's append-only, `errors.json` is a running log — safe to re-run steps, and you can delete the file any time to start a fresh log.

---

## Paths & commands at a glance

Everything below assumes you have **opened a terminal and changed into this folder first**:

```bash
cd java
```

All commands are run from inside `java/`. The three files you care about:

| Purpose | File | Path (from inside `java/`) |
|---------|------|--------------------------------|
| **Edit** your inputs (api_key, sign_urls, file ids, level) | `config.json` | `../config.json` (repo root) |
| **View** your tracked results (file_ids, job_ids, download links) | `data.json` | `./data.json` (this folder) |
| **View** anything that failed (207 / errors / failed jobs) | `errors.json` | `./errors.json` (this folder) |

- To **edit** your values, open [config.json](../config.json) (one level up from here).
- To **see results**, open `java/data.json` after running a step.
- To **see failures**, open `java/errors.json` (created only when something goes wrong).

A step is always run the same way — `cd` in first, then run, e.g.:

```bash
cd java
java -cp ".:lib/gson.jar" Step1Upload.java
```

---

## How to run

First, move into the `java/` folder (do this once, in your terminal):

```bash
cd java
```

Then run each step from there. The only OS-specific part is the classpath separator before the jar: **Mac/Linux use `:`, Windows use `;`.** Run them in order — copy one line at a time.

**Mac / Linux:**

```bash
java -cp ".:lib/gson.jar" Step1Upload.java
java -cp ".:lib/gson.jar" Step1UploadFromUrl.java
java -cp ".:lib/gson.jar" Step2CheckUpload.java
java -cp ".:lib/gson.jar" Step3CreateJob.java
java -cp ".:lib/gson.jar" Step4CheckJob.java
java -cp ".:lib/gson.jar" Step5CreateReport.java
java -cp ".:lib/gson.jar" Step6CheckReport.java
```

**Windows:**

```bash
java -cp ".;lib\gson.jar" Step1Upload.java
java -cp ".;lib\gson.jar" Step1UploadFromUrl.java
java -cp ".;lib\gson.jar" Step2CheckUpload.java
java -cp ".;lib\gson.jar" Step3CreateJob.java
java -cp ".;lib\gson.jar" Step4CheckJob.java
java -cp ".;lib\gson.jar" Step5CreateReport.java
java -cp ".;lib\gson.jar" Step6CheckReport.java
```

> Note: `Step1Upload.java` and `Step1UploadFromUrl.java` are the **two upload options** — run only the one that fits you (see Step 1 below), not both.

> Run one line, wait for it to finish, then run the next. Steps 2, 4, and 6 are safe to re-run until everything shows as finished.

## Step-by-step

### Step 1 — Upload your file(s)

There are **two ways** to upload — pick the one that fits you. Both save the same thing to `data.json`, so Steps 2–6 are identical afterwards. Run **one** of them.

#### Option A — Direct upload from your computer → `Step1Upload.java`

Best if your PDFs are on your laptop and you don't have a cloud account.

1. Drop your PDF file(s) into the **`uploads/`** folder at the repo root.
2. (Optional) set `description` in [config.json](../config.json).
3. Run:

```bash
cd java
```

```bash
java -cp ".:lib/gson.jar" Step1Upload.java
```

It automatically picks up **every PDF** in `uploads/` — no file paths to type. (Windows: use `-cp ".;lib\gson.jar"`.)

**Result:** each accepted file is saved to `data.json` with `status: "Uploading"`. If some files fail (status **207**, e.g. malware detected), those are logged to `errors.json` under `url_errors`; the successful ones are still saved.

#### Option B — Upload from signed URLs → `Step1UploadFromUrl.java`

Best if your files already live in S3 or Google Drive, or you already have signed URLs.

**In [config.json](../config.json):** set `api_key` and add your `sign_urls` (and optionally `description`). *(Need a signed URL? See [How to get a signed URL](../docs/getting-signed-urls.md).)*

```bash
cd java
```

```bash
java -cp ".:lib/gson.jar" Step1UploadFromUrl.java
```

**Result:** each accepted file is saved to `data.json` with `status: "Uploading"`. If some URLs fail (status **207**), the failures are written to `errors.json` under `url_errors` (the successful ones are still saved).

> ⏱️ Both uploads are rate-limited. Sending more files/URLs means a longer cooldown before your next upload (see the main README, Section 6).

**Next:** run Step 2.

---

### Step 2 — Check upload status → `Step2CheckUpload.java`

run below to check status of added for uploading

```bash
java -cp ".:lib/gson.jar" Step2CheckUpload.java
```

**Result:** prints the status of each file. Files already `Uploaded` are skipped; the rest are updated. Re-run until all show `Uploaded`.

**Next:** copy an uploaded `file_id` into `config.json` under `process.file_id`, then run Step 3.

---

### Step 3 — Start processing → `Step3CreateJob.java`

**In the root [config.json](../config.json):** set `process.file_id` to an uploaded `file_id`, and `process.level` to `1` or `2`.

```bash
java -cp ".:lib/gson.jar" Step3CreateJob.java
```

**Result:** a `job_id`, saved to `data.json` under `job_process` with `status: "Queued"`.

> ⏱️ This endpoint is rate-limited based on the number of pages in the file (see the main README, Section 6).

**Next:** check it in Step 4.

---

### Step 4 — Check job & get tagged PDF → `Step4CheckJob.java`

run below to check status of added in processing

```bash
java -cp ".:lib/gson.jar" Step4CheckJob.java
```

**Result:** prints the status of each job. When a job is `Completed`, the script saves and prints the **tagged PDF `download_url`**. Jobs already `Completed` are skipped. Any job that comes back `Failed` (or whose response can't be read) is logged to `errors.json` under `job_errors`, not `data.json`.

> ⏳ The download link expires (see `expires_in_seconds`, e.g. 300 = 5 minutes). Download the PDF soon.

---

### Step 5 — Request a score report → `Step5CreateReport.java`

**In the root [config.json](../config.json):** set `report.file_id` to the file you want a report for.

```bash
java -cp ".:lib/gson.jar" Step5CreateReport.java
```

**Result:** a **report job_id**, saved to `data.json` under `report_process`.

---

### Step 6 — Get the score report → `Step6CheckReport.java`

run below to check status of added in generate report

```bash
java -cp ".:lib/gson.jar" Step6CheckReport.java
```

**Result:** prints the status of each report. When `Completed`, the script saves and prints the **score report PDF `download_url`**. A `Failed` report (or unreadable response) is logged to `errors.json` under `job_errors`.

> ⏳ Like the tagged PDF, this link also expires — download it soon before it get expire.

---

## Troubleshooting

- **Where did my failures go?** Anything that wasn't a clean success is in **`errors.json`** (this folder), grouped into `url_errors` / `file_errors` / `job_errors` / `other`, newest appended last. `data.json` only keeps clean items.
- **`config.json was not found at ../config.json`** — run the command from inside the `java/` folder, with `config.json` sitting in the folder above it (the repo root).
- **`Please set your real "api_key"`** — `api_key` in `config.json` is still the placeholder. Paste your real key.
- **`No signed URLs found` / `No file_id given`** — the matching field in `config.json` is still blank or a placeholder. Fill it in.
- **`error: cannot find symbol` / `package com.google.gson does not exist`** — Gson isn't on the classpath. Make sure `lib/gson.jar` exists and you included `-cp ".:lib/gson.jar"` (Mac/Linux) or `-cp ".;lib\gson.jar"` (Windows).
- **`class found in ... has wrong name`** — don't rename the files; each filename must match its class (e.g. `Step1Upload.java`).
- **`com.google.gson.JsonSyntaxException` reading config.json** — the JSON is malformed (a missing comma or quote). Paste it into any JSON validator to find the spot.
- **401 Unauthorized** — your API key is missing, wrong, or has extra spaces. Re-check `api_key` in `config.json`.
- **429 Too Many Requests** — you're calling too fast. Wait the `retry-after-sec` seconds shown in the response and try again.
- **A URL failed with "unsupported source"** — only **S3** and **Google Drive** signed URLs are supported.

For the complete list of status codes and error shapes, see Section 9 of the [main README](../readme.md).
