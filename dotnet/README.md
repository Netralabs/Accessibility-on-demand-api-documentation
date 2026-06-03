# .NET (C#) — AOD-API

This folder is **one small .NET project** with 6 steps for calling the API. You pick which step to run by passing its name, e.g. `dotnet run -- step1`. You set your **API key once** in `Helper.cs`; in the step files you only edit inputs like signed URLs or a file_id.

Uses the **built-in `HttpClient`** and **`System.Text.Json`** — no NuGet packages to install.

For the full API reference (every endpoint, request, and response), see the [main README](../readme.md).

---

## Setup (one time)

1. Make sure the **.NET SDK 8.0 or newer** is installed. Check with:

   ```bash
   dotnet --version
   ```

   (New to .NET? A quick search for "install .NET SDK" or asking an AI assistant will get you set up.)

2. Open **`Helper.cs`** and paste your API key into the `API_KEY` value at the top:

   ```csharp
   // ===== EDIT HERE =====
   const string API_KEY = "aod-xxxxxxxxxxx"; // paste your key from Section 3 of the main README
   ```

That's the only place the key goes. No `dotnet restore` of extra packages is needed — everything used is built into .NET.

---

## The files

| Step | File | What it does |
|------|------|--------------|
| 1 | `Step1Upload.cs`       | Upload your file(s) → save each `file_id` (status starts as `Uploading`) |
| 2 | `Step2CheckUpload.cs`  | Check **all** uploads → update each to `Uploaded` when ready |
| 3 | `Step3CreateJob.cs`    | Start processing one file → get a `job_id` |
| 4 | `Step4CheckJob.cs`     | Check **all** jobs → get the tagged-PDF download link |
| 5 | `Step5CreateReport.cs` | Request a score report for one file → get a report `job_id` |
| 6 | `Step6CheckReport.cs`  | Check **all** reports → get the score-report PDF download link |

`Program.cs` is a small dispatcher that runs the step you name. `Helper.cs` holds the API key, Base URL, headers, and `data.json` read/write. `aod.csproj` is the project file. You normally do **not** need to edit `Program.cs` or `aod.csproj`.

### How values are shared between files

When you run a step, it **prints the result on screen** and **saves the important values into `data.json`** in this folder. The "check" steps (2, 4, 6) read from `data.json`, loop through everything, skip anything already finished, and update the rest — so they're safe to run repeatedly until done.

---

## How to run

From inside this folder, run a step by name:

```bash
dotnet run -- step1   # upload
dotnet run -- step2   # check upload
dotnet run -- step3   # create job
dotnet run -- step4   # check job
dotnet run -- step5   # create report
dotnet run -- step6   # check report
```

(The `--` tells `dotnet` that what follows is for our program, not for the `dotnet` command itself.)

---

## Step-by-step

(Your API key is already set once in `Helper.cs` — the steps below only mention other inputs.)

### Step 1 — Upload your file(s) → `Step1Upload.cs`

**Edit:** the `SIGNED_URLS` array.

```csharp
static readonly string[] SIGNED_URLS = {
    "https://your-signed-url-1",
    "https://your-signed-url-2",
};
const string DESCRIPTION = "description about batch - optional";
```

**Run:**

```bash
dotnet run -- step1
```

**Result:** each accepted file is saved to `data.json` with `status: "Uploading"`. If some URLs fail (status **207**), the script lists which ones and why, but still saves the ones that succeeded.

> ⏱️ This endpoint is rate-limited. Sending more URLs means a longer cooldown before your next upload (see the main README, Section 6).

**Next:** run Step 2.

---

### Step 2 — Check upload status → `Step2CheckUpload.cs`

**Edit:** nothing.

```bash
dotnet run -- step2
```

**Result:** prints the status of each file. Files already `Uploaded` are skipped; the rest are updated. Re-run until all show `Uploaded`.

**Next:** once a file is `Uploaded`, use its `file_id` in Step 3.

---

### Step 3 — Start processing → `Step3CreateJob.cs`

**Edit:** paste the `file_id` you want to process, and choose the **level** (1 or 2).

```csharp
const string FILE_ID = "paste-an-uploaded-file_id-here";
const int LEVEL = 1;     // 1 or 2
```

```bash
dotnet run -- step3
```

**Result:** a `job_id`, saved to `data.json` under `job_process` with `status: "Queued"`.

> ⏱️ This endpoint is rate-limited based on the number of pages in the file (see the main README, Section 6).

**Next:** check it in Step 4.

---

### Step 4 — Check job & get tagged PDF → `Step4CheckJob.cs`

**Edit:** nothing.

```bash
dotnet run -- step4
```

**Result:** prints the status of each job. When a job is `Completed`, the script saves and prints the **tagged PDF `download_url`**. Jobs already `Completed` are skipped.

> ⏳ The download link expires (see `expires_in_seconds`, e.g. 300 = 5 minutes). Download the PDF soon.

---

### Step 5 — Request a score report → `Step5CreateReport.cs`

**Edit:** paste the `file_id` you want a report for.

```csharp
const string FILE_ID = "paste-a-file_id-here";
```

```bash
dotnet run -- step5
```

**Result:** a **report job_id**, saved to `data.json` under `report_process`.

---

### Step 6 — Get the score report → `Step6CheckReport.cs`

**Edit:** nothing.

```bash
dotnet run -- step6
```

**Result:** prints the status of each report. When `Completed`, the script saves and prints the **score report PDF `download_url`**.

> ⏳ Like the tagged PDF, this link also expires — download it soon, or re-run this step for a fresh one.

---

## Troubleshooting

- **`Couldn't find a project to run`** — run the commands from inside this `dotnet` folder (where `aod.csproj` is).
- **401 Unauthorized** — your API key is missing, wrong, or has extra spaces. Re-check the `API_KEY` value in `Helper.cs`.
- **429 Too Many Requests** — you're calling too fast. Wait the `retry-after-sec` seconds shown in the response and try again.
- **A URL failed with "unsupported source"** — only **S3** and **Google Drive** signed URLs are supported.

For the complete list of status codes and error shapes, see Section 9 of the [main README](../readme.md).
