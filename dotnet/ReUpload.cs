/*
 * ReUpload.cs  —  Retry files whose upload Failed
 * ================================================
 * When Step 2 shows a file's status as "failed" and "can_reupload" is true, this
 * step retries the upload for those files by calling
 * POST /files/re-upload/{file_id} for each of them.  Run:  dotnet run -- reupload
 *
 * It reads the files saved in data.json, picks the ones that failed and can be
 * re-uploaded, and re-uploads each one. Re-uploading restarts the background
 * transfer (the status goes back to "Uploading"), so afterwards run step2 again
 * to see whether it finished.
 *
 * A file whose status is failed with "can_reupload": false can't be recovered —
 * upload a fresh copy with step1 instead.
 *
 * EDIT NOTHING HERE. Your api_key lives in  ../config.json
 */

using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

namespace Aod
{
    public static class ReUpload
    {
        // The re-upload response wraps the file info in 'data' — return it (or empty).
        static JsonObject ReadData(JsonObject body)
        {
            return body["data"] is JsonObject data ? data : new JsonObject();
        }

        public static async Task RunAsync()
        {
            string apiKey = Helper.ApiKey();

            JsonArray fileUploads = Helper.GetArray("file_uploads");

            if (fileUploads.Count == 0)
            {
                Console.WriteLine("[X] No files found. Run step1 first.");
                return;
            }

            // Split the failed files into 'can retry' vs 'cannot retry'.
            var retryable = new List<JsonObject>();
            var blocked = new List<JsonObject>();
            foreach (var el in fileUploads)
            {
                var entry = el.AsObject();
                if (Helper.Str(entry["status"]).ToLower() == "failed")
                {
                    if (Helper.GetBool(entry, "can_reupload", false)) retryable.Add(entry);
                    else blocked.Add(entry);
                }
            }

            if (retryable.Count == 0)
            {
                if (blocked.Count > 0)
                {
                    Console.WriteLine("[!] Some files failed but cannot be re-uploaded (can_reupload = false):");
                    foreach (var e in blocked)
                        Console.WriteLine($"   - {Helper.Str(e["file_id"])}: {Helper.GetString(e, "uploading_error", "upload failed")}");
                    Console.WriteLine("    These can't be recovered — upload a fresh copy with  dotnet run -- step1");
                }
                else
                {
                    Console.WriteLine("[OK] No failed files to re-upload.");
                    Console.WriteLine("    (Run  dotnet run -- step2  first — it marks a file 'failed' if its upload fails.)");
                }
                return;
            }

            Console.WriteLine($"Re-uploading {retryable.Count} failed file(s)...\n");

            bool changed = false;
            int started = 0;

            foreach (var entry in retryable)
            {
                string fileId = Helper.Str(entry["file_id"]);

                var resp = await Helper.PostNoBodyAsync(Helper.BaseUrl + "/files/re-upload/" + fileId, apiKey);

                if ((int)resp.StatusCode != 200)
                {
                    Console.WriteLine($"   - {fileId}: re-upload failed (status code {(int)resp.StatusCode})");
                    JsonNode raw = null;
                    try { raw = JsonNode.Parse(await resp.Content.ReadAsStringAsync()); }
                    catch { raw = null; }
                    Helper.LogFileError(fileId, (int)resp.StatusCode, "Re-upload request failed", raw);
                    continue;
                }

                JsonObject respBody;
                try { respBody = JsonNode.Parse(await resp.Content.ReadAsStringAsync()).AsObject(); }
                catch
                {
                    Console.WriteLine($"   - {fileId}: could not read response");
                    Helper.LogFileError(fileId, (int)resp.StatusCode, "Could not read/parse re-upload response", null);
                    continue;
                }

                string newStatus = Helper.GetString(ReadData(respBody), "uploading_status", "Uploading");
                // A successful re-upload restarts the background transfer. Reset our tracked
                // status so step2 will check it again, and clear the old failure info.
                entry["status"] = newStatus;
                entry.Remove("uploading_error");
                entry.Remove("can_reupload");
                Console.WriteLine($"   - {fileId}: re-upload started (status: {newStatus})");
                started++;
                changed = true;
            }

            if (changed) Helper.SaveValue("file_uploads", fileUploads);

            string line = $"   re-upload started: {started}  |  couldn't start: {retryable.Count - started}";
            if (blocked.Count > 0) line += $"  |  not re-uploadable: {blocked.Count}";
            Console.WriteLine("\nSummary:");
            Console.WriteLine(line);
            if (started > 0)
                Console.WriteLine("\nNext: run  dotnet run -- step2  again to see whether they finished uploading.");
        }
    }
}
