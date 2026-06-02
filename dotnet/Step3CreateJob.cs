/*
 * Step3CreateJob.cs  —  STEP 3: Start processing the PDF
 * =======================================================
 * Sends an uploaded file for processing and gets back a job_id.
 * Run:  dotnet run -- step3
 *
 * What it saves to data.json:
 *   "job_process": [ { "file_id": "....", "job_id": "....", "status": "Queued" }, ... ]
 */

using System;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

namespace Aod
{
    public static class Step3CreateJob
    {
        // ===== EDIT HERE =====
        const string API_KEY = "aod-xxxxxxxxxxx"; // paste your key from Section 3
        const string FILE_ID = "";                // an uploaded file_id to process
        const int LEVEL = 1;                      // 1 or 2
        // ===== STOP EDITING =====

        public static async Task RunAsync()
        {
            if (string.IsNullOrEmpty(FILE_ID))
            {
                Console.WriteLine("[X] No file_id given. Paste an uploaded FILE_ID above.");
                return;
            }

            var payload = new JsonObject { ["file_id"] = FILE_ID, ["level"] = LEVEL };

            Console.WriteLine($"Starting a job for file_id {FILE_ID} at level {LEVEL} ...");
            var response = await Helper.PostAsync(Helper.BaseUrl + "/jobs", API_KEY, payload.ToJsonString());
            var body = await Helper.ShowResponseAsync(response);

            int code = (int)response.StatusCode;
            if (code == 409)
                Console.WriteLine($"\n[Conflict] This is already processed: change file id {FILE_ID}");

            if ((code == 200 || code == 201) && body != null)
            {
                var data = body["data"] as JsonObject ?? new JsonObject();
                string jobId = data["job_id"] != null ? Helper.Str(data["job_id"]) : null;

                if (jobId != null)
                {
                    JsonArray jobProcess = Helper.GetArray("job_process");
                    bool exists = false;
                    foreach (var e in jobProcess)
                        if (Helper.Str(e.AsObject()["job_id"]) == jobId) { exists = true; break; }

                    if (!exists)
                    {
                        jobProcess.Add(new JsonObject
                        {
                            ["file_id"] = FILE_ID,
                            ["job_id"] = jobId,
                            ["status"] = "Queued",
                        });
                        Helper.SaveValue("job_process", jobProcess);
                    }
                    Console.WriteLine("\n[OK] Got job_id: " + jobId);
                    Console.WriteLine("Next: run  dotnet run -- step4");
                }
                else
                {
                    Console.WriteLine("\n[!] Could not find 'job_id' in the response. "
                        + "Check the printed response above and update the key name.");
                }
            }
            else
            {
                Console.WriteLine("\n[X] Could not start the job. Check the file_id, level, and status code above.");
            }
        }
    }
}
