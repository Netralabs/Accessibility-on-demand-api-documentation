/*
 * Step6CheckReport.cs  —  STEP 6: Get the score report
 * =====================================================
 * Checks every report saved by Step 5 and updates its status.
 *   - Reports already "Completed" are skipped.
 *   - When a report is Completed, the full "details" block is saved,
 *     and any old error is removed.
 * Run:  dotnet run -- step6
 *
 * Note: the download_url expires after a short time (expires_in_seconds).
 * Download the score report PDF soon, or re-run this step.
 */

using System;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

namespace Aod
{
    public static class Step6CheckReport
    {
        // ===== EDIT HERE =====
        const string API_KEY = "aod-xxxxxxxxxxx"; // paste your key from Section 3
        // ===== STOP EDITING =====

        static bool IsFinished(string status) =>
            status != null && status.ToLower() == "completed";

        public static async Task RunAsync()
        {
            JsonArray reportProcess = Helper.GetArray("report_process");

            if (reportProcess.Count == 0)
            {
                Console.WriteLine("[X] No reports found. Run step5 first.");
                return;
            }

            bool changed = false;
            int done = 0, pending = 0;

            Console.WriteLine($"Checking {reportProcess.Count} report(s)...\n");

            foreach (var el in reportProcess)
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

                var resp = await Helper.GetAsync(Helper.BaseUrl + "/report/" + jobId, API_KEY);
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

            if (changed) Helper.SaveValue("report_process", reportProcess);

            Console.WriteLine("\nSummary:");
            Console.WriteLine($"   finished: {done}  |  still generating: {pending}");

            if (pending > 0)
                Console.WriteLine("Some reports are still generating. Wait a moment and run this step again.");
            else
                Console.WriteLine("[OK] All reports finished. Download your score report PDF(s) using the URL(s) above.");
        }
    }
}
