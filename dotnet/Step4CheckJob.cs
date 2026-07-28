/*
 * Step4CheckJob.cs  —  STEP 4: Check the job & get the tagged PDF
 * ===============================================================
 * Checks every job saved by Step 3 and updates its status.
 *   - Jobs already "Completed" are skipped.
 *   - When a job is Completed, the full "details" block is saved.
 *   - Failed jobs (or unreadable responses) are logged to errors.json,
 *     not data.json.
 * Run:  dotnet run -- step4
 *
 * Manual review case:
 *   If you started the job with requires_manual_review=true (Step 3), the job
 *   may come back with API status "Completed" BUT no download_url — the API is
 *   holding the link until you complete the manual review in the web UI. This
 *   step marks such jobs locally as "AwaitingManualReview" (not "Completed") so
 *   polling keeps going. To finish them:
 *     1. Go to https://app.accessibilityondemand.ai/login and log in
 *        (you'll also receive an email when the file is ready to review).
 *     2. Open the batch, select the file, click Review.
 *     3. On the last page of the review, click the Complete button.
 *     4. Run this step again — the download_url will now be included.
 *
 * EDIT NOTHING HERE. Your api_key lives in  ../config.json
 *
 * Note: the download_url expires after a short time (expires_in_seconds, e.g.
 * 300s = 5 minutes). Download the tagged PDF soon, or re-run this step.
 */

using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

namespace Aod
{
    public static class Step4CheckJob
    {
        static bool IsFinished(string status) =>
            status != null && status.ToLower() == "completed";

        /*
         * The API reports status="Completed" for two very different situations:
         *   1) Fully done  -> details has a download_url
         *   2) Waiting for manual review -> details has a "message" but NO download_url
         * Detect case 2 so we can label it distinctly and keep polling.
         */
        static bool IsManualReviewPending(string apiStatus, JsonObject details)
        {
            if (apiStatus == null || apiStatus.ToLower() != "completed") return false;
            if (details == null) return false;
            string downloadUrl = details["download_url"] != null ? Helper.Str(details["download_url"]) : "";
            string message = details["message"] != null ? Helper.Str(details["message"]) : "";
            return string.IsNullOrEmpty(downloadUrl) && !string.IsNullOrEmpty(message);
        }

        public static async Task RunAsync()
        {
            string apiKey = Helper.ApiKey();

            JsonArray jobProcess = Helper.GetArray("job_process");

            if (jobProcess.Count == 0)
            {
                Console.WriteLine("[X] No jobs found. Run step3 first.");
                return;
            }

            bool changed = false;
            int done = 0, awaiting = 0, stillProcessing = 0;

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

                var resp = await Helper.GetAsync(Helper.BaseUrl + "/jobs/" + jobId, apiKey);
                JsonObject body;
                try { body = JsonNode.Parse(await resp.Content.ReadAsStringAsync()).AsObject(); }
                catch
                {
                    Console.WriteLine($"   - {jobId}: could not check (status code {(int)resp.StatusCode})");
                    Helper.LogJobError(jobId, (int)resp.StatusCode, "Could not read/parse job response", null);
                    stillProcessing++;
                    continue;
                }

                string apiStatus;
                JsonObject details = null;
                JsonObject error = null;

                if (body["success"] != null && body["success"].GetValue<bool>() == false)
                {
                    apiStatus = "Failed";
                    error = body["error"] as JsonObject ?? new JsonObject();
                }
                else
                {
                    var data = body["data"] as JsonObject ?? new JsonObject();
                    apiStatus = data["status"] != null ? Helper.Str(data["status"]) : "unknown";
                    details = data["details"] as JsonObject;
                }

                // Distinguish the "completed but manual review pending" case locally so it
                // doesn't get bucketed with the fully-done jobs.
                bool manualReviewPending = IsManualReviewPending(apiStatus, details);
                string status = manualReviewPending ? "AwaitingManualReview" : apiStatus;

                Console.WriteLine($"   - {jobId}: {status}");

                if (status != current)
                {
                    entry["status"] = status;
                    changed = true;
                }

                if (manualReviewPending)
                {
                    // Show a friendly, actionable note so the user knows exactly what to do.
                    // We do NOT save details here (there's no download_url yet).
                    Console.WriteLine("     note: " + Helper.Str(details["message"]));
                    Console.WriteLine("     -> log in at https://app.accessibilityondemand.ai/login,");
                    Console.WriteLine("        open the batch, select the file, click Review,");
                    Console.WriteLine("        then click Complete on the last page.");
                    Console.WriteLine("        After that, run this step again to get the download_url.");
                }

                if (status.ToLower() == "completed" && details != null
                    && details["download_url"] != null
                    && !string.IsNullOrEmpty(Helper.Str(details["download_url"])))
                {
                    entry["details"] = details.DeepClone();
                    changed = true;
                    Console.WriteLine("     download_url: " + Helper.Str(details["download_url"]));
                    Console.WriteLine("     expires_in_seconds: " +
                        (details["expires_in_seconds"]?.ToString() ?? ""));
                }

                if (error != null)
                {
                    // Failed jobs are not kept in data.json — they go to errors.json (job_errors).
                    string ecode = Helper.Str(error["code"]);
                    string edetail = Helper.Str(error["detail"]);
                    Console.WriteLine("     error: " + ecode + " - " + edetail);
                    Helper.LogJobError(jobId, (int)resp.StatusCode, ($"{ecode} {edetail}").Trim(), error);
                }

                if (IsFinished(status)) done++;
                else if (status == "AwaitingManualReview") awaiting++;
                else stillProcessing++;
            }

            if (changed) Helper.SaveValue("job_process", jobProcess);

            // Collect awaiting-review jobs so we can list them by id.
            var awaitingList = new List<JsonObject>();
            foreach (var el in jobProcess)
            {
                var entry = el.AsObject();
                if (Helper.Str(entry["status"]) == "AwaitingManualReview")
                    awaitingList.Add(entry);
            }

            Console.WriteLine("\nSummary:");
            Console.WriteLine($"   finished: {done}  |  awaiting manual review: {awaiting}"
                + $"  |  still processing: {stillProcessing}");

            if (awaitingList.Count > 0)
            {
                Console.WriteLine("\nJobs ready for manual review:");
                foreach (var j in awaitingList)
                {
                    Console.WriteLine($"   - job_id: {Helper.Str(j["job_id"])}  |  file_id: {Helper.Str(j["file_id"])}");
                }
                Console.WriteLine("   Log in at https://app.accessibilityondemand.ai/login, complete the review,");
                Console.WriteLine("   then run  dotnet run -- step4  again to get the download link.");
            }

            if (stillProcessing > 0)
                Console.WriteLine("\nSome jobs are still processing. Wait a moment and run this step again.");

            if (awaiting == 0 && stillProcessing == 0)
                Console.WriteLine("[OK] All jobs finished. To get a score report, put a file_id into config.json "
                    + "(\"report\": {\"file_id\": ...}) and run  dotnet run -- step5");
        }
    }
}
