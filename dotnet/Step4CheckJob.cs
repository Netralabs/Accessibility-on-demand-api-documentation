/*
 * Step4CheckJob.cs  —  STEP 4: Check the job & get the tagged PDF
 * ===============================================================
 * Checks every job saved by Step 3 and updates its status.
 *   - Jobs already "Completed" are skipped.
 *   - When a job is Completed, the full "details" block is saved.
 * Run:  dotnet run -- step4
 *
 * Note: the download_url expires after a short time (expires_in_seconds, e.g.
 * 300s = 5 minutes). Download the tagged PDF soon, or re-run this step.
 */

using System;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

namespace Aod
{
    public static class Step4CheckJob
    {

        static bool IsFinished(string status) =>
            status != null && status.ToLower() == "completed";

        public static async Task RunAsync()
        {
            JsonArray jobProcess = Helper.GetArray("job_process");

            if (jobProcess.Count == 0)
            {
                Console.WriteLine("[X] No jobs found. Run step3 first.");
                return;
            }

            bool changed = false;
            int done = 0, pending = 0;

            Console.WriteLine($"Checking {jobProcess.Count} job(s)...\n");

            foreach (var el in jobProcess)
            {
                var entry = el.AsObject();
                string jobId = Helper.Str(entry["job_id"]);
                string current = Helper.Str(entry["status"]);

                if (IsFinished(current))
                {
                    Console.WriteLine($"   - {jobId}: already {current} (skipped)");
                    done++;
                    continue;
                }

                var resp = await Helper.GetAsync(Helper.BaseUrl + "/jobs/" + jobId, Helper.API_KEY);
                JsonObject body;
                try { body = JsonNode.Parse(await resp.Content.ReadAsStringAsync()).AsObject(); }
                catch { Console.WriteLine($"   - {jobId}: could not check (status code {(int)resp.StatusCode})"); pending++; continue; }

                string status;
                JsonObject details = null;
                JsonObject error = null;

                if (body["success"] != null && body["success"].GetValue<bool>() == false)
                {
                    status = "Failed";
                    error = body["error"] as JsonObject ?? new JsonObject();
                }
                else
                {
                    var data = body["data"] as JsonObject ?? new JsonObject();
                    status = data["status"] != null ? Helper.Str(data["status"]) : "unknown";
                    details = data["details"] as JsonObject;
                }

                Console.WriteLine($"   - {jobId}: {status}");

                if (status != current)
                {
                    entry["status"] = status;
                    changed = true;
                }

                if (status.ToLower() == "completed" && details != null)
                {
                    entry["details"] = details.DeepClone();
                    entry.Remove("error");
                    changed = true;
                    Console.WriteLine("     download_url: " + Helper.Str(details["download_url"]));
                    Console.WriteLine("     expires_in_seconds: " +
                        (details["expires_in_seconds"]?.ToString() ?? ""));
                }

                if (error != null)
                {
                    entry["error"] = error.DeepClone();
                    changed = true;
                    Console.WriteLine("     error: " + Helper.Str(error["code"]) + " - " + Helper.Str(error["detail"]));
                }

                if (IsFinished(status)) done++; else pending++;
            }

            if (changed) Helper.SaveValue("job_process", jobProcess);

            Console.WriteLine("\nSummary:");
            Console.WriteLine($"   finished: {done}  |  still processing: {pending}");

            if (pending > 0)
                Console.WriteLine("Some jobs are still processing. Wait a moment and run this step again.");
            else
                Console.WriteLine("[OK] All jobs finished. You can now run  dotnet run -- step5");
        }
    }
}
