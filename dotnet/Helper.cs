/*
 * Helper.cs
 * ---------
 * Shared code used by all 6 steps. You normally do NOT need to edit this file.
 *
 * It holds the Base URL, builds the Authorization header, sends requests,
 * and reads/writes data.json. Uses the built-in HttpClient and
 * System.Text.Json (no packages to install).
 */

using System;
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

        // ============================================================
        // ===== EDIT HERE =====
        // ============================================================
        public const string API_KEY = "aod-xxxxxxxxxxx"; // paste your key from Section 3
        // ============================================================
        // ===== STOP EDITING (the rest runs by itself) =====
        // ============================================================


        // The web address all the APIs live under (from Section 1 of the README).
        public const string BaseUrl = "https://staging.api.accessibilityondemand.space/api/v1";

        // data.json is created in the same folder you run from.
        public static readonly string DataFile =
            Path.Combine(Directory.GetCurrentDirectory(), "data.json");

        private static readonly HttpClient Client = new HttpClient();

        private static readonly JsonSerializerOptions Pretty =
            new JsonSerializerOptions { WriteIndented = true };

        public static async Task<HttpResponseMessage> PostAsync(string url, string apiKey, string jsonBody)
        {
            var req = new HttpRequestMessage(HttpMethod.Post, url);
            req.Headers.TryAddWithoutValidation("Authorization", "Bearer " + apiKey);
            req.Content = new StringContent(jsonBody, Encoding.UTF8, "application/json");
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

        // ---- data.json helpers ----
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
    }
}
