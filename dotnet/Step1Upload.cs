/*
 * Step1Upload.cs  —  STEP 1 (option A): Upload files from your computer
 * =====================================================================
 * Uploads every PDF in the repo-root  uploads/  folder directly to the API
 * (multipart/form-data) and gets back a file_id for each accepted file.
 * Use this if your PDFs are on your computer and you don't have a cloud account.
 *
 *   Run:  dotnet run -- step1
 *
 *   • Files already in S3 / Google Drive (or you have signed URLs)?
 *     Use  dotnet run -- step1url  instead.
 *
 * HOW TO USE:
 *   1. Drop your PDF file(s) into the  uploads/  folder at the repo root.
 *   2. (Optional) set "description" in ../config.json.
 *   3. (Optional) set "user_batch_id" + "batch_name" in ../config.json to group
 *      these files into a specific batch — set BOTH, or leave BOTH blank to have
 *      the API generate a fresh batch for you. See the README for the pairing rules.
 *   4. Run:  dotnet run -- step1
 *
 * EDIT NOTHING HERE. All values live in ../config.json.
 *
 * What it saves to data.json:
 *   "file_uploads": [
 *     { "file_id": "....", "filename": "....", "status": "Uploading",
 *       "user_batch_id": "....", "batch_name": "...." }, ...
 *   ]
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

namespace Aod
{
    public static class Step1Upload
    {
        public static async Task RunAsync()
        {
            // --- read everything from ../config.json ---
            JsonObject cfg = Helper.LoadConfig();
            string apiKey = Helper.ApiKey();
            string description = Helper.GetString(cfg, "description", "");
            // Enforce the "both or neither" rule locally so we don't send a bad pair.
            var (userBatchId, batchName) = Helper.GetBatchFields(cfg);

            List<string> pdfPaths = Helper.FindLocalPdfs();

            if (pdfPaths.Count == 0)
            {
                Console.WriteLine("[X] No PDF files found to upload.");
                Console.WriteLine("    Add your PDF file(s) here, then run this again:");
                Console.WriteLine("      " + Path.GetFullPath(Helper.UploadsDir));
                Console.WriteLine("    (Copy or move your .pdf files into that uploads/ folder.)");
                Console.WriteLine("    Already have files in S3 / Google Drive, or a signed URL?");
                Console.WriteLine("    Use signed URLs instead:  dotnet run -- step1url");
                return;
            }

            string endpoint = Helper.BaseUrl + "/files/upload/";

            // Friendly one-liner so the user can see which batch the files are heading to.
            if (userBatchId != null && batchName != null)
                Console.WriteLine($"Uploading {pdfPaths.Count} file(s) into batch "
                    + $"'{batchName}' (user_batch_id: {userBatchId}) ...");
            else
                Console.WriteLine($"Uploading {pdfPaths.Count} file(s) (batch will be auto-generated) ...");
            foreach (var p in pdfPaths)
                Console.WriteLine("   - " + Path.GetFileName(p));

            // Non-file form fields — only include what the user actually set.
            var textFields = new Dictionary<string, string>();
            if (!string.IsNullOrEmpty(description)) textFields["description"] = description;
            if (userBatchId != null && batchName != null)
            {
                textFields["user_batch_id"] = userBatchId;
                textFields["batch_name"] = batchName;
            }

            var response = await Helper.PostMultipartAsync(endpoint, apiKey, pdfPaths, textFields);
            var body = await Helper.ShowResponseAsync(response);

            int code = (int)response.StatusCode;

            if (code == 409)
            {
                // The batch pair partially matches an existing batch — user has to fix config.
                Console.WriteLine("\n[Conflict] The user_batch_id / batch_name pair doesn't match an existing batch.");
                Console.WriteLine("           See the response above for the exact reason.");
                Console.WriteLine("           Fix it in config.json: use the matching partner value, pick a fresh");
                Console.WriteLine("           unique pair, or clear BOTH fields to have them auto-generated.");
                Helper.LogOther(409, "Batch pair conflict on direct upload", body);
                return;
            }

            if ((code == 200 || code == 207) && body != null)
            {
                JsonArray fileUploads = Helper.GetArray("file_uploads");
                var failed = new List<JsonObject>();

                foreach (var blockEl in Helper.ExtractDetailBlocks(body))
                {
                    var block = blockEl.AsObject();

                    if (block["successful_uploads"] is JsonArray succ)
                    {
                        foreach (var itEl in succ)
                        {
                            var it = itEl.AsObject();
                            if (it["file_id"] != null)
                            {
                                var saved = new JsonObject
                                {
                                    ["file_id"] = Helper.Str(it["file_id"]),
                                    ["filename"] = Helper.Str(it["filename"]),
                                    ["status"] = it["status"] != null ? Helper.Str(it["status"]) : "Uploading",
                                };
                                // The server echoes back the batch the file was placed in.
                                if (it["user_batch_id"] != null) saved["user_batch_id"] = Helper.Str(it["user_batch_id"]);
                                if (it["batch_name"] != null) saved["batch_name"] = Helper.Str(it["batch_name"]);
                                fileUploads.Add(saved);
                            }
                        }
                    }
                    if (block["failed_uploads"] is JsonArray fail)
                    {
                        foreach (var itEl in fail) failed.Add(itEl.AsObject());
                    }
                }

                if (fileUploads.Count > 0)
                {
                    Helper.SaveValue("file_uploads", fileUploads);
                    Console.WriteLine("\n[OK] Uploaded files (status will be 'Uploading' at first):");
                    foreach (var e in fileUploads)
                    {
                        var f = e.AsObject();
                        string line = $"   - file_id: {Helper.Str(f["file_id"])}  |  {Helper.Str(f["filename"])}  |  status: {Helper.Str(f["status"])}";
                        if (f["batch_name"] != null) line += $"  |  batch: {Helper.Str(f["batch_name"])}";
                        Console.WriteLine(line);
                    }
                    Console.WriteLine("\nNext: run  dotnet run -- step2");
                }
                else
                {
                    Console.WriteLine("\n[!] No files were accepted. See the failures below.");
                }

                if (failed.Count > 0)
                {
                    Console.WriteLine("\n[!] Some files failed (logged to errors.json):");
                    foreach (var f in failed)
                    {
                        // direct-upload failures carry 'filename' (not 'url').
                        string name = Helper.Str(f["filename"]);
                        string reason = Helper.Str(f["detail"]);
                        Console.WriteLine("   - file: " + name);
                        Console.WriteLine("     reason: " + reason);
                        // Reuse the url_errors section; pass the filename as the reference value.
                        Helper.LogUrlError(name, code, reason, f);
                    }
                }
            }
            else
            {
                Console.WriteLine("\n[X] Upload request failed. Check your api_key, the files in uploads/, "
                    + "and the status code above.");
                // whole-request failure (non-2xx) -> errors.json
                Helper.LogOther(code, "Direct file upload request failed", body);
            }
        }
    }
}
