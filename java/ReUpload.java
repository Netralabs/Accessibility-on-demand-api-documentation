/*
 * ReUpload.java  —  Retry files whose upload Failed
 * =================================================
 * When Step 2 (Step2CheckUpload.java) shows a file's status as "failed" and
 * "can_reupload" is true, this file retries the upload for those files by
 * calling  POST /files/re-upload/{file_id}  for each of them.
 *
 * It reads the files saved in data.json, picks the ones that failed and can be
 * re-uploaded, and re-uploads each one. Re-uploading restarts the background
 * transfer (the status goes back to "Uploading"), so afterwards run
 * Step2CheckUpload.java again to see whether it finished.
 *
 * A file whose status is failed with "can_reupload": false can't be recovered —
 * upload a fresh copy with Step1Upload.java instead.
 *
 * EDIT NOTHING HERE. Your api_key lives in  config.json
 *
 * How to run (Java 11+):
 *   Mac/Linux:  java -cp ".:lib/gson.jar" ReUpload.java
 *   Windows:    java -cp ".;lib\gson.jar" ReUpload.java
 */

import com.google.gson.*;

public class ReUpload {

    static boolean canReupload(JsonObject o) {
        return o.has("can_reupload") && !o.get("can_reupload").isJsonNull()
                && o.get("can_reupload").getAsBoolean();
    }

    /** The re-upload response wraps the file info in 'data' — return it (or empty). */
    static JsonObject readData(JsonObject body) {
        if (body.has("data") && body.get("data").isJsonObject()) {
            return body.getAsJsonObject("data");
        }
        return new JsonObject();
    }

    public static void main(String[] args) throws Exception {
        String apiKey = AOD.apiKey();

        JsonArray fileUploads = AOD.getArray("file_uploads");

        if (fileUploads.size() == 0) {
            System.out.println("[X] No files found. Run Step1Upload.java first.");
            return;
        }

        // Split the failed files into 'can retry' vs 'cannot retry'.
        java.util.List<JsonObject> retryable = new java.util.ArrayList<>();
        java.util.List<JsonObject> blocked = new java.util.ArrayList<>();
        for (JsonElement el : fileUploads) {
            JsonObject entry = el.getAsJsonObject();
            String status = entry.has("status") && !entry.get("status").isJsonNull()
                    ? entry.get("status").getAsString() : "";
            if (status.equalsIgnoreCase("failed")) {
                if (canReupload(entry)) retryable.add(entry); else blocked.add(entry);
            }
        }

        if (retryable.isEmpty()) {
            if (!blocked.isEmpty()) {
                System.out.println("[!] Some files failed but cannot be re-uploaded (can_reupload = false):");
                for (JsonObject e : blocked) {
                    System.out.println("   - " + e.get("file_id").getAsString() + ": "
                            + AOD.getString(e, "uploading_error", "upload failed"));
                }
                System.out.println("    These can't be recovered — upload a fresh copy with  Step1Upload.java");
            } else {
                System.out.println("[OK] No failed files to re-upload.");
                System.out.println("    (Run  Step2CheckUpload.java  first — it marks a file 'failed' if its upload fails.)");
            }
            return;
        }

        System.out.println("Re-uploading " + retryable.size() + " failed file(s)...\n");

        boolean changed = false;
        int started = 0;

        for (JsonObject entry : retryable) {
            String fileId = entry.get("file_id").getAsString();

            java.net.http.HttpResponse<String> resp =
                    AOD.postNoBody(AOD.BASE_URL + "/files/re-upload/" + fileId, apiKey);

            if (resp.statusCode() != 200) {
                System.out.println("   - " + fileId + ": re-upload failed (status code " + resp.statusCode() + ")");
                JsonElement raw = null;
                try {
                    raw = JsonParser.parseString(resp.body());
                } catch (Exception ignored) {}
                AOD.logFileError(fileId, resp.statusCode(), "Re-upload request failed", raw);
                continue;
            }

            JsonObject body;
            try {
                body = JsonParser.parseString(resp.body()).getAsJsonObject();
            } catch (Exception e) {
                System.out.println("   - " + fileId + ": could not read response");
                AOD.logFileError(fileId, resp.statusCode(), "Could not read/parse re-upload response", null);
                continue;
            }

            String newStatus = AOD.getString(readData(body), "uploading_status", "Uploading");
            // A successful re-upload restarts the background transfer. Reset our tracked
            // status so Step 2 will check it again, and clear the old failure info.
            entry.addProperty("status", newStatus);
            entry.remove("uploading_error");
            entry.remove("can_reupload");
            System.out.println("   - " + fileId + ": re-upload started (status: " + newStatus + ")");
            started++;
            changed = true;
        }

        if (changed) AOD.saveValue("file_uploads", fileUploads);

        String line = "   re-upload started: " + started
                + "  |  couldn't start: " + (retryable.size() - started);
        if (!blocked.isEmpty()) line += "  |  not re-uploadable: " + blocked.size();
        System.out.println("\nSummary:");
        System.out.println(line);
        if (started > 0) {
            System.out.println("\nNext: run  Step2CheckUpload.java  again to see whether they finished uploading.");
        }
    }
}


