/*
 * Program.cs  —  dispatcher
 * -------------------------
 * Decides which step to run based on the argument you pass:
 *
 *   dotnet run -- step1   (upload PDFs from the uploads/ folder)
 *   dotnet run -- step1url (upload from signed URLs)
 *   dotnet run -- step2   (check upload)
 *   dotnet run -- step3   (create job)
 *   dotnet run -- step4   (check job)
 *   dotnet run -- step5   (create report)
 *   dotnet run -- step6   (check report)
 *
 * You normally do NOT need to edit this file. Edit the Step*.cs files instead.
 */

using System;
using System.Threading.Tasks;

namespace Aod
{
    public static class Program
    {
        public static async Task Main(string[] args)
        {
            string step = args.Length > 0 ? args[0].ToLower() : "";

            switch (step)
            {
                case "step1": await Step1Upload.RunAsync(); break;
                case "step1url": await Step1UploadFromUrl.RunAsync(); break;
                case "step2": await Step2CheckUpload.RunAsync(); break;
                case "step3": await Step3CreateJob.RunAsync(); break;
                case "step4": await Step4CheckJob.RunAsync(); break;
                case "step5": await Step5CreateReport.RunAsync(); break;
                case "step6": await Step6CheckReport.RunAsync(); break;
                default:
                    Console.WriteLine("Please say which step to run, for example:");
                    Console.WriteLine("  dotnet run -- step1");
                    Console.WriteLine("\nSteps:");
                    Console.WriteLine("  step1    = upload PDFs from the uploads/ folder (direct)");
                    Console.WriteLine("  step1url = upload from signed URLs (S3 / Google Drive)");
                    Console.WriteLine("  step2    = check upload     step4 = check job");
                    Console.WriteLine("  step3    = create job       step5 = create report");
                    Console.WriteLine("                              step6 = check report");
                    break;
            }
        }
    }
}
