/*
 * Step1UploadFromUrl.cs  —  STEP 1 (option B): Upload from signed URLs
 * ====================================================================
 * Sends your signed URLs to the API and gets back a file_id for each
 * file that was accepted. Use this if your files already live in S3 or
 * Google Drive (or you already have signed URLs).
 *
 *   Run:  dotnet run -- step1url
 *
 *   • Have PDFs on your computer instead? Use  dotnet run -- step1  (direct upload).
 *   • Need a signed URL? See ../docs/getting-signed-urls.md
 *
 * EDIT NOTHING HERE. All your values live in  ../config.json
 *   - api_key
 *   - sign_urls
 *   - description (optional)
 *   - user_batch_id + batch_name (optional pair; set BOTH to target a specific
 *     batch, or leave BOTH blank to have the API generate one for you)
 *
 * What it saves to data.json:
 *   "file_uploads": [
 *     { "file_id": "....", "url": "....", "status": "Uploading",
 *       "user_batch_id": "....", "batch_name": "...." }, ...
 *   ]
 */

using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

namespace Aod
{
    public static class Step1UploadFromUrl
    {
        public static async Task RunAsync()
        {
            // --- read everything from ../config.json ---
            JsonObject cfg = Helper.LoadConfig();
            string apiKey = Helper.ApiKey();
            string description = Helper.GetString(cfg, "description", "");
            List<string> signedUrls = Helper.GetStringArray(cfg, "sign_urls");
            // Enforce the "both or neither" rule locally so we don't send a bad pair.
            var (userBatchId, batchName) = Helper.GetBatchFields(cfg);

            if (signedUrls.Count == 0)
            {
                Console.WriteLine("[X] No signed URLs found. Add at least one real URL to "
                    + "\"sign_urls\" in config.json.");
                Console.WriteLine("    (Or drop PDFs into the uploads/ folder and use  dotnet run -- step1  instead.)");
                return;
            }

            string endpoint = Helper.BaseUrl + "/files/upload-from-url/";

            var urls = new JsonArray();
            foreach (var u in signedUrls) urls.Add(u);

            // Build the JSON body — only include fields the user actually set.
            var payload = new JsonObject { ["sign_urls"] = urls };
            if (!string.IsNullOrEmpty(description)) payload["description"] = description;
            if (userBatchId != null && batchName != null)
            {
                payload["user_batch_id"] = userBatchId;
                payload["batch_name"] = batchName;
            }

            if (userBatchId != null && batchName != null)
                Console.WriteLine($"Uploading {signedUrls.Count} file(s) from signed URLs into batch "
                    + $"'{batchName}' (user_batch_id: {userBatchId}) ...");
            else
                Console.WriteLine($"Uploading {signedUrls.Count} file(s) from signed URLs "
                    + "(batch will be auto-generated) ...");

            var response = await Helper.PostAsync(endpoint, apiKey, payload.ToJsonString());
            var body = await Helper.ShowResponseAsync(response);

            int code = (int)response.StatusCode;

            if (code == 409)
            {
                // The batch pair partially matches an existing batch — user has to fix config.
                Console.WriteLine("\n[Conflict] The user_batch_id / batch_name pair doesn't match an existing batch.");
                Console.WriteLine("           See the response above for the exact reason.");
                Console.WriteLine("           Fix it in config.json: use the matching partner value, pick a fresh");
                Console.WriteLine("           unique pair, or clear BOTH fields to have them auto-generated.");
                Helper.LogOther(409, "Batch pair conflict on upload-from-url", body);
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
                                    ["url"] = Helper.Str(it["url"]),
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
                        string line = $"   - file_id: {Helper.Str(f["file_id"])}  |  status: {Helper.Str(f["status"])}";
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
                        string fUrl = Helper.Str(f["url"]);
                        string reason = Helper.Str(f["detail"]);
                        Console.WriteLine("   - URL: " + fUrl);
                        Console.WriteLine("     reason: " + reason);
                        // 207 partial-failure item -> errors.json under url_errors
                        Helper.LogUrlError(fUrl, code, reason, f);
                    }
                }
            }
            else
            {
                Console.WriteLine("\n[X] Upload request failed. Check your api_key, your sign_urls, "
                    + "and the status code above.");
                // whole-request failure (non-2xx) -> errors.json
                Helper.LogOther(code, "File upload-from-url request failed", body);
            }
        }
    }
}