/*
 * AOD — shared helper used by every step file.
 * You normally do NOT need to edit this. It holds the Base URL, builds the
 * Authorization header, sends requests, reads your values from config.json,
 * reads/writes data.json, and logs anything that is not a clean success to errors.json.
 *
 * ALL editable values live in  config.json  — you never edit the .java files.
 */
class AOD {
    static final String BASE_URL = "https://api.accessibilityondemand.space/api/v1";

    // Shared config lives in the REPO ROOT (one level up from this language folder).
    static final java.nio.file.Path CONFIG_FILE = java.nio.file.Paths.get("..", "config.json");
    // data.json (tracked, clean items) stays inside THIS language folder.
    static final java.nio.file.Path DATA_FILE = java.nio.file.Paths.get("data.json");
    // errors.json (anything that is NOT a clean success) also stays in this folder.
    static final java.nio.file.Path ERRORS_FILE = java.nio.file.Paths.get("errors.json");
    static final com.google.gson.Gson GSON =
            new com.google.gson.GsonBuilder().setPrettyPrinting().create();
    static final java.net.http.HttpClient CLIENT = java.net.http.HttpClient.newHttpClient();

    // ---------- config.json (the one file you edit) ----------

    static com.google.gson.JsonObject loadConfig() {
        try {
            if (!java.nio.file.Files.exists(CONFIG_FILE)) {
                System.out.println("[X] config.json was not found at ../config.json (the repo root). "
                        + "Run this file from inside the java folder, with config.json in the folder above it.");
                System.exit(1);
            }
            String txt = java.nio.file.Files.readString(CONFIG_FILE);
            return com.google.gson.JsonParser.parseString(txt).getAsJsonObject();
        } catch (Exception e) {
            System.out.println("[X] Could not read config.json (is the JSON valid?): " + e.getMessage());
            System.exit(1);
            return new com.google.gson.JsonObject(); // unreachable
        }
    }

    /** Read the API key, with a friendly error if it's still the placeholder. */
    static String apiKey() {
        String key = getString(loadConfig(), "api_key", "");
        if (key.isEmpty() || key.equals("aod-xxxxxxxxxxx")) {
            System.out.println("[X] Please set your real \"api_key\" in config.json "
                    + "(it is still the placeholder).");
            System.exit(1);
        }
        return key;
    }

    /** Read a String value from a JsonObject, or return the default if missing/null. */
    static String getString(com.google.gson.JsonObject obj, String key, String def) {
        if (obj != null && obj.has(key) && !obj.get(key).isJsonNull()) {
            return obj.get(key).getAsString();
        }
        return def;
    }

    /** Read an int value from a JsonObject, or return the default if missing/null. */
    static int getInt(com.google.gson.JsonObject obj, String key, int def) {
        if (obj != null && obj.has(key) && !obj.get(key).isJsonNull()) {
            try { return obj.get(key).getAsInt(); } catch (Exception ignored) {}
        }
        return def;
    }

    /** Read a nested object (e.g. "process", "report") from config, or empty object. */
    static com.google.gson.JsonObject getObject(com.google.gson.JsonObject obj, String key) {
        if (obj != null && obj.has(key) && obj.get(key).isJsonObject()) {
            return obj.getAsJsonObject(key);
        }
        return new com.google.gson.JsonObject();
    }

