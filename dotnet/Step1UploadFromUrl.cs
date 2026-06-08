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
 *   (api_key, signed_urls, description).
 *
 * What it saves to data.json:
 *   "file_uploads": [ { "file_id": "....", "url": "....", "status": "Uploading" }, ... ]
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
            List<string> signedUrls = Helper.GetStringArray(cfg, "signed_urls");

            if (signedUrls.Count == 0)
            {
                Console.WriteLine("[X] No signed URLs found. Add at least one real URL to "
                    + "\"signed_urls\" in config.json.");
                Console.WriteLine("    (Or drop PDFs into the uploads/ folder and use  dotnet run -- step1  instead.)");
                return;
            }

            string endpoint = Helper.BaseUrl + "/files/upload-from-url/";

            var urls = new JsonArray();
            foreach (var u in signedUrls) urls.Add(u);

            var payload = new JsonObject
            {
                ["sign_urls"] = urls,
                ["description"] = description,
            };

            Console.WriteLine($"Uploading {signedUrls.Count} file(s) from signed URLs...");
            var response = await Helper.PostAsync(endpoint, apiKey, payload.ToJsonString());
            var body = await Helper.ShowResponseAsync(response);

            int code = (int)response.StatusCode;
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
                                fileUploads.Add(new JsonObject
                                {
                                    ["file_id"] = Helper.Str(it["file_id"]),
                                    ["url"] = Helper.Str(it["url"]),
                                    ["status"] = it["status"] != null ? Helper.Str(it["status"]) : "Uploading",
                                });
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
                        Console.WriteLine($"   - file_id: {Helper.Str(f["file_id"])}  |  status: {Helper.Str(f["status"])}");
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
                Console.WriteLine("\n[X] Upload request failed. Check your api_key, your signed_urls, "
                    + "and the status code above.");
                // whole-request failure (non-2xx) -> errors.json
                Helper.LogOther(code, "File upload-from-url request failed", body);
            }
        }
    }
}
