/*
 * Step2CheckUpload.cs  —  STEP 2: Check upload status
 * ====================================================
 * Checks every file saved by Step 1 and updates its status.
 * Files already "uploaded" are skipped. Run:  dotnet run -- step2
 */

using System;
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
            JsonArray fileUploads = Helper.GetArray("file_uploads");

            if (fileUploads.Count == 0)
            {
                Console.WriteLine("[X] No files found. Run step1 first.");
                return;
            }

            bool changed = false;
            int uploaded = 0, pending = 0;

            Console.WriteLine($"Checking {fileUploads.Count} file(s)...\n");

            foreach (var el in fileUploads)
            {
                var entry = el.AsObject();
                string fileId = Helper.Str(entry["file_id"]);
                string current = Helper.Str(entry["status"]);

                if (current.ToLower() == "uploaded")
                {
                    Console.WriteLine($"   - {fileId}: already uploaded (skipped)");
                    uploaded++;
                    continue;
                }

                var resp = await Helper.GetAsync(Helper.BaseUrl + "/file-upload/" + fileId, Helper.API_KEY);
                if ((int)resp.StatusCode != 200)
                {
                    Console.WriteLine($"   - {fileId}: could not check (status code {(int)resp.StatusCode})");
                    pending++;
                    continue;
                }

                JsonObject respBody;
                try { respBody = JsonNode.Parse(await resp.Content.ReadAsStringAsync()).AsObject(); }
                catch { Console.WriteLine($"   - {fileId}: could not read response"); pending++; continue; }

                string newStatus = ReadStatus(respBody) ?? "unknown";
                Console.WriteLine($"   - {fileId}: {newStatus}");

                if (newStatus.ToLower() == "uploaded")
                {
                    entry["status"] = "uploaded";
                    changed = true;
                    uploaded++;
                }
                else { pending++; }
            }

            if (changed) Helper.SaveValue("file_uploads", fileUploads);

            Console.WriteLine("\nSummary:");
            Console.WriteLine($"   uploaded: {uploaded}  |  still uploading: {pending}");

            if (pending > 0)
                Console.WriteLine("Some files are still uploading. Wait a moment and run this step again.");
            else
                Console.WriteLine("[OK] All files uploaded. Next: run  dotnet run -- step3");
        }
    }
}
