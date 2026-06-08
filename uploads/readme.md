# uploads/

Put the **PDF files you want to upload** in this folder.

When you run the **direct upload** step (the "Step 1 — direct upload" file in your
language folder), it automatically picks up **every `.pdf` file in this folder** and
uploads them — you don't type any file paths.

This folder is shared by **all languages** (Python, Node.js, Java, .NET). Whichever
language you use, it reads the PDFs from here.

## How to use

1. Copy or move your PDF file(s) into this folder.
2. Open your language folder (e.g. `python-sync/`, `python-async/`, `node/`, `java/`, or `dotnet/`).
3. Run that folder's **direct-upload** step (Step 1). Each language's README shows the
   exact command — for example `python 1_upload.py`, `node 1_upload.js`,
   `java -cp ".:lib/gson.jar" Step1Upload.java`, or `dotnet run -- step1`.

## Notes

- Only `.pdf` files are uploaded. This `README.md` (and any non-PDF file) is ignored.
- Already have your files in **S3** or **Google Drive**, or have a **signed URL**?
  You don't need this folder — use the *signed-URL* upload step instead. See
  [docs/getting-signed-urls.md](../docs/getting-signed-urls.md).
- This file just keeps the folder in the repository (Git doesn't track empty folders).
  You can leave it here.