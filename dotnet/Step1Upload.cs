/*
 * Step1Upload.cs  —  STEP 1: Upload your file(s)
 * ===============================================
 * Sends your signed URLs to the API and gets back a file_id for each
 * file that was accepted. Run this first:  dotnet run -- step1
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
    public static class Step1Upload
    {
        // ============================================================
        // ===== EDIT HERE =====
        // ============================================================
        static readonly string[] SIGNED_URLS = {   // paste your signed URL(s) here
            "https://your-signed-url-1",
            "https://your-signed-url-2",
        };

        const string DESCRIPTION = "description about batch - optional"; // optional text
        // ============================================================
        // ===== STOP EDITING (the rest runs by itself) =====
        // ============================================================

        public static async Task RunAsync()
        {
            string endpoint = Helper.BaseUrl + "/file-upload/";

            var urls = new JsonArray();
            foreach (var u in SIGNED_URLS) urls.Add(u);

            var payload = new JsonObject
            {
                ["sign_urls"] = urls,
                ["description"] = DESCRIPTION,
            };

            Console.WriteLine("Uploading files...");
            var response = await Helper.PostAsync(endpoint, Helper.API_KEY, payload.ToJsonString());
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
                    Console.WriteLine("\n[!] Some files failed:");
                    foreach (var f in failed)
                    {
                        Console.WriteLine("   - URL: " + Helper.Str(f["url"]));
                        Console.WriteLine("     reason: " + Helper.Str(f["detail"]));
                    }
                }
            }
            else
            {
                Console.WriteLine("\n[X] Upload request failed. Check your API key, your signed URLs, "
                    + "and the status code above.");
            }
        }
    }
}
