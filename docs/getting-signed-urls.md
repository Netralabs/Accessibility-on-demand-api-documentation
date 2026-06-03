# How to get a signed URL (S3 or Google Drive)

The AOD API doesn't take a file upload directly. Instead, you give it a **signed URL** — a web link the API can use to download your PDF. Right now the API supports two sources: **Amazon S3** and **Google Drive**.

This guide shows, step by step, how to:
1. Put your PDF in S3 or Google Drive,
2. Get a link the API can use, and
3. Paste that link into the code (the `SIGNED_URLS` list).

You only need **one** of the two methods — pick whichever you already use.

---

## Table of Contents

- [Option A — Amazon S3](#option-a--amazon-s3)
  - [A1. Create a bucket](#a1-create-a-bucket)
  - [A2. Upload your PDF](#a2-upload-your-pdf)
  - [A3. Get a presigned URL](#a3-get-a-presigned-url)
- [Option B — Google Drive](#option-b--google-drive)
  - [B1. Upload your PDF](#b1-upload-your-pdf)
  - [B2. Share it with "anyone with the link"](#b2-share-it-with-anyone-with-the-link)
  - [B3. Turn the share link into a direct link](#b3-turn-the-share-link-into-a-direct-link)
- [Where to paste the URL in the code](#where-to-paste-the-url-in-the-code)
- [Common mistakes](#common-mistakes)

---

## Option A — Amazon S3

You'll need a free [AWS account](https://aws.amazon.com/). All steps below use the **AWS Console** (the website) — no command line needed.

### A1. Create a bucket

A "bucket" is just a folder in S3 where your files live.

1. Sign in to the [AWS Console](https://console.aws.amazon.com/).
2. In the search bar at the top, type **S3** and open the **S3** service.
3. Click **Create bucket**.
4. Give it a **unique name** (e.g. `my-aod-uploads-2026`) and pick a **Region** near you.
5. Leave the default settings (including "Block all public access" — that's fine, because a presigned URL works without making the bucket public).
6. Click **Create bucket** at the bottom.

### A2. Upload your PDF

1. Click the bucket you just created.
2. Click **Upload** → **Add files**.
3. Choose your PDF, then click **Upload**.
4. When it finishes, click the file's name to open its details page.

### A3. Get a presigned URL

A "presigned URL" is a temporary link that lets the API download your file without making it public.

1. On the file's details page, look for the **Object actions** menu (top right).
2. Click **Share with a presigned URL**.
3. Choose how long the link should stay valid (for example, **60 minutes**). Pick enough time to run the upload step.
4. Click **Create presigned URL**. It is copied to your clipboard automatically (or use the **Copy** button).

The link looks something like this (very long):

```
https://my-aod-uploads-2026.s3.amazonaws.com/myfile.pdf?X-Amz-Algorithm=...&X-Amz-Signature=...&X-Amz-Expires=3600
```

That whole string is your signed URL. Keep it handy for the [paste step](#where-to-paste-the-url-in-the-code).

> ⏳ Presigned URLs **expire**. If the upload step fails with an "expired" error, just generate a fresh one and paste it again.

---

## Option B — Google Drive

You only need a normal Google account.

### B1. Upload your PDF

1. Go to [Google Drive](https://drive.google.com/).
2. Click **New** → **File upload**, and choose your PDF.
3. Wait for it to finish uploading.

### B2. Share it with "anyone with the link"

The API can only download the file if the link is open to anyone.

1. Right-click your PDF in Drive and choose **Share**.
2. Under **General access**, change **Restricted** to **Anyone with the link**.
3. Make sure the role is **Viewer**.
4. Click **Copy link**, then **Done**.

The copied link looks like this:

```
https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/view?usp=sharing
```

### B3. Turn the share link into a direct link

> ⚠️ **Important:** the link from the Share button is a "view" link — it opens a preview page, not the file itself. The API needs a **direct download** link. You must convert it.

1. From your copied link, find the **file ID** — it's the long code between `/d/` and `/view`:

   ```
   https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/view?usp=sharing
                                    └──────── this part ────────┘
   ```

   In this example the file ID is `1AbCdEfGhIjKlMnOpQrStUvWxYz`.

2. Put that ID into this template:

   ```
   https://drive.google.com/uc?export=download&id=FILE_ID
   ```

3. So the final, usable link becomes:

   ```
   https://drive.google.com/uc?export=download&id=1AbCdEfGhIjKlMnOpQrStUvWxYz
   ```

That converted link is your signed URL. Use it in the [paste step](#where-to-paste-the-url-in-the-code).

---

## Where to paste the URL in the code

Once you have a link (from S3 or Google Drive), open **Step 1** of your language folder and paste it into the `SIGNED_URLS` list. For example, in Python:

```python
SIGNED_URLS = [
    "https://drive.google.com/uc?export=download&id=1AbCdEfGhIjKlMnOpQrStUvWxYz",
    "https://my-aod-uploads-2026.s3.amazonaws.com/myfile.pdf?X-Amz-Algorithm=...",
]
```

You can mix sources and add as many URLs as you like — one line per file, each in quotes, separated by commas. Then run Step 1 as described in your language's README.

---

## Common mistakes

- **Pasting the Google Drive "view" link instead of the converted direct link.** This is the #1 cause of the "unsupported source" error — see [step B3](#b3-turn-the-share-link-into-a-direct-link).
- **Drive file not shared as "Anyone with the link."** If it's still "Restricted," the API can't reach it.
- **Expired S3 presigned URL.** Generate a fresh one and paste it again.
- **A source other than S3 or Google Drive.** Only those two are supported right now; other cloud platforms are coming soon.
