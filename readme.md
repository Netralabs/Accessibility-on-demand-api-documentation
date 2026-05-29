<a id="top"></a>
# AOD-API — Accessibility On Demand API

> The Accessibility On Demand API lets you make PDFs accessible: upload a PDF, get back a tagged (accessibility-enhanced) version, and generate an accessibility score for the tagged PDF.

This guide is written so that **anyone** — even someone who has never written code — can call these APIs from their own laptop. Just follow the steps in order.

---
## Table of Contents

1. [What is this API?](#1-what-is-this-api)
2. [Before you start (what you need)](#2-before-you-start-what-you-need)
3. [How to get your API Key](#3-how-to-get-your-api-key)
4. [Where to put your API Key](#4-where-to-put-your-api-key)
5. [List of all APIs (what each one does)](#5-list-of-all-apis-what-each-one-does)
6. [How to call the APIs using Python (step by step)](#6-how-to-call-the-apis-using-python-step-by-step)
7. [Full examples for every endpoint (curl + responses)](#7-full-examples-for-every-endpoint-curl--responses)
   - [Endpoint 1 — Upload files](#endpoint-1--upload-files)
   - [Endpoint 2 — Check upload status](#endpoint-2--check-upload-status)
   - [Endpoint 3 — Start a processing job](#endpoint-3--start-a-processing-job)
   - [Endpoint 4 — Check job & get tagged PDF](#endpoint-4--check-job--get-tagged-pdf)
   - [Endpoint 5 — Request a score report](#endpoint-5--request-a-score-report)
   - [Endpoint 6 — Get the score report](#endpoint-6--get-the-score-report)
   - [Common errors (all endpoints)](#common-errors-all-endpoints)
8. [Understanding errors](#8-understanding-errors)
9. [FAQ](#9-faq)

---

## 1. What is this API?

The Accessibility On Demand API helps you turn ordinary PDF files into accessible ones that people using screen readers and other assistive tools can read properly. You upload a PDF, the API adds the accessibility tags for you, and you can download the tagged version back. You can also ask the API for an axes4 accessibility score, which tells you how accessible the tagged PDF is.

- **Base URL:** `https://staging.api.accessibilityondemand.space/api`
  *(This is the web address all the APIs live under. Every call starts with this, followed by the specific endpoint — for example `https://staging.api.accessibilityondemand.space/api/file-upload`.)*
- **Authentication:** Bearer token (an API key you send with every request)
- **Data format:** JSON (a simple text format for sending and receiving data)

---
## 2. Before you start (what you need)

To call this API from your laptop, you'll need a few basic things set up. You don't need to be a programmer — just have these ready:

1. **A way to run code on your computer.** In this guide we use **Python** (version 3.8 or newer), a popular and beginner-friendly language.
2. **A package installer** to add small helper tools. For Python this is **pip**, which comes bundled with Python automatically.
3. **A code editor or terminal** to write and run your code — for example, VS Code, or the built-in terminal on your laptop.

> 💡 **New to this?** Setting up Python and a code editor is a one-time task that takes about 10–15 minutes. There are plenty of free, up-to-date guides to walk you through it — a quick search for "how to install Python" or "how to set up VS Code," or asking an AI assistant, will get you there. Pick whichever resource (article, video, or official docs) suits you best.

Once Python is installed and working, you're ready to move on. The rest of this guide focuses on **how to actually call the API** — that's the part we'll teach you in detail.
You need three things installed on your laptop:

| # | Thing | Why | How to check |
|---|-------|-----|--------------|
| 1 | **Python** (version 3.8 or newer) | The language we use to call the API | Open a terminal and type `python --version` |
| 2 | **pip** (comes with Python) | Lets you install helper tools | Type `pip --version` |
| 3 | The **requests** library | Makes calling APIs easy | We install it in Step 6 |

**How to open a terminal:**
- **Windows:** Press the Windows key, type `cmd`, press Enter.
- **Mac:** Press `Cmd + Space`, type `Terminal`, press Enter.

If `python --version` shows an error, download Python from <https://www.python.org/downloads/> and install it (tick the box "Add Python to PATH" during installation).

pip install requests

[⬆ Back to top](#top)
---

## 3. How to get your API Key

An **API Key** is like a password that proves you are allowed to use the API. You send it with every request so the API knows the calls are coming from you.

Follow these steps to generate a key:

1. Go to **<https://app.accessibilityondemand.ai/login>**.
2. Log in with your **Admin** or **Super Admin** account.
3. Open the **User Management** section.
4. Choose who the key is for:
   - **New user:** Add the user first, and allot them sufficient credits to use the API.
   - **Existing user:** Make sure they already have enough credits.
5. On the user's account, click the **three dots (⋮)** and open **Detail**.
6. Click **"Generate API Key"**.
7. A new API key will appear on the screen, looking something like this:
   ```
   aod-xxxxxxxxxxxxxxxxxxxx
   ```
8. **Copy it immediately** (or take a screenshot). This is the token you'll use in the Authorization header.

> ⚠️ **Keep your API key private.** Share it only with the specific user it was created for. Never publish it or post it publicly (on GitHub, social media, screenshots, etc.) — anyone who has the key can use the API as that user and spend their credits.

[⬆ Back to top](#top)
---
## 4. Where to put your API Key

The API key is sent with every request inside something called a **header**, in this exact format:

Authorization: Bearer YOUR_API_KEY_HERE

Example:
Authorization: Bearer aod-xxxxxxxxxxx

Breaking that down:
- `Authorization` is the name of the header.
- `Bearer` must be written exactly as shown, followed by **one space**.
- `aod-xxxxxxxxxxx` is your actual API key (the one you copied in Section 3).

You don't need to set this up by hand — the code examples later in this guide do it for you. You only have to paste your key in **one place** (shown in Section 6), and the rest is handled automatically.

[⬆ Back to top](#top)
---

## 5. List of all APIs (what each one does)

| # | Method | Endpoint (add after Base URL) | What it does |
|---|--------|-------------------------------|--------------|
| 1 | POST   | `/file-upload`                | Starts a file upload. You send **signed_urls** in the payload, and it returns the **file_ids** of the uploaded URLs. |
| 2 | GET    | `/file-upload/{file_id}`      | Returns the upload **status** (`uploading` / `uploaded`) for the given file_id. |
| 3 | POST   | `/jobs`                       | Sends an uploaded PDF for processing. Takes a successfully uploaded **file_id** and a **level** (1 or 2). Returns a **job_id**. |
| 4 | GET    | `/jobs/{job_id}`              | Returns the processing **status** and a **link to the tagged PDF**. |
| 5 | POST   | `/report`                     | Requests an axes4 score report. Takes a **file_id** and returns a **job_id** for the report. |
| 6 | GET    | `/report/{job_id}`            | Returns the report **status** and a **link to the generated score report PDF** for the file. |

**Quick meaning of the two words:**
- **GET** = "Give me information." (You usually send nothing extra.)
- **POST** = "Here is some data, please save/process it." (You send a payload — see below.)

A **payload** (also called the "request body") is the data you send with a POST request, written in JSON.

[⬆ Back to top](#top)

---

## 6. How to call the APIs using Python (step by step)

In this section we call the APIs using **Python**. To keep things simple, each API has its **own ready-made file** in this repository, inside the `python/` folder:

| Step | File | What it does |
|------|------|--------------|
| 1 | `python/1_upload.py`        | Upload your file(s) → get **file_ids** (status starts as *Uploading*) |
| 2 | `python/2_check_upload.py`  | Check **all** uploads → update each to *uploaded* when ready |
| 3 | `python/3_create_job.py`    | Start processing one file → get a **job_id** |
| 4 | `python/4_check_job.py`     | Check **all** jobs → get the **tagged PDF** download link |
| 5 | `python/5_create_report.py` | Request a score report for one file → get a **report job_id** |
| 6 | `python/6_check_report.py`  | Check **all** reports → get the **score report PDF** download link |

### How it works (read this once)

- Each file has a clearly marked section at the top called **`# ===== EDIT HERE =====`**. That's the **only** part you change.
- When you run a file, it **prints the full result on screen** AND **saves the important values into a shared file called `data.json`** in the same folder.
- Values are saved as lists that also track a **status**, for example:
  - `file_uploads` → `[{ "file_id", "status" }, ...]`
  - `job_process` → `[{ "file_id", "job_id", "status", "details" }, ...]`
  - `report_process` → `[{ "file_id", "job_id", "status", "details" }, ...]`
- The "check" steps (2, 4, 6) automatically **loop through every item** in these lists, **skip anything already finished**, and **update the status** of the rest. You can run them again and again until everything is done.

### One-time setup

1. Make sure you've installed Python and the `requests` library (a quick search or AI assistant can guide you — see Section 2).
2. Open the `python/` folder.
3. Open **each** file and paste your API key into the `API_KEY` variable at the top:

```python
   # ===== EDIT HERE =====
   API_KEY = "aod-xxxxxxxxxxx"   # 👈 paste your key from Section 3
```

You're now ready to run the steps in order.

---

### Step 1 — Upload your file(s) → `python/1_upload.py`

**What to edit:** your API key, and paste your signed URL(s) into the `SIGNED_URLS` list.

```python
# ===== EDIT HERE =====
API_KEY = "aod-xxxxxxxxxxx"
SIGNED_URLS = [
    "https://your-signed-url-1",
    "https://your-signed-url-2",
]
DESCRIPTION = "description about batch - optional"
```

**Run it** (in your terminal, inside the `python/` folder):

```bash
python 1_upload.py
```

**What you get:** each accepted file is saved to `data.json` with `status: "Uploading"`. If some URLs fail (status **207**), the script lists which ones and why, but still saves the ones that succeeded.
**Next:** run Step 2 to check when they finish uploading.

---

### Step 2 — Check upload status → `python/2_check_upload.py`

**What to edit:** only your API key. The script checks **every** file from Step 1.

```python
# ===== EDIT HERE =====
API_KEY = "aod-xxxxxxxxxxx"
```

**Run it:**

```bash
python 2_check_upload.py
```

**What you get:** the status of each file. Files already `uploaded` are skipped; the rest are updated. Re-run until all show `uploaded`.
**Next:** once a file is `uploaded`, use its `file_id` in Step 3.

---

### Step 3 — Start processing → `python/3_create_job.py`

**What to edit:** paste the `file_id` you want to process, and choose the **level** (1 or 2).

```python
# ===== EDIT HERE =====
API_KEY = "aod-xxxxxxxxxxx"
FILE_ID = "paste-an-uploaded-file_id-here"
LEVEL   = 1     # 1 or 2
```

**Run it:**

```bash
python 3_create_job.py
```

**What you get:** a `job_id`, saved to `data.json` under `job_process` with `status: "queued"`.
**Next:** check it in Step 4.

---

### Step 4 — Check job & get tagged PDF → `python/4_check_job.py`

**What to edit:** only your API key. The script checks **every** job.

```python
# ===== EDIT HERE =====
API_KEY = "aod-xxxxxxxxxxx"
```

**Run it:**

```bash
python 4_check_job.py
```

**What you get:** the status of each job. When a job is `Completed`, the script saves and prints the **tagged PDF `download_url`**. Jobs already `Completed`/`Failed` are skipped.

> ⏳ **The download link expires** (see `expires_in_seconds`, e.g. 300 = 5 minutes). Download the PDF soon

---

### Step 5 — Request a score report → `python/5_create_report.py`

**What to edit:** paste the `file_id` you want a report for.

```python
# ===== EDIT HERE =====
API_KEY = "aod-xxxxxxxxxxx"
FILE_ID = "paste-a-file_id-here"
```

**Run it:**

```bash
python 5_create_report.py
```

**What you get:** a **report job_id**, saved to `data.json` under `report_process`.

---

### Step 6 — Get the score report → `python/6_check_report.py`

**What to edit:** only your API key. The script checks **every** report.

```python
# ===== EDIT HERE =====
API_KEY = "aod-xxxxxxxxxxx"
```

**Run it:**

```bash
python 6_check_report.py
```

**What you get:** the status of each report. When `Completed`, the script saves and prints the **score report PDF `download_url`**.

> ⏳ Like the tagged PDF, this link also expires.

[⬆ Back to top](#top)

---

## 7. Full examples for every endpoint (curl + responses)

This section shows the **raw request and response** for each API, using `curl` (a command-line tool available on Mac, Linux, and Windows). Use it to understand exactly what each endpoint expects and returns — useful for debugging or for calling the API in any language.

In every example, replace `aod-xxxxxxxxxxx` with your API key.

> ℹ️ **About error messages:** where a `message` shows options separated by `/`, it means the API returns **one** of those messages depending on the situation — not all of them at once. Common errors that can occur on **any** endpoint (401, 422, 500, etc.) are listed once at the [end of this section](#common-errors-all-endpoints), so they aren't repeated for every endpoint.

---

- [Endpoint 1 — Upload files](#endpoint-1--upload-files)
- [Endpoint 2 — Check upload status](#endpoint-2--check-upload-status)
- [Endpoint 3 — Start a processing job](#endpoint-3--start-a-processing-job)
- [Endpoint 4 — Check job & get tagged PDF](#endpoint-4--check-job--get-tagged-pdf)
- [Endpoint 5 — Request a score report](#endpoint-5--request-a-score-report)
- [Endpoint 6 — Get the score report](#endpoint-6--get-the-score-report)
- [Common errors (all endpoints)](#common-errors-all-endpoints)

### Endpoint 1 — Upload files

`POST /file-upload`

Starts uploading one or more files from signed URLs. Returns a `file_id` for each accepted file.

> ⏱️ **Rate limit:** 1 request per second per user. In addition, the cooldown after a request equals the **number of signed URLs** you send (number of URLs = number of seconds to wait). For example, sending 5 URLs means waiting ~5 seconds before the next call.

**Request**

```bash
curl -X POST "https://staging.api.accessibilityondemand.space/api/file-upload" \
  -H "Authorization: Bearer aod-xxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "signed_urls": [
      "https://your-signed-url-1",
      "https://your-signed-url-2"
    ],
    "description": "description about batch - optional"
  }'
```

**Success — `200 OK`** (all files accepted)

```json
{
  "success": true,
  "data": {
    "code": "SUCCESS",
    "message": "All batch uploading started.",
    "detail": [
      {
        "successful_uploads": [
          {
            "success": true,
            "file_id": "aaa950240561cd149157e054",
            "url": "my url",
            "status": "Uploading"
          }
        ]
      }
    ]
  },
  "message": "Files accepted for uploading, file upload started",
  "request_id": "beb7d0c9-52ae-48af-a1b9-3d4a1b1cbca7",
  "timestamp": "2026-05-29T08:14:02.465082+00:00"
}
```

**Partial success — `207 Multi-Status`** (some files succeeded, some failed)

```json
{
  "success": false,
  "error": {
    "code": "PARTIAL_SUCCESS",
    "message": "Some files uploaded successfully, some had errors",
    "details": [
      {
        "successful_uploads": [
          {
            "success": true,
            "file_id": "aaa950240561cd149157e054",
            "url": "url1",
            "status": "Uploading"
          }
        ],
        "failed_uploads": [
          {
            "url": "url2",
            "status": 400,
            "detail": "Unable to download from the provided URL. Supported sources: s3, gdrive. Please provide a URL from one of these sources."
          },
          {
            "url": "url3",
            "status": 400,
            "detail": "Access denied or URL expired"
          },
          {
            "url": "url4",
            "status": 400,
            "detail": "Malicious file detected"
          }
        ]
      }
    ]
  },
  "request_id": "a00e457c-ba20-4d05-afb8-82b34cc6dbf1",
  "timestamp": "2026-05-29T08:16:45.095922+00:00"
}
```

**Failed — `400 Bad Request`** (all files failed)

```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "All batch uploads failed.",
    "details": [
      {
        "field": "url1",
        "message": "some error"
      },
      {
        "field": "url2",
        "message": "Unsupported content type: text/plain"
      }
    ]
  },
  "request_id": "a00e457c-ba20-4d05-afb8-82b34cc6dbf1",
  "timestamp": "2026-05-29T08:16:45.095922+00:00"
}
```

**Field explanations**

| Field | Meaning |
|-------|---------|
| `success` | `true` if every file was accepted; `false` if any failed |
| `data.detail` / `error.details` | List of upload result blocks (success uses `data.detail`, partial uses `error.details`) |
| `successful_uploads[].file_id` | The ID you use in later steps. **Save this.** |
| `successful_uploads[].status` | Always `Uploading` at this point |
| `failed_uploads[].url` | The URL that could not be used |
| `failed_uploads[].detail` | Why it failed (e.g. unsupported source — only s3 / gdrive allowed) |
| `request_id` | Unique ID for this request — quote it if contacting support |

---

### Endpoint 2 — Check upload status

`GET /file-upload/{file_id}`

Returns whether a file has finished uploading.

**Request**

```bash
curl -X GET "https://staging.api.accessibilityondemand.space/api/file-upload/aaa950240561cd149157e054" \
  -H "Authorization: Bearer aod-xxxxxxxxxxx"
```

**Success — `200 OK`**

```json
{
    "success": true,
    "data": {
        "file_id": "aaa950240561cd149157e054",
        "uploading_status": "Uploading",
        "uploading_error": null
    },
    "message": null,
    "request_id": "e1bd07bf-e78c-4913-aedd-7e4ec9dd9187",
    "timestamp": "2026-05-29T08:40:24.134330+00:00"
}
```

**Success — `200 OK`**

```json
{
    "success": true,
    "data": {
        "file_id": "aaa950240561cd149157e054",
        "uploading_status": "Uploaded",
        "uploading_error": null
    },
    "message": null,
    "request_id": "e1bd07bf-e78c-4913-aedd-7e4ec9dd9187",
    "timestamp": "2026-05-29T08:40:24.134330+00:00"
}
```

**Not Found — `404 Not Found`**

```json
{
    "success": false,
    "error": {
        "code": "NOT_FOUND",
        "message": "File id 6a1950240561cd149157e05 is not valid id",
        "details": []
    },
    "request_id": "cc2200c3-c07a-4709-a107-5d0a4dd5886e",
    "timestamp": "2026-05-29T12:17:03.273158+00:00"
}
```

**if not send file_id in path — `405 Method Not Allowed`**

```json
{
    "success": false,
    "error": {
        "code": "HTTP_ERROR",
        "message": "Method Not Allowed",
        "details": []
    },
    "request_id": "b61cc546-3ec5-4bc3-9991-f977ec468ba1",
    "timestamp": "2026-05-29T12:18:28.702943+00:00"
}
```

**Field explanations**

| Field | Meaning |
|-------|---------|
| `data.file_id` | The file being checked |
| `data.uploading_status` | `Uploading` while in progress, `Uploaded` when finished |
| `data.uploading_error` | `null` if no error, otherwise the reason the upload failed |

---

### Endpoint 3 — Start a processing job

`POST /jobs`

Sends an uploaded file for tagging. Returns a `job_id`.

> ⏱️ **Rate limit:** 1 request per second per user. In addition, the cooldown depends on the **number of pages** in the file, divided by 10. For example, a 100-page file gives a cooldown of about 10 seconds (100 ÷ 10). 

**Request**

```bash
curl -X POST "https://staging.api.accessibilityondemand.space/api/jobs" \
  -H "Authorization: Bearer aod-xxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "aaa950240561cd149157e054",
    "level": 1
  }'
```

**Success — `200 OK`**


```json
{
  "success": true,
  "data": {
    "job_id": "...."
  },
  "request_id": "....",
  "timestamp": "2026-05-29T09:00:00.000000+00:00"
}
```

**Field explanations**

| Field | Meaning |
|-------|---------|
| `file_id` (request) | An uploaded file's ID |
| `level` (request) | Processing level: `1` or `2` |
| `data.job_id` | The job's ID — use it to check status in the next step |

---

### Endpoint 4 — Check job & get tagged PDF

`GET /jobs/{job_id}`

Returns the job status and, when finished, a download link for the tagged PDF.

**Request**

```bash
curl -X GET "https://staging.api.accessibilityondemand.space/api/jobs/JOB_ID_HERE" \
  -H "Authorization: Bearer aod-xxxxxxxxxxx"
```

**Success — `200 OK`**

```json
{
  "success": true,
  "data": {
    "status": "Completed",
    "details": {
      "download_url": "downloading url",
      "expires_in_seconds": 300
    }
  },
  "message": null,
  "request_id": "57c29386-0b78-4ad5-88d2-f3eb9c18cffb",
  "timestamp": "2026-05-29T10:24:48.968985+00:00"
}
```

**Error** (`success: false`)

```json
{
  "success": false,
  "error": {
    "code": "JOB_FAILED",
    "detail": "Reason the job could not be completed"
  },
  "request_id": "....",
  "timestamp": "2026-05-29T10:25:00.000000+00:00"
}
```

**Field explanations**

| Field | Meaning |
|-------|---------|
| `data.status` | e.g. `Processing`, `Completed`, `Failed` |
| `data.details.download_url` | Link to download the tagged PDF (only when `Completed`) |
| `data.details.expires_in_seconds` | How long the link stays valid (e.g. 300 = 5 minutes) |
| `error.code` / `error.detail` | Present only on failure |

---

### Endpoint 5 — Request a score report

`POST /report`

Requests an axes4 accessibility score report for a file. Returns a report `job_id`.

**Request**

```bash
curl -X POST "https://staging.api.accessibilityondemand.space/api/report" \
  -H "Authorization: Bearer aod-xxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "aaa950240561cd149157e054"
  }'
```

**Success — `200 OK`**

> ⚠️ **Please confirm the exact shape** (assumed same as `/jobs`):

```json
{
  "success": true,
  "data": {
    "job_id": "...."
  },
  "request_id": "....",
  "timestamp": "2026-05-29T11:00:00.000000+00:00"
}
```

**Field explanations**

| Field | Meaning |
|-------|---------|
| `file_id` (request) | The file to score |
| `data.job_id` | The report job's ID — check it in the next step |

---

### Endpoint 6 — Get the score report

`GET /report/{job_id}`

Returns the report status and, when ready, a download link for the score report PDF.

**Request**

```bash
curl -X GET "https://staging.api.accessibilityondemand.space/api/report/JOB_ID_HERE" \
  -H "Authorization: Bearer aod-xxxxxxxxxxx"
```

**Success — `200 OK`**

> ⚠️ **Please confirm** (assumed same shape as `/jobs/{job_id}`):

```json
{
  "success": true,
  "data": {
    "status": "Completed",
    "details": {
      "download_url": "score report pdf url",
      "expires_in_seconds": 300
    }
  },
  "request_id": "....",
  "timestamp": "2026-05-29T11:30:00.000000+00:00"
}
```

**Field explanations**

| Field | Meaning |
|-------|---------|
| `data.status` | e.g. `Processing`, `Completed`, `Failed` |
| `data.details.download_url` | Link to download the score report PDF (only when `Completed`) |
| `data.details.expires_in_seconds` | How long the link stays valid |

---

<a id="common-errors-all-endpoints"></a>

### Common errors (all endpoints)

These errors can be returned by **any** endpoint. They all follow the same shape — only the `code` and `message` change. The `message` may be any one of the variations listed.

**Validation error — `422 Unprocessable Entity`** (something in your request is invalid)

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "signed_urls",
        "message": "Field required"
      }
    ]
  },
  "request_id": "baff5eab-8a02-4c89-a940-2e2b1761faaa",
  "timestamp": "2026-05-26T13:41:03.776502+00:00"
}
```

Possible `details[].message` values include: *Field required*, *Input should be a valid list*, *Duplicate URLs detected — the list must contain unique URLs*, or *Invalid or empty JSON body*.

**Unauthorized — `401 Unauthorized`** (your API key is missing or wrong)

```json
{
  "success": false,
  "error": {
    "code": "HTTP_ERROR",
    "message": "Missing or invalid API key",
    "details": []
  },
  "request_id": "8950daa9-b3ad-4458-b14a-49177cd2d609",
  "timestamp": "2026-05-28T04:54:50.914863+00:00"
}
```

Possible `message` values include: *Invalid authorization header*, *Authorization header missing*, or *Missing or invalid API key*.

*(rate limit may change if backend logic is updated.)*
**Rate limit exceeded — `429 Too Many Requests`** (you sent requests too quickly)

```json
{
  "success": false,
  "error": {
    "code": "HTTP_ERROR",
    "message": "Rate limit exceeded",
    "details": []
  },
  "request_id": "1256e103-fd91-4043-9d8d-804924af6d1c",
  "timestamp": "2026-05-26T13:42:51.502796+00:00"
}
```

This applies mainly to **`POST /file-upload`** and **`POST /jobs`** (see their rate-limit notes above). If you hit this, wait the required number of seconds and try again.

**Server error — `500 Internal Server Error`** (problem on our side)

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Something went wrong while processing your request. Please try again later.",
    "details": []
  },
  "request_id": "8395e1ed-dc42-4a97-b53b-ad03b64b0729",
  "timestamp": "2026-05-27T08:18:45.211417+00:00"
}
```

For a `500`, wait a moment and try again. If it keeps happening, contact support with the `request_id`.

[⬆ Back to top](#top)

---

## 8. Understanding errors

When something goes wrong, the API sends back a **status code** and a message.

| Code | Meaning | What to do |
|------|---------|------------|
| 200  | Success | Everything worked |
| 201  | Created | Your POST saved successfully |
| 207  | Partial Success | Some succcess some failed |
| 400  | Bad request | Check your payload — a field is missing or wrong |
| 401  | Unauthorized | Your API key is missing, wrong, or expired |
| 403  | Forbidden | Your key is valid but not allowed to do this |
| 404  | Not found | The ID or endpoint doesn't exist — check spelling |
| 409  | Conflict | some conflict like reprocess old |
| 429  | Too many requests | You're calling too fast — wait a bit |
| 500  | Server error | Problem on our side — try again later |

**Tip:** Always print `response.status_code` to see what happened.

```python
if response.status_code == 200:
    print("Worked! Here is the data:")
    print(response.json())
else:
    print("Something went wrong:", response.status_code)
    print(response.text)
```

---

## 9. FAQ

**Q: I get a 401 error. Why?**
Your API key is wrong or not pasted correctly. Re-check Step 6 and make sure there are no extra spaces.

**Q: "ModuleNotFoundError: No module named 'requests'"**
You skipped the install step. Run `pip install requests` in your terminal.

**Q: Can I use a language other than Python?**
Yes — examples for Java, JavaScript, and cURL are coming in the `examples/` folder. Python is documented first.

**Q: Where do I get help?**
Contact [your support email / link] or open an issue on this GitHub repo.

---

*Last updated: [date] · Maintained by [your name/team]*