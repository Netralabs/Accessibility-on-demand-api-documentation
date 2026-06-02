# Node.js — AOD-API

This folder contains **6 ready-to-run Node.js files**, one for each API step, plus a shared `helper.js`. You run them in order. The only thing you edit is the `===== EDIT HERE =====` section at the top of each file.

These files use Node's **built-in `fetch`** and **`fs`** — no packages to install. The "check" steps (2, 4, 6) check many files/jobs/reports **at the same time** (with `Promise.all`) — faster when you have a lot of them.

For the full API reference (every endpoint, request, and response), see the [main README](../readme.md).

---

## Setup (one time)

1. Make sure **Node.js 18 or newer** is installed (`fetch` is built in from Node 18). Check with:

   ```bash
   node --version
   ```

   (New to Node? A quick search for "how to install Node.js" or asking an AI assistant will get you set up in about 10 minutes.)

2. Open this folder in your editor (e.g. VS Code).
3. Open **helper.js** file and paste your API key into the `API_KEY` variable at the top:

   ```javascript
   // ===== EDIT HERE =====
   const API_KEY = "aod-xxxxxxxxxxx"; // paste your key from Section 3 of the main README
   ```

You're now ready to run the steps in order. No `npm install` is needed.

---

## The files

| Step | File | What it does |
|------|------|--------------|
| 1 | `1_upload.js`        | Upload your file(s) → save each `file_id` (status starts as `Uploading`) |
| 2 | `2_check_upload.js`  | Check **all** uploads concurrently → update each to `Uploaded` when ready |
| 3 | `3_create_job.js`    | Start processing one file → get a `job_id` |
| 4 | `4_check_job.js`     | Check **all** jobs concurrently → get the tagged-PDF download link |
| 5 | `5_create_report.js` | Request a score report for one file → get a report `job_id` |
| 6 | `6_check_report.js`  | Check **all** reports concurrently → get the score-report PDF download link |

### How values are shared between files

When you run a file, it **prints the result on screen** and **saves the important values into `data.json`** in this folder. The "check" files (steps 2, 4, 6) read from `data.json`, check everything at once with `Promise.all`, skip anything already finished, and update the rest — so they're safe to run repeatedly until done.

You normally do **not** need to edit `helper.js` — it just holds the Base URL, builds the Authorization header, and reads/writes `data.json`.

---

## Step 1 — Upload your file(s) → `1_upload.js`

**Edit:** your API key, and paste your signed URL(s) into the `SIGNED_URLS` list.

```javascript
// ===== EDIT HERE =====
const SIGNED_URLS = [
  "https://your-signed-url-1",
  "https://your-signed-url-2",
];
const DESCRIPTION = "description about batch - optional";
```

**Run:**

```bash
node 1_upload.js
```

**Result:** each accepted file is saved to `data.json` with `status: "Uploading"`. If some URLs fail (status **207**), the script lists which ones and why, but still saves the ones that succeeded.

> ⏱️ This endpoint is rate-limited. Sending more URLs means a longer cooldown before your next upload (see the main README, Endpoint 1).

**Next:** run Step 2 to check when they finish uploading.

---

## Step 2 — Check upload status → `2_check_upload.js`

**Edit:** only your API key. The script checks **every** file from Step 1, all at once.

```javascript
```

**Run:**

```bash
node 2_check_upload.js
```

**Result:** prints the status of each file. Files already `Uploaded` are skipped; the rest are updated. Re-run until all show `Uploaded`.

**Next:** once a file is `Uploaded`, use its `file_id` in Step 3.

---

## Step 3 — Start processing → `3_create_job.js`

**Edit:** paste the `file_id` you want to process, and choose the **level** (1 or 2).

```javascript
// ===== EDIT HERE =====
const FILE_ID = "paste-an-uploaded-file_id-here";
const LEVEL   = 1;     // 1 or 2
```

**Run:**

```bash
node 3_create_job.js
```

**Result:** a `job_id`, saved to `data.json` under `job_process` with `status: "Queued"`.

> ⏱️ This endpoint is rate-limited based on the number of pages in the file (see the main README, Endpoint 3).

**Next:** check it in Step 4.

---

## Step 4 — Check job & get tagged PDF → `4_check_job.js`

**Edit:** only your API key. The script checks **every** job, all at once.

```javascript
```

**Run:**

```bash
node 4_check_job.js
```

**Result:** prints the status of each job. When a job is `Completed`, the script saves and prints the **tagged PDF `download_url`**. Jobs already `Completed` are skipped.

> ⏳ The download link expires (see `expires_in_seconds`, e.g. 300 = 5 minutes). Download the PDF soon, or re-run this file to get a fresh link.

---

## Step 5 — Request a score report → `5_create_report.js`

**Edit:** paste the `file_id` you want a report for.

```javascript
// ===== EDIT HERE =====
const FILE_ID = "paste-a-file_id-here";
```

**Run:**

```bash
node 5_create_report.js
```

**Result:** a **report job_id**, saved to `data.json` under `report_process`.

---

## Step 6 — Get the score report → `6_check_report.js`

**Edit:** only your API key. The script checks **every** report, all at once.

```javascript
```

**Run:**

```bash
node 6_check_report.js
```

**Result:** prints the status of each report. When `Completed`, the script saves and prints the **score report PDF `download_url`**.

> ⏳ Like the tagged PDF, this link also expires — download it soon before expiry

---

## Troubleshooting

- **`fetch is not defined`** — your Node.js is older than v18. Install Node 18+.
- **401 Unauthorized** — your API key is missing, wrong, or has extra spaces. Re-check the `API_KEY` value.
- **429 Too Many Requests** — you're calling too fast. Wait the `retry-after-sec` seconds shown in the response and try again.
- **A URL failed with "unsupported source"** — only **s3** and **gdrive** signed URLs are supported.

For the complete list of status codes and error shapes, see Section 9 of the [main README](../readme.md).
