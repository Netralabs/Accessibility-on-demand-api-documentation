<a id="top"></a>

# AOD-API — Accessibility On Demand API

> The Accessibility On Demand API lets you make PDFs accessible: upload a PDF, get back a tagged (accessibility-enhanced) version, and generate an axes4 accessibility score for the tagged PDF.

This guide is written so that **anyone** - can call these APIs , Just follow the steps in order. The API works the same way no matter which programming language you use.

---

## Table of Contents

1. [What is this API?](#1-what-is-this-api)
2. [Before you start (what you need)](#2-before-you-start-what-you-need)
3. [How to get your API Key](#3-how-to-get-your-api-key)
4. [Where to put your API Key](#4-where-to-put-your-api-key)
5. [List of all APIs (what each one does)](#5-list-of-all-apis-what-each-one-does)
6. [How to call the APIs (pick your language)](#6-how-to-call-the-apis-pick-your-language)
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

The Accessibility On Demand API helps you turn ordinary PDF files into accessible ones that people using screen readers and other assistive tools can read properly. You upload a PDF, the API adds the accessibility tags for you, and you can download the tagged version back. You can also ask the API for an **axes4 accessibility score**, which tells you how accessible the tagged PDF is.

- **Base URL:** `https://staging.api.accessibilityondemand.space/api`
  *(This is the web address all the APIs live under. Every call starts with this, followed by the specific endpoint — for example `https://staging.api.accessibilityondemand.space/api/file-upload`.)*
- **Environment:** This is the **staging** (testing) environment.
- **Authentication:** Bearer token (an API key you send with every request).
- **Data format:** JSON (a simple text format for sending and receiving data).

[⬆ Back to top](#top)

---

## 2. Before you start (what you need)

To call this API , you need two things:

1. **A way to run code** in the language of your choice — Python, Node.js, Java, or .NET. Pick whichever you're comfortable with.
2. **A code editor or terminal** to edit and run the files — for example, VS Code or your system's built-in terminal.

> 💡 **New to this?** Installing a language and a code editor is a one-time setup that takes about 10–15 minutes. There are plenty of free, up-to-date guides for it — a quick search like "how to install Python" (or Node.js / Java / .NET) or asking an AI assistant will get you set up. Pick whichever resource (article, video, or official docs) suits you best.

This guide focuses on **how to call the API**. Once your chosen language is installed, you're ready to go.

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

```
Authorization: Bearer YOUR_API_KEY_HERE
```

Example:

```
Authorization: Bearer aod-xxxxxxxxxxx
```

Breaking that down:
- `Authorization` is the name of the header.
- `Bearer` must be written exactly as shown, followed by **one space**.
- `aod-xxxxxxxxxxx` is your actual API key (the one you copied in Section 3).

You don't need to set this up by hand — the ready-made files in each language folder do it for you. You only have to paste your key in **one place** (the `===== EDIT HERE =====` section at the top of each file), and the rest is handled automatically.

[⬆ Back to top](#top)

---

## 5. List of all APIs (what each one does)

| # | Method | Endpoint (add after Base URL) | What it does |
|---|--------|-------------------------------|--------------|
| 1 | POST   | `/file-upload`                | Starts a file upload. You send **signed_urls** in the payload, and it returns the **file_ids** of the uploaded URLs. |
| 2 | GET    | `/file-upload/{file_id}`      | Returns the upload **status** (`Uploading` / `Uploaded`) for the given file_id. |
| 3 | POST   | `/jobs`                       | Sends an uploaded PDF for processing. Takes a successfully uploaded **file_id** and a **level** (1 or 2). Returns a **job_id**. |
| 4 | GET    | `/jobs/{job_id}`              | Returns the processing **status** and a **link to the tagged PDF**. |
| 5 | POST   | `/report`                     | Requests an axes4 score report. Takes a **file_id** and returns a **job_id** for the report. |
| 6 | GET    | `/report/{job_id}`            | Returns the report **status** and a **link to the generated score report PDF** for the file. |

[⬆ Back to top](#top)

---

## 6. How to call the APIs (pick your language)

The flow is the same in every language. To make it easy, each language has its **own folder** in this repository with **6 ready-to-run files** — one per step. You only edit a clearly marked section at the top of each file (your API key and inputs); the rest runs by itself.

| Language | Folder | Status |
|----------|--------|--------|
| Python   | [`/python`](python) | ✅ Available |
| Node.js  | [`/node`](node)     | 🔜 Coming soon |
| Java     | [`/java`](java)     | 🔜 Coming soon |
| .NET     | [`/dotnet`](dotnet) | 🔜 Coming soon |

### The flow (same for every language)

1. **Upload** your file(s) → get a `file_id` for each (status starts as `Uploading`).
2. **Check upload** → repeat until the status is `Uploaded`.
3. **Create a job** with a `file_id` and a level (1 or 2) → get a `job_id`.
4. **Check the job** → when `Completed`, get the tagged-PDF download link.
5. **Request a report** with a `file_id` → get a report `job_id`.
6. **Check the report** → when `Completed`, get the score-report PDF download link.

### How the ready-made files work

- Each file has a section marked **`===== EDIT HERE =====`** at the top. That's the **only** part you change — your API key and your inputs.
- Running a file **prints the result on screen** AND **saves the important values** (file_ids, job_ids, and their status) into a shared **`data.json`** file in that folder.
- The "check" files (steps 2, 4, 6) automatically **loop through everything saved**, skip anything already finished, and update the rest. They are safe to run again and again until everything is done.

Here is roughly what `data.json` looks like after a few steps:

```json
{
  "file_uploads": [
    { "file_id": "aaa950240561cd149157e054", "status": "Uploaded" }
  ],
  "job_process": [
    {
      "file_id": "aaa950240561cd149157e054",
      "job_id": "job_123",
      "status": "Completed",
      "details": { "download_url": "...", "expires_in_seconds": 300 }
    }
  ],
  "report_process": [
    { "file_id": "aaa950240561cd149157e054", "job_id": "rep_123", "status": "queued" }
  ]
}
```

> 📂 **Open your language's folder and follow its own README** for the exact commands to run each file. The API behaves identically regardless of language — see [Section 7](#7-full-examples-for-every-endpoint-curl--responses) for the raw requests and responses.

> ⏳ **Download links expire** (see `expires_in_seconds`, e.g. 300 = 5 minutes). Download the file promptly, or re-run the matching "check" file to get a fresh link.

[⬆ Back to top](#top)

---

## 7. Full examples for every endpoint (curl + responses)

This section shows the **raw request and response** for each API, using `curl` (a command-line tool available on Mac, Linux, and Windows). Use it to understand exactly what each endpoint expects and returns — useful for debugging or for calling the API in any language.

In every example, replace `aod-xxxxxxxxxxx` with your API key.

> ℹ️ **About error messages:** where a `message` shows options separated by `/`, it means the API returns **one** of those messages depending on the situation — not all of them at once. Common errors that can occur on **any** endpoint (401, 422, 429, 500, etc.) are listed once at the [end of this section](#common-errors-all-endpoints), so they aren't repeated for every endpoint.

Jump to an endpoint:

- [Endpoint 1 — Upload files](#endpoint-1--upload-files)
- [Endpoint 2 — Check upload status](#endpoint-2--check-upload-status)
- [Endpoint 3 — Start a processing job](#endpoint-3--start-a-processing-job)
- [Endpoint 4 — Check job & get tagged PDF](#endpoint-4--check-job--get-tagged-pdf)
- [Endpoint 5 — Request a score report](#endpoint-5--request-a-score-report)
- [Endpoint 6 — Get the score report](#endpoint-6--get-the-score-report)
- [Common errors (all endpoints)](#common-errors-all-endpoints)

---

### Endpoint 1 — Upload files

`POST /file-upload`

Starts uploading one or more files from signed URLs. Returns a `file_id` for each accepted file.

> ⏱️ **Rate limit:** 1 request per second per user. In addition, the cooldown after a request equals the **number of signed URLs** you send (number of URLs = number of seconds to wait). For example, sending 5 URLs means waiting about 5 seconds before the next call.

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

[⬆ Back to top](#top)

---

### Endpoint 2 — Check upload status

`GET /file-upload/{file_id}`

Returns whether a file has finished uploading.

**Request**

```bash
curl -X GET "https://staging.api.accessibilityondemand.space/api/file-upload/aaa950240561cd149157e054" \
  -H "Authorization: Bearer aod-xxxxxxxxxxx"
```

**Success — `200 OK`** (still uploading)

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

**Success — `200 OK`** (finished)

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
    "message": "File id 6a1950240561cd149157e05 is not a valid id",
    "details": []
  },
  "request_id": "cc2200c3-c07a-4709-a107-5d0a4dd5886e",
  "timestamp": "2026-05-29T12:17:03.273158+00:00"
}
```

**No file_id in path — `405 Method Not Allowed`**

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

[⬆ Back to top](#top)

---

### Endpoint 3 — Start a processing job

`POST /jobs`

Sends an uploaded file for tagging. Returns a `job_id`.

> ⏱️ **Rate limit:** 1 request per second per user. In addition, the cooldown depends on the **number of pages** in the file, divided by 10. For example, a 100-page file gives a cooldown of about 10 seconds (100 ÷ 10).
>
> *(This divisor may change if the backend logic is updated.)*

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

[⬆ Back to top](#top)

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

[⬆ Back to top](#top)

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

[⬆ Back to top](#top)

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

[⬆ Back to top](#top)

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

**Rate limit exceeded — `429 Too Many Requests`** (you sent requests too quickly)

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": [
      {
        "retry-after-sec": 39
      }
    ]
  },
  "request_id": "f1045cbb-5c6c-4944-8684-65e8c1e23fc8",
  "timestamp": "2026-05-29T13:21:45.489020+00:00"
}
```

This applies mainly to **`POST /file-upload`** and **`POST /jobs`** (see their rate-limit notes above). The `retry-after-sec` value tells you how many seconds to wait before trying again. *(Rate limits may change if the backend logic is updated.)*

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

When something goes wrong, the API sends back a **status code** and a message. Here are the ones you may see.

| Code | Meaning | What to do |
|------|---------|------------|
| 200  | Success | Everything worked |
| 207  | Partial success | Some files succeeded, some failed — check `failed_uploads` |
| 400  | Bad request | Check your payload — a field is missing or wrong |
| 401  | Unauthorized | Your API key is missing, wrong, or expired |
| 403  | Forbidden | Your key is valid but not allowed to do this |
| 404  | Not found | The ID or endpoint doesn't exist — check spelling |
| 405  | Method not allowed | Wrong method, or a required path value (like a file_id) is missing |
| 409  | Conflict | A conflict, such as reprocessing something already in progress |
| 422  | Validation error | Your request body failed validation — check the `details` |
| 429  | Too many requests | You're calling too fast — wait the `retry-after-sec` seconds |
| 500  | Server error | Problem on our side — try again later |

Every error response follows the same shape:

```json
{
  "success": false,
  "error": { "code": "...", "message": "...", "details": [] },
  "request_id": "...",
  "timestamp": "..."
}
```

When contacting support, include the `request_id` — it lets us find your exact request.

[⬆ Back to top](#top)

---

## 9. FAQ

**Q: I get a 401 error. Why?**
Your API key is wrong or not pasted correctly. Re-check your key (Section 4) and make sure there are no extra spaces and that it starts with `Bearer `.

**Q: Which languages are supported?**
Python is available now in the [`/python`](python) folder. Node.js, Java, and .NET are coming — each will have its own folder with the same 6 files. The API works the same in any language; see [Section 7](#7-full-examples-for-every-endpoint-curl--responses) for the raw requests and responses you can translate into any language.

**Q: My download link stopped working.**
Download links expire after a short time (`expires_in_seconds`). Just re-run the matching "check" step to get a fresh link.

**Q: I keep getting 429 (too many requests).**
You're calling too fast. The upload and job endpoints have a cooldown — wait the number of seconds shown in `retry-after-sec` (or see the rate-limit notes in Section 7) and try again.

**Q: A URL failed with "unsupported source".**
Only **s3** and **gdrive** signed URLs are supported. Make sure your URL comes from one of those sources and hasn't expired.

**Q: Where do I get help?**
Contact [your support email / link] or open an issue on this GitHub repo. Include the `request_id` from the error response.

---

*Last updated: 29-05-2026 · Maintained by aod-tech*