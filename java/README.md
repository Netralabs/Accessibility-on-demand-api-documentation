# Java — AOD-API

This folder contains **6 ready-to-run Java files**, one for each API step. The values you edit live in **one shared `config.json` at the repo root** — so every language folder (Java, .NET, Node, Python) reads the same config, and you fill it in **once**. Each `.java` file is self-contained (it includes a small built-in `AOD` helper at the bottom), so you run it directly with `java` — no build tool, no project setup.

**You only ever edit the root `config.json`.** The six step files read every value (API key, signed URLs, file IDs, level) from `../config.json`. They never need editing.

Each step also writes its progress to a **`data.json` inside this `java/` folder** (created automatically) — that file is per-language and you don't touch it.

These files need **one library — Gson** — for reading and writing JSON. It's a single jar you download once.

For the full API reference (every endpoint, request, and response), see the [main README](../readme.md).

---

## Setup (one time)

**1. Check Java 11 or newer is installed** (Java 11+ runs a single `.java` file directly, no compile step):

```bash
java -version
```

(New to Java? A quick search for "how to install Java JDK" will get you set up.)

**2. Download Gson into a `lib` folder — one command, run from this folder.**
It creates the `lib` folder and saves the jar as `lib/gson.jar` for you.

**Mac / Linux:**
```bash
mkdir -p lib && curl -L -o lib/gson.jar https://repo1.maven.org/maven2/com/google/code/gson/gson/2.11.0/gson-2.11.0.jar
```

**Windows (PowerShell):**
```powershell
mkdir lib -Force; curl.exe -L -o lib/gson.jar https://repo1.maven.org/maven2/com/google/code/gson/gson/2.11.0/gson-2.11.0.jar
```

> Prefer to download by hand? Save [this jar](https://repo1.maven.org/maven2/com/google/code/gson/gson/2.11.0/gson-2.11.0.jar) into a new folder named `lib` (in this same directory) and rename it to `gson.jar`.

**3. Open the root `config.json` and fill in your values** (it sits one level up from this `java/` folder — it's the only file you edit; see the next section).

You're now ready to run the steps in order.

### Folder layout

```
your-project/
├── config.json          ← the ONE file you edit (shared by all languages)
├── java/
│   ├── README.md         (this file)
│   ├── config? NO — config is at the root, not here
│   ├── lib/gson.jar      (you download this)
│   ├── Step1Upload.java … Step6CheckReport.java
│   └── data.json         (created automatically when you run a step)
├── dotnet/   …           (reads the same ../config.json, its own data.json)
├── node/     …
└── python/   …
```

---

## The one file you edit — `../config.json` (repo root)

```json
{
  "api_key": "aod-xxxxxxxxxxx",

  "description": "description about batch - optional",

  "signed_urls": [
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
| `description`        | Step 1 | Optional text describing the batch |
| `signed_urls`        | Step 1 | One or more signed URLs. *(Need one? See [How to get a signed URL](../docs/getting-signed-urls.md).)* |
| `process.file_id`    | Step 3 | An **uploaded** `file_id` (from Step 2) to process |
| `process.level`      | Step 3 | `1` or `2` |
| `report.file_id`     | Step 5 | The `file_id` you want a score report for |

You fill these in **as you go** — `signed_urls` before Step 1, `process.file_id` before Step 3, `report.file_id` before Step 5. The steps tell you what to set next.

---

## The files

| Step | File | What it does |
|------|------|--------------|
| 1 | `Step1Upload.java`       | Upload your file(s) → save each `file_id` (status starts as `Uploading`) |
| 2 | `Step2CheckUpload.java`  | Check **all** uploads → update each to `Uploaded` when ready |
| 3 | `Step3CreateJob.java`    | Start processing one file → get a `job_id` |
| 4 | `Step4CheckJob.java`     | Check **all** jobs → get the tagged-PDF download link |
| 5 | `Step5CreateReport.java` | Request a score report for one file → get a report `job_id` |
| 6 | `Step6CheckReport.java`  | Check **all** reports → get the score-report PDF download link |

### How values are shared between files

- **You → the scripts:** through the root **`../config.json`** (the only file you edit — shared by every language).
- **Between scripts:** through **`data.json` inside this `java/` folder**, which the scripts create and update automatically. Each language keeps its own `data.json`, so runs in different languages don't collide. Each step **prints its result on screen** and **saves the important values into `data.json`**. The "check" files (steps 2, 4, 6) read `data.json`, loop through everything, skip anything already finished, and update the rest — so they're safe to run repeatedly until done.

Each file has a small `AOD` helper class at the bottom (Base URL, headers, reads `../config.json`, reads/writes the local `data.json`). You do **not** need to edit it.

---

## How to run

Every file is run the same way. The only OS-specific part is the classpath separator before the jar: **Mac/Linux use `:`, Windows use `;`.**

**Mac / Linux:**
```bash
java -cp ".:lib/gson.jar" Step1Upload.java
```

**Windows:**
```bash
java -cp ".;lib\gson.jar" Step1Upload.java
```

Run them in order, swapping in each filename:

```
Step1Upload.java
Step2CheckUpload.java
Step3CreateJob.java
Step4CheckJob.java
Step5CreateReport.java
Step6CheckReport.java
```

---

## Step-by-step

### Step 1 — Upload your file(s) → `Step1Upload.java`

**In the root `../config.json`:** set `api_key` and add your `signed_urls` (and optionally `description`).

```bash
java -cp ".:lib/gson.jar" Step1Upload.java
```

**Result:** each accepted file is saved to `data.json` with `status: "Uploading"`. If some URLs fail (status **207**), the script lists which ones and why, but still saves the ones that succeeded.

> ⏱️ This endpoint is rate-limited. Sending more URLs means a longer cooldown before your next upload (see the main README, Section 6).

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

**In the root `../config.json`:** set `process.file_id` to an uploaded `file_id`, and `process.level` to `1` or `2`.

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

**Result:** prints the status of each job. When a job is `Completed`, the script saves and prints the **tagged PDF `download_url`**. Jobs already `Completed` are skipped.

> ⏳ The download link expires (see `expires_in_seconds`, e.g. 300 = 5 minutes). Download the PDF soon.

---

### Step 5 — Request a score report → `Step5CreateReport.java`

**In the root `../config.json`:** set `report.file_id` to the file you want a report for.

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

**Result:** prints the status of each report. When `Completed`, the script saves and prints the **score report PDF `download_url`**.

> ⏳ Like the tagged PDF, this link also expires — download it soon or re-run this file for a fresh one.

---

## Troubleshooting

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
