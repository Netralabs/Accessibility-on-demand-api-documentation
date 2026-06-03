/*
 * Step3CreateJob.cs  —  STEP 3: Start processing the PDF
 * =======================================================
 * Sends an uploaded file for processing and gets back a job_id.
 * Run:  dotnet run -- step3
 *
 * EDIT NOTHING HERE. Set these in  ../config.json  under "process":
 *   "process": { "file_id": "<an uploaded file_id>", "level": 1 }   // level 1 or 2
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
        public static async Task RunAsync()
        {
            JsonObject cfg = Helper.LoadConfig();
            string apiKey = Helper.ApiKey();
            JsonObject process = Helper.GetObject(cfg, "process");
            string fileId = Helper.GetString(process, "file_id", "").Trim();
            int level = Helper.GetInt(process, "level", 1);

            if (string.IsNullOrEmpty(fileId))
            {
                Console.WriteLine("[X] No file_id given. Set \"process\": {\"file_id\": ...} in config.json "
                    + "(use an uploaded file_id from Step 2).");
                return;
            }

            var payload = new JsonObject { ["file_id"] = fileId, ["level"] = level };

            Console.WriteLine($"Starting a job for file_id {fileId} at level {level} ...");
            var response = await Helper.PostAsync(Helper.BaseUrl + "/jobs/", apiKey, payload.ToJsonString());
            var body = await Helper.ShowResponseAsync(response);

            int code = (int)response.StatusCode;
            if (code == 409)
            {
                Console.WriteLine($"\n[Conflict] This is already processed: change the file_id in config.json ({fileId})");
                Helper.LogFileError(fileId, code, "Conflict - file already processed", body);
            }

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
                            ["file_id"] = fileId,
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
                    Helper.LogFileError(fileId, code, "No job_id in job-create response", body);
                }
            }
            else if (code != 409)
            {
                Console.WriteLine("\n[X] Could not start the job. Check the file_id, level, and status code above.");
                Helper.LogFileError(fileId, code, "Could not start job", body);
            }
        }
    }
}