    /** Read a String array from config (e.g. "sign_urls"), ignoring blank/placeholder entries. */
    static java.util.List<String> getStringArray(com.google.gson.JsonObject obj, String key) {
        java.util.List<String> out = new java.util.ArrayList<>();
        if (obj != null && obj.has(key) && obj.get(key).isJsonArray()) {
            for (com.google.gson.JsonElement e : obj.getAsJsonArray(key)) {
                if (e == null || e.isJsonNull()) continue;
                String v = e.getAsString().trim();
                if (v.isEmpty() || v.startsWith("https://your-signed-url")) continue;
                out.add(v);
            }
        }
        return out;
    }

    // ---------- HTTP ----------

    static java.net.http.HttpResponse<String> post(String url, String apiKey, String jsonBody)
            throws Exception {
        java.net.http.HttpRequest req = java.net.http.HttpRequest.newBuilder()
                .uri(java.net.URI.create(url))
                .header("Authorization", "Bearer " + apiKey)
                .header("Content-Type", "application/json")
                .POST(java.net.http.HttpRequest.BodyPublishers.ofString(jsonBody))
                .build();
        return CLIENT.send(req, java.net.http.HttpResponse.BodyHandlers.ofString());
    }

    // POST with NO body — used by the re-upload endpoint (file_id is in the URL).
    // Send Authorization only; there is no body, so no Content-Type is set.
    static java.net.http.HttpResponse<String> postNoBody(String url, String apiKey) throws Exception {
        java.net.http.HttpRequest req = java.net.http.HttpRequest.newBuilder()
                .uri(java.net.URI.create(url))
                .header("Authorization", "Bearer " + apiKey)
                .POST(java.net.http.HttpRequest.BodyPublishers.noBody())
                .build();
        return CLIENT.send(req, java.net.http.HttpResponse.BodyHandlers.ofString());
    }

    static java.net.http.HttpResponse<String> get(String url, String apiKey) throws Exception {
        java.net.http.HttpRequest req = java.net.http.HttpRequest.newBuilder()
                .uri(java.net.URI.create(url))
                .header("Authorization", "Bearer " + apiKey)
                .GET()
                .build();
        return CLIENT.send(req, java.net.http.HttpResponse.BodyHandlers.ofString());
    }

    static com.google.gson.JsonObject showResponse(java.net.http.HttpResponse<String> response) {
        System.out.println("Status code: " + response.statusCode());
        try {
            com.google.gson.JsonObject body =
                    com.google.gson.JsonParser.parseString(response.body()).getAsJsonObject();
            System.out.println("Response:");
            System.out.println(GSON.toJson(body));
            return body;
        } catch (Exception e) {
            System.out.println("Response (text): " + response.body());
            return null;
        }
    }

    // ---------- data.json (shared between steps) ----------

    static com.google.gson.JsonObject loadData() {
        try {
            if (!java.nio.file.Files.exists(DATA_FILE)) return new com.google.gson.JsonObject();
            String txt = java.nio.file.Files.readString(DATA_FILE);
            return com.google.gson.JsonParser.parseString(txt).getAsJsonObject();
        } catch (Exception e) {
            return new com.google.gson.JsonObject();
        }
    }

    static void saveValue(String key, com.google.gson.JsonElement value) {
        try {
            com.google.gson.JsonObject data = loadData();
            data.add(key, value);
            java.nio.file.Files.writeString(DATA_FILE, GSON.toJson(data));
            System.out.println("[saved] '" + key + "' was saved to data.json");
        } catch (Exception e) {
            System.out.println("[!] Could not save to data.json: " + e.getMessage());
        }
    }

    static com.google.gson.JsonArray getArray(String key) {
        com.google.gson.JsonObject data = loadData();
        if (data.has(key) && data.get(key).isJsonArray()) {
            return data.getAsJsonArray(key);
        }
        return new com.google.gson.JsonArray();
    }

