/*
 * Step5CreateReport.cs  —  STEP 5: Request an axes4 score report
 * ===============================================================
 * Asks the API to generate an axes4 accessibility score report for a file.
 * Run:  dotnet run -- step5
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
        // ===== EDIT HERE =====
        const string FILE_ID = "";                // the file_id to generate a report for
        // ===== STOP EDITING =====

        public static async Task RunAsync()
        {
            if (string.IsNullOrEmpty(FILE_ID))
            {
                Console.WriteLine("[X] No file_id given. Paste a FILE_ID above.");
                return;
            }

            var payload = new JsonObject { ["file_id"] = FILE_ID };

            Console.WriteLine($"Requesting a score report for file_id {FILE_ID} ...");
            var response = await Helper.PostAsync(Helper.BaseUrl + "/report/", Helper.API_KEY, payload.ToJsonString());
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
                            ["file_id"] = FILE_ID,
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
                }
            }
            else
            {
                Console.WriteLine("\n[X] Could not request the report. Check the file_id and status code above.");
            }
        }
    }
}
