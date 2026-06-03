# Java — AOD-API

This folder contains **6 ready-to-run Java files**, one for each API step. Each file is self-contained (it includes a small built-in `AOD` helper at the bottom), so you run it directly with `java` — no build tool, no project setup.

These files need **one library — Gson** — for reading and writing JSON. It's a single jar you download once.

For the full API reference (every endpoint, request, and response), see the [main README](../readme.md).

---

## Setup (one time)

1. Make sure **Java 11 or newer** is installed (Java 11+ can run a single `.java` file directly, with no compile step). Check with:

   ```bash
   java -version
   ```

   (New to Java? A quick search for "how to install Java JDK" or asking an AI assistant will get you set up.)

2. **Get the Gson jar.** Download it once from Maven Central:

   <https://repo1.maven.org/maven2/com/google/code/gson/gson/2.11.0/gson-2.11.0.jar>

   Save it inside the `lib` folder and rename it to **`gson.jar`** (so the path is `lib/gson.jar`).

3. Open each file and paste your API key into the `API_KEY` value at the top:

   ```java
   // ===== EDIT HERE =====
   static final String API_KEY = "aod-xxxxxxxxxxx"; // paste your key from Section 3 of the main README
   ```

You're now ready to run the steps in order.

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

When you run a file, it **prints the result on screen** and **saves the important values into `data.json`** in this folder. The "check" files (steps 2, 4, 6) read from `data.json`, loop through everything, skip anything already finished, and update the rest — so they're safe to run repeatedly until done.

Each file has a small `AOD` helper class at the bottom (Base URL, headers, `data.json` read/write). You normally do **not** need to edit it.

---

## How to run

Every file is run the same way. The only tricky part is putting the Gson jar on the "classpath" with `-cp`. Use the form for your operating system:

**Mac / Linux** (colon separator):

```bash
java -cp ".:lib/gson.jar" Step1Upload.java
```

**Windows** (semicolon separator):

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

**Edit:** paste your API key, and the `SIGNED_URLS` array. *(Need one? See [How to get a signed URL](../docs/getting-signed-urls.md).)*

```java
static final String API_KEY = "aod-xxxxxxxxxxx";
static final String[] SIGNED_URLS = {
    "https://your-signed-url-1",
    "https://your-signed-url-2",
};
static final String DESCRIPTION = "description about batch - optional";
```

**Run** (Mac/Linux):

```bash
java -cp ".:lib/gson.jar" Step1Upload.java
```

**Result:** each accepted file is saved to `data.json` with `status: "Uploading"`. If some URLs fail (status **207**), the script lists which ones and why, but still saves the ones that succeeded.

> ⏱️ This endpoint is rate-limited. Sending more URLs means a longer cooldown before your next upload (see the main README, Section 6).

**Next:** run Step 2.

---

### Step 2 — Check upload status → `Step2CheckUpload.java`

**Edit:** only your API key.

```bash
java -cp ".:lib/gson.jar" Step2CheckUpload.java
```

**Result:** prints the status of each file. Files already `Uploaded` are skipped; the rest are updated. Re-run until all show `Uploaded`.

**Next:** once a file is `Uploaded`, use its `file_id` in Step 3.

---

### Step 3 — Start processing → `Step3CreateJob.java`

**Edit:** paste the `file_id` you want to process, and choose the **level** (1 or 2).

```java
static final String API_KEY = "aod-xxxxxxxxxxx";
static final String FILE_ID = "paste-an-uploaded-file_id-here";
static final int LEVEL = 1;     // 1 or 2
```

```bash
java -cp ".:lib/gson.jar" Step3CreateJob.java
```

**Result:** a `job_id`, saved to `data.json` under `job_process` with `status: "Queued"`.

> ⏱️ This endpoint is rate-limited based on the number of pages in the file (see the main README, Section 6).

**Next:** check it in Step 4.

---

### Step 4 — Check job & get tagged PDF → `Step4CheckJob.java`

**Edit:** only your API key.

```bash
java -cp ".:lib/gson.jar" Step4CheckJob.java
```

**Result:** prints the status of each job. When a job is `Completed`, the script saves and prints the **tagged PDF `download_url`**. Jobs already `Completed` are skipped.

> ⏳ The download link expires (see `expires_in_seconds`, e.g. 300 = 5 minutes). Download the PDF soon.

---

### Step 5 — Request a score report → `Step5CreateReport.java`

**Edit:** paste the `file_id` you want a report for.

```java
static final String API_KEY = "aod-xxxxxxxxxxx";
static final String FILE_ID = "paste-a-file_id-here";
```

```bash
java -cp ".:lib/gson.jar" Step5CreateReport.java
```

**Result:** a **report job_id**, saved to `data.json` under `report_process`.

---

### Step 6 — Get the score report → `Step6CheckReport.java`

**Edit:** only your API key.

```bash
java -cp ".:lib/gson.jar" Step6CheckReport.java
```

**Result:** prints the status of each report. When `Completed`, the script saves and prints the **score report PDF `download_url`**.

> ⏳ Like the tagged PDF, this link also expires — download it soon or re-run this file for a fresh one.

---

## Troubleshooting

- **`error: cannot find symbol` / `package com.google.gson does not exist`** — Gson isn't on the classpath. Make sure `lib/gson.jar` exists and you included `-cp ".:lib/gson.jar"` (Mac/Linux) or `-cp ".;lib\gson.jar"` (Windows).
- **`class found in ... has wrong name`** — don't rename the files; each filename must match its class (e.g. `Step1Upload.java`).
- **401 Unauthorized** — your API key is missing, wrong, or has extra spaces. Re-check the `API_KEY` value.
- **429 Too Many Requests** — you're calling too fast. Wait the `retry-after-sec` seconds shown in the response and try again.
- **A URL failed with "unsupported source"** — only **S3** and **Google Drive** signed URLs are supported.

For the complete list of status codes and error shapes, see Section 9 of the [main README](../readme.md).