    static com.google.gson.JsonArray extractDetailBlocks(com.google.gson.JsonObject body) {
        if (body.has("data") && body.get("data").isJsonObject()) {
            com.google.gson.JsonObject data = body.getAsJsonObject("data");
            if (data.has("detail") && data.get("detail").isJsonArray()) {
                return data.getAsJsonArray("detail");
            }
        }
        if (body.has("error") && body.get("error").isJsonObject()) {
            com.google.gson.JsonObject err = body.getAsJsonObject("error");
            if (err.has("details") && err.get("details").isJsonArray()) {
                return err.getAsJsonArray("details");
            }
        }
        return new com.google.gson.JsonArray();
    }

    // ---------- errors.json (anything that is NOT a clean success) ----------
    //
    // Grouped, append-only history. Sections:
    //   "url_errors"  — tied to a signed URL (Step 1 uploads)
    //   "file_errors" — tied to a file_id (Steps 2, 3, 5, and ReUpload)
    //   "job_errors"  — tied to a job_id  (Steps 4, 6)
    //   "other"       — anything not clearly tied to one of the above
    // Every entry carries a UTC timestamp (ISO-8601, e.g. 2025-06-03T10:07:42Z).

    static com.google.gson.JsonObject loadErrors() {
        try {
            if (!java.nio.file.Files.exists(ERRORS_FILE)) return new com.google.gson.JsonObject();
            String txt = java.nio.file.Files.readString(ERRORS_FILE);
            return com.google.gson.JsonParser.parseString(txt).getAsJsonObject();
        } catch (Exception e) {
            return new com.google.gson.JsonObject();
        }
    }

    static String utcNow() {
        return java.time.format.DateTimeFormatter.ISO_INSTANT
                .format(java.time.Instant.now().truncatedTo(java.time.temporal.ChronoUnit.SECONDS));
    }

    /**
     * Log one error to errors.json. Pick the section by what the error relates to:
     *   refKey = "url" | "file_id" | "job_id"  (or null/"" -> goes to "other")
     * refValue is the actual URL / file_id / job_id (may be empty for "other").
     * raw is the original response body or detail (JsonElement), or null.
     */
    static void logError(String refKey, String refValue, int statusCode, String message,
                         com.google.gson.JsonElement raw) {
        String section;
        if ("url".equals(refKey))            section = "url_errors";
        else if ("file_id".equals(refKey))   section = "file_errors";
        else if ("job_id".equals(refKey))    section = "job_errors";
        else                                  section = "other";

        try {
            com.google.gson.JsonObject all = loadErrors();
            com.google.gson.JsonArray arr = all.has(section) && all.get(section).isJsonArray()
                    ? all.getAsJsonArray(section) : new com.google.gson.JsonArray();

            com.google.gson.JsonObject entry = new com.google.gson.JsonObject();
            entry.addProperty("timestamp_utc", utcNow());
            if (refKey != null && !refKey.isEmpty() && refValue != null && !refValue.isEmpty()) {
                entry.addProperty(refKey, refValue);   // "url" / "file_id" / "job_id"
            }
            entry.addProperty("status_code", statusCode);
            if (message != null && !message.isEmpty()) entry.addProperty("message", message);
            if (raw != null && !raw.isJsonNull()) entry.add("raw", raw);

            arr.add(entry);                 // append (full history, keeps growing)
            all.add(section, arr);
            java.nio.file.Files.writeString(ERRORS_FILE, GSON.toJson(all));
            System.out.println("[error logged] -> errors.json (" + section + ")"
                    + (refValue != null && !refValue.isEmpty() ? "  " + refKey + ": " + refValue : ""));
        } catch (Exception e) {
            System.out.println("[!] Could not write to errors.json: " + e.getMessage());
        }
    }

    // Convenience overloads
    static void logUrlError(String url, int statusCode, String message, com.google.gson.JsonElement raw) {
        logError("url", url, statusCode, message, raw);
    }
    static void logFileError(String fileId, int statusCode, String message, com.google.gson.JsonElement raw) {
        logError("file_id", fileId, statusCode, message, raw);
    }
    static void logJobError(String jobId, int statusCode, String message, com.google.gson.JsonElement raw) {
        logError("job_id", jobId, statusCode, message, raw);
    }
    static void logOther(int statusCode, String message, com.google.gson.JsonElement raw) {
        logError("other", "", statusCode, message, raw);
    }
}
