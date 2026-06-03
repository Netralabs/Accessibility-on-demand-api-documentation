/*
 * Step5CreateReport.cs  —  STEP 5: Request an axes4 score report
 * ===============================================================
 * Asks the API to generate an axes4 accessibility score report for a file.
 * Run:  dotnet run -- step5
 *
 * EDIT NOTHING HERE. Set this in  ../config.json  under "report":
 *   "report": { "file_id": "<the file_id to generate a report for>" }
 *
 * What it saves to data.json:
 *   "report_process": [ { "file_id": "....", "job_id": "....", "status": "Processing" }, ... ]
 */

using System;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

namespace Aod
{
    public static class Step5CreateReport
    {
        public static async Task RunAsync()
        {
            JsonObject cfg = Helper.LoadConfig();
            string apiKey = Helper.ApiKey();
            JsonObject report = Helper.GetObject(cfg, "report");
            string fileId = Helper.GetString(report, "file_id", "").Trim();

            if (string.IsNullOrEmpty(fileId))
            {
                Console.WriteLine("[X] No file_id given. Set \"report\": {\"file_id\": ...} in config.json.");
                return;
            }

            var payload = new JsonObject { ["file_id"] = fileId };

            Console.WriteLine($"Requesting a score report for file_id {fileId} ...");
            var response = await Helper.PostAsync(Helper.BaseUrl + "/report/", apiKey, payload.ToJsonString());
            var body = await Helper.ShowResponseAsync(response);

            int code = (int)response.StatusCode;
            if ((code == 200 || code == 201) && body != null)
            {
                var data = body["data"] as JsonObject ?? new JsonObject();
                string jobId = data["job_id"] != null ? Helper.Str(data["job_id"]) : null;

                if (jobId != null)
                {
                    JsonArray reportProcess = Helper.GetArray("report_process");
                    bool exists = false;
                    foreach (var e in reportProcess)
                        if (Helper.Str(e.AsObject()["job_id"]) == jobId) { exists = true; break; }

                    if (!exists)
                    {
                        reportProcess.Add(new JsonObject
                        {
                            ["file_id"] = fileId,
                            ["job_id"] = jobId,
                            ["status"] = "Processing",
                        });
                        Helper.SaveValue("report_process", reportProcess);
                    }
                    Console.WriteLine("\n[OK] Got report job_id: " + jobId);
                    Console.WriteLine("Next: run  dotnet run -- step6");
                }
                else
                {
                    Console.WriteLine("\n[!] Could not find 'job_id' in the response. "
                        + "Check the printed response above and update the key name.");
                    Helper.LogFileError(fileId, code, "No job_id in report-create response", body);
                }
            }
            else
            {
                Console.WriteLine("\n[X] Could not request the report. Check the file_id and status code above.");
                Helper.LogFileError(fileId, code, "Could not request report", body);
            }
        }
    }
}
