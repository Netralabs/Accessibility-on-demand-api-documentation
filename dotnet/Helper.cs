/*
 * Helper.cs
 * ---------
 * Shared code used by all 6 steps. You normally do NOT need to edit this file.
 *
 * It holds the Base URL, builds the Authorization header, sends requests,
 * reads your values from the shared ../config.json (repo root), reads/writes
 * the local data.json, and logs anything that is NOT a clean success to
 * the local errors.json. Uses the built-in HttpClient and System.Text.Json
 * (no packages to install).
 *
 * ALL editable values live in  ../config.json  — you never edit the .cs files.
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

namespace Aod
{
    public static class Helper
    {
        // The web address all the APIs live under (from Section 1 of the README).
        public const string BaseUrl = "https://api.accessibilityondemand.space/api/v1";

        // Shared config lives in the REPO ROOT (one level up from this dotnet folder).
        public static readonly string ConfigFile =
            Path.Combine(Directory.GetCurrentDirectory(), "..", "config.json");

        // data.json (clean tracked items) is created in this dotnet folder.
        public static readonly string DataFile =
            Path.Combine(Directory.GetCurrentDirectory(), "data.json");

        // errors.json (anything that is NOT a clean success) also stays in this folder.
        public static readonly string ErrorsFile =
            Path.Combine(Directory.GetCurrentDirectory(), "errors.json");

        // uploads/ folder (repo root) — where users drop PDFs for direct upload (Step 1).
        public static readonly string UploadsDir =
            Path.Combine(Directory.GetCurrentDirectory(), "..", "uploads");

        private static readonly HttpClient Client = new HttpClient();

        private static readonly JsonSerializerOptions Pretty =
            new JsonSerializerOptions { WriteIndented = true };

        // ---------- config.json (the one file you edit) ----------

        public static JsonObject LoadConfig()
        {
            try
            {
                if (!File.Exists(ConfigFile))
                {
                    Console.WriteLine("[X] config.json was not found at ../config.json (the repo root). "
                        + "Run from inside the dotnet folder, with config.json in the folder above it.");
                    Environment.Exit(1);
                }
                string txt = File.ReadAllText(ConfigFile);
                return JsonNode.Parse(txt).AsObject();
            }
            catch (Exception e)
            {
                Console.WriteLine("[X] Could not read config.json (is the JSON valid?): " + e.Message);
                Environment.Exit(1);
                return new JsonObject(); // unreachable
            }
        }

        // Read the API key, with a friendly error if it's still the placeholder.
        public static string ApiKey()
        {
            string key = GetString(LoadConfig(), "api_key", "");
            if (string.IsNullOrEmpty(key) || key == "aod-xxxxxxxxxxx")
            {
                Console.WriteLine("[X] Please set your real \"api_key\" in config.json (it is still the placeholder).");
                Environment.Exit(1);
            }
            return key;
        }

        // Read a string value from a JsonObject, or the default if missing/null.
        public static string GetString(JsonObject obj, string key, string def = "")
        {
            if (obj != null && obj[key] != null)
            {
                try { return obj[key].GetValue<string>(); } catch { }
            }
            return def;
        }

        // Read an int value from a JsonObject, or the default if missing/null.
        public static int GetInt(JsonObject obj, string key, int def)
        {
            if (obj != null && obj[key] != null)
            {
                try { return obj[key].GetValue<int>(); } catch { }
                // tolerate numbers stored as strings, e.g. "1"
                try { return int.Parse(obj[key].GetValue<string>()); } catch { }
            }
            return def;
        }

        // Read a nested object (e.g. "process", "report") from config, or empty object.
        public static JsonObject GetObject(JsonObject obj, string key)
        {
            if (obj != null && obj[key] is JsonObject o)
            {
                return o.DeepClone().AsObject();
            }
            return new JsonObject();
        }

        // Read a string array from config (e.g. "sign_urls"), ignoring blank/placeholder entries.
        public static List<string> GetStringArray(JsonObject obj, string key)
        {
            var outList = new List<string>();
            if (obj != null && obj[key] is JsonArray arr)
            {
                foreach (var el in arr)
                {
                    if (el == null) continue;
                    string v;
                    try { v = el.GetValue<string>().Trim(); } catch { continue; }
                    if (string.IsNullOrEmpty(v) || v.StartsWith("https://your-signed-url")) continue;
                    outList.Add(v);
                }
            }
            return outList;
        }

        // Returns a sorted list of full paths to every .pdf in the repo-root uploads/ folder.
        // Used by Step 1 direct upload. Returns an empty list if the folder is missing or has no PDFs.
        public static List<string> FindLocalPdfs()
        {
            var outList = new List<string>();
            if (!Directory.Exists(UploadsDir)) return outList;
            var files = Directory.GetFiles(UploadsDir);
            Array.Sort(files, StringComparer.OrdinalIgnoreCase);
            foreach (var path in files)
            {
                if (path.ToLower().EndsWith(".pdf") && File.Exists(path))
                    outList.Add(path);
            }
            return outList;
        }

        // ---------- HTTP ----------

        public static async Task<HttpResponseMessage> PostAsync(string url, string apiKey, string jsonBody)
        {
            var req = new HttpRequestMessage(HttpMethod.Post, url);
            req.Headers.TryAddWithoutValidation("Authorization", "Bearer " + apiKey);
            req.Content = new StringContent(jsonBody, Encoding.UTF8, "application/json");
            return await Client.SendAsync(req);
        }

        // POST one or more local files as multipart/form-data.
        // The 'files' field is repeated once per file; 'description' is optional.
        // Do NOT set Content-Type yourself — MultipartFormDataContent sets the boundary.
        public static async Task<HttpResponseMessage> PostMultipartAsync(
            string url, string apiKey, List<string> filePaths, string description)
        {
            var req = new HttpRequestMessage(HttpMethod.Post, url);
            req.Headers.TryAddWithoutValidation("Authorization", "Bearer " + apiKey);

            var form = new MultipartFormDataContent();
            foreach (var path in filePaths)
            {
                byte[] bytes = File.ReadAllBytes(path);
                var fileContent = new ByteArrayContent(bytes);
                fileContent.Headers.ContentType =
                    new System.Net.Http.Headers.MediaTypeHeaderValue("application/pdf");
                // field name "files" (repeated), with the file's name
                form.Add(fileContent, "files", Path.GetFileName(path));
            }
            if (!string.IsNullOrEmpty(description))
                form.Add(new StringContent(description), "description");

            req.Content = form;
            return await Client.SendAsync(req);
        }

        public static async Task<HttpResponseMessage> GetAsync(string url, string apiKey)
        {
            var req = new HttpRequestMessage(HttpMethod.Get, url);
            req.Headers.TryAddWithoutValidation("Authorization", "Bearer " + apiKey);
            return await Client.SendAsync(req);
        }

        // Prints status + body; returns the parsed JSON object (or null if not JSON).
        public static async Task<JsonObject> ShowResponseAsync(HttpResponseMessage response)
        {
            Console.WriteLine("Status code: " + (int)response.StatusCode);
            string text = await response.Content.ReadAsStringAsync();
            try
            {
                JsonObject body = JsonNode.Parse(text).AsObject();
                Console.WriteLine("Response:");
                Console.WriteLine(JsonSerializer.Serialize((JsonNode)body, Pretty));
                return body;
            }
            catch
            {
                Console.WriteLine("Response (text): " + text);
                return null;
            }
        }

        // ---------- data.json (clean tracked items) ----------

        public static JsonObject LoadData()
        {
            try
            {
                if (!File.Exists(DataFile)) return new JsonObject();
                string txt = File.ReadAllText(DataFile);
                return JsonNode.Parse(txt).AsObject();
            }
            catch
            {
                return new JsonObject();
            }
        }

        public static void SaveValue(string key, JsonNode value)
        {
            try
            {
                JsonObject data = LoadData();
                data[key] = value;
                File.WriteAllText(DataFile, JsonSerializer.Serialize((JsonNode)data, Pretty));
                Console.WriteLine($"[saved] '{key}' was saved to data.json");
            }
            catch (Exception e)
            {
                Console.WriteLine("[!] Could not save to data.json: " + e.Message);
            }
        }

        public static JsonArray GetArray(string key)
        {
            JsonObject data = LoadData();
            if (data.ContainsKey(key) && data[key] is JsonArray arr)
            {
                // detach so we can re-add under the key later
                JsonArray copy = new JsonArray();
                foreach (var el in arr) copy.Add(el?.DeepClone());
                return copy;
            }
            return new JsonArray();
        }

        // The 'detail' list lives in different places depending on the status:
        //   200 -> body.data.detail   |   207 -> body.error.details
        public static JsonArray ExtractDetailBlocks(JsonObject body)
        {
            if (body["data"] is JsonObject data && data["detail"] is JsonArray d)
                return d;
            if (body["error"] is JsonObject err && err["details"] is JsonArray dd)
                return dd;
            return new JsonArray();
        }

        public static string Str(JsonNode node, string fallback = "")
        {
            return node == null ? fallback : node.GetValue<string>();
        }

        // ---------- errors.json (anything that is NOT a clean success) ----------
        //
        // Grouped, append-only history. Sections:
        //   "url_errors"  — tied to a signed URL (Step 1 uploads)
        //   "file_errors" — tied to a file_id (Steps 2, 3, 5)
        //   "job_errors"  — tied to a job_id  (Steps 4, 6)
        //   "other"       — anything not clearly tied to one of the above
        // Every entry carries a UTC timestamp (ISO-8601, e.g. 2025-06-03T10:07:42Z).

        public static JsonObject LoadErrors()
        {
            try
            {
                if (!File.Exists(ErrorsFile)) return new JsonObject();
                string txt = File.ReadAllText(ErrorsFile);
                return JsonNode.Parse(txt).AsObject();
            }
            catch
            {
                return new JsonObject();
            }
        }

        public static string UtcNow()
        {
            return DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");
        }

        /*
         * Log one error to errors.json. Pick the section by what the error relates to:
         *   refKey = "url" | "file_id" | "job_id"  (or null/"" -> goes to "other")
         * refValue is the actual URL / file_id / job_id (may be empty for "other").
         * raw is the original response body or detail (JsonNode), or null.
         */
        public static void LogError(string refKey, string refValue, int statusCode, string message, JsonNode raw)
        {
            string section;
            if (refKey == "url")           section = "url_errors";
            else if (refKey == "file_id")  section = "file_errors";
            else if (refKey == "job_id")   section = "job_errors";
            else                            section = "other";

            try
            {
                JsonObject all = LoadErrors();
                JsonArray arr = all[section] is JsonArray a
                    ? a.DeepClone().AsArray()
                    : new JsonArray();

                var entry = new JsonObject { ["timestamp_utc"] = UtcNow() };
                if (!string.IsNullOrEmpty(refKey) && !string.IsNullOrEmpty(refValue))
                    entry[refKey] = refValue;                 // "url" / "file_id" / "job_id"
                entry["status_code"] = statusCode;
                if (!string.IsNullOrEmpty(message)) entry["message"] = message;
                if (raw != null) entry["raw"] = raw.DeepClone();

                arr.Add(entry);                                // append (full history, keeps growing)
                all[section] = arr;
                File.WriteAllText(ErrorsFile, JsonSerializer.Serialize((JsonNode)all, Pretty));
                Console.WriteLine($"[error logged] -> errors.json ({section})"
                    + (!string.IsNullOrEmpty(refValue) ? $"  {refKey}: {refValue}" : ""));
            }
            catch (Exception e)
            {
                Console.WriteLine("[!] Could not write to errors.json: " + e.Message);
            }
        }

        // Convenience overloads
        public static void LogUrlError(string url, int statusCode, string message, JsonNode raw)
            => LogError("url", url, statusCode, message, raw);
        public static void LogFileError(string fileId, int statusCode, string message, JsonNode raw)
            => LogError("file_id", fileId, statusCode, message, raw);
        public static void LogJobError(string jobId, int statusCode, string message, JsonNode raw)
            => LogError("job_id", jobId, statusCode, message, raw);
        public static void LogOther(int statusCode, string message, JsonNode raw)
            => LogError("other", "", statusCode, message, raw);
    }
}
