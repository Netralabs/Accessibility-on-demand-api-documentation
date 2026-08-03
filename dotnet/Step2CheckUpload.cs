/*
 * Step2CheckUpload.cs  —  STEP 2: Check upload status
 * ====================================================
 * Checks every file saved by Step 1 and updates its status: "uploaded", still
 * "uploading", or "failed".  Run:  dotnet run -- step2
 *
 * A file that comes back "failed" is recorded with its error and a "can_reupload"
 * flag. If can_reupload is true, retry it with  dotnet run -- reupload  and run
 * this again; if false, the file can't be recovered — upload a fresh copy with
 * step1. Files already "uploaded" or "failed" are skipped on later runs.
 *
 * EDIT NOTHING HERE. Your api_key lives in  ../config.json
 */

using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

namespace Aod
{
    public static class Step2CheckUpload
    {
        static string ReadStatus(JsonObject body)
        {
            if (body["status"] != null) return Helper.Str(body["status"]);
            if (body["data"] is JsonObject data && data["uploading_status"] != null)
                return Helper.Str(data["uploading_status"]);
            return null;
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

            bool changed = false;

            // Only files that haven't settled yet need checking; print why the rest are skipped.
            var pending = new List<JsonObject>();
            foreach (var el in fileUploads)
            {
                var entry = el.AsObject();
                string status = Helper.Str(entry["status"]).ToLower();
                if (status == "uploaded")
                {
                    Console.WriteLine($"   - {Helper.Str(entry["file_id"])}: already uploaded (skipped)");
                }
                else if (status == "failed")
                {
                    string hint = Helper.GetBool(entry, "can_reupload", false) ? "can re-upload" : "cannot re-upload";
                    Console.WriteLine($"   - {Helper.Str(entry["file_id"])}: already failed ({hint}, skipped)");
                }
                else
                {
                    pending.Add(entry);
                }
            }

            Console.WriteLine($"\nChecking {pending.Count} file(s)...\n");

            foreach (var entry in pending)
            {
                string fileId = Helper.Str(entry["file_id"]);

                var resp = await Helper.GetAsync(Helper.BaseUrl + "/files/status/" + fileId, apiKey);
                if ((int)resp.StatusCode != 200)
                {
                    Console.WriteLine($"   - {fileId}: could not check (status code {(int)resp.StatusCode})");
                    Helper.LogFileError(fileId, (int)resp.StatusCode, "Could not check upload status", null);
                    continue;
                }

                JsonObject respBody;
                try { respBody = JsonNode.Parse(await resp.Content.ReadAsStringAsync()).AsObject(); }
                catch
                {
                    Console.WriteLine($"   - {fileId}: could not read response");
                    Helper.LogFileError(fileId, (int)resp.StatusCode, "Could not read/parse response body", null);
                    continue;
                }

                JsonObject data = respBody["data"] is JsonObject d ? d : new JsonObject();
                string newStatus = ReadStatus(respBody) ?? "unknown";
                string statusLower = newStatus.ToLower();

                if (statusLower == "uploaded")
                {
                    Console.WriteLine($"   - {fileId}: {newStatus}");
                    entry["status"] = "uploaded";
                    entry.Remove("uploading_error");
                    entry.Remove("can_reupload");
                    changed = true;
                }
                else if (statusLower == "failed")
                {
                    // The background upload failed. Record why, and whether it can be retried,
                    // so the re-upload step knows what to do.
                    string err = Helper.GetString(data, "uploading_error", "upload failed");
                    bool can = Helper.GetBool(data, "can_reupload", false);
                    entry["status"] = "failed";
                    entry["uploading_error"] = err;
                    entry["can_reupload"] = can;
                    string hint = can ? "can re-upload" : "cannot re-upload";
                    Console.WriteLine($"   - {fileId}: Failed — {err}  ({hint})");
                    changed = true;
                }
                else
                {
                    // Still uploading (or an unexpected status) — check again next run.
                    Console.WriteLine($"   - {fileId}: {newStatus}");
                }
            }

            if (changed) Helper.SaveValue("file_uploads", fileUploads);

            // Tally the final state.
            int uploaded = 0, failedCount = 0, stillPending = 0;
            var failed = new List<JsonObject>();
            foreach (var el in fileUploads)
            {
                var entry = el.AsObject();
                string status = Helper.Str(entry["status"]).ToLower();
                if (status == "uploaded") uploaded++;
                else if (status == "failed") { failedCount++; failed.Add(entry); }
                else stillPending++;
            }

            Console.WriteLine("\nSummary:");
            Console.WriteLine($"   uploaded: {uploaded}  |  failed: {failedCount}  |  still uploading: {stillPending}");

            if (failed.Count > 0)
            {
                Console.WriteLine("\n[!] Some files failed to upload:");
                int retryable = 0, blocked = 0;
                foreach (var e in failed)
                {
                    bool can = Helper.GetBool(e, "can_reupload", false);
                    string err = Helper.GetString(e, "uploading_error", "upload failed");
                    string hint = can ? "can re-upload" : "cannot re-upload";
                    Console.WriteLine($"   - {Helper.Str(e["file_id"])}: {err}  ({hint})");
                    if (can) retryable++; else blocked++;
                }
                if (retryable > 0)
                    Console.WriteLine($"    {retryable} can be retried — run  dotnet run -- reupload");
                if (blocked > 0)
                    Console.WriteLine($"    {blocked} cannot be re-uploaded — upload a fresh copy with  dotnet run -- step1");
            }

            if (stillPending > 0)
                Console.WriteLine("\nSome files are still uploading. Wait a moment and run this step again.");
            else if (failed.Count == 0)
                Console.WriteLine("[OK] All files uploaded. Next: put an uploaded file_id into config.json "
                    + "(\"process\": {\"file_id\": ...}) and run  dotnet run -- step3");
        }
    }
}
