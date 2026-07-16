/*
 * Step4CheckJob.java  —  STEP 4: Check the job & get the tagged PDF
 * =================================================================
 * Checks every job saved by Step 3 and updates its status.
 *   - Jobs already "Completed" are skipped.
 *   - When a job is Completed, the full "details" block (download_url +
 *     expires_in_seconds) is saved on that job.
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
 *     4. Run this file again — the download_url will now be included.
 *
 * EDIT NOTHING HERE. Your api_key lives in  config.json
 *
 * How to run (Java 11+):
 *   Mac/Linux:  java -cp ".:lib/gson.jar" Step4CheckJob.java
 *   Windows:    java -cp ".;lib\gson.jar" Step4CheckJob.java
 *
 * Note: the download_url expires after a short time (expires_in_seconds, e.g.
 * 300s = 5 minutes). Download the tagged PDF soon, or re-run this file.
 */

import com.google.gson.*;

public class Step4CheckJob {

    static boolean isFinished(String status) {
        return status != null && status.equalsIgnoreCase("completed");
    }

    /**
     * The API reports status="Completed" for two very different situations:
     *   1) Fully done  -> details has a download_url
     *   2) Waiting for manual review -> details has a "message" but NO download_url
     * Detect case 2 so we can label it distinctly and keep polling.
     */
    static boolean isManualReviewPending(String apiStatus, JsonObject details) {
        if (apiStatus == null || !apiStatus.equalsIgnoreCase("completed")) return false;
        if (details == null) return false;
        boolean hasDownload = details.has("download_url")
                && !details.get("download_url").isJsonNull()
                && !details.get("download_url").getAsString().isEmpty();
        boolean hasMessage = details.has("message")
                && !details.get("message").isJsonNull()
                && !details.get("message").getAsString().isEmpty();
        return !hasDownload && hasMessage;
    }

    public static void main(String[] args) throws Exception {
        String apiKey = AOD.apiKey();

        JsonArray jobProcess = AOD.getArray("job_process");

        if (jobProcess.size() == 0) {
            System.out.println("[X] No jobs found. Run Step3CreateJob.java first.");
            return;
        }

        boolean changed = false;
        int done = 0, awaiting = 0, stillProcessing = 0;

        System.out.println("Checking " + jobProcess.size() + " job(s)...\n");

        for (JsonElement el : jobProcess) {
            JsonObject entry = el.getAsJsonObject();
            String jobId = entry.get("job_id").getAsString();
            String current = entry.has("status") ? entry.get("status").getAsString() : "";

            if (isFinished(current)) {
                System.out.println("   - " + jobId + ": already " + current + " (skipped)");
                done++;
                continue;
            }

            java.net.http.HttpResponse<String> resp = AOD.get(AOD.BASE_URL + "/jobs/" + jobId, apiKey);
            JsonObject body;
            try {
                body = JsonParser.parseString(resp.body()).getAsJsonObject();
            } catch (Exception e) {
                System.out.println("   - " + jobId + ": could not check (status code " + resp.statusCode() + ")");
                AOD.logJobError(jobId, resp.statusCode(), "Could not read/parse job response", null);
                stillProcessing++;
                continue;
            }

            String apiStatus;
            JsonObject details = null;
            JsonObject error = null;

            if (body.has("success") && !body.get("success").getAsBoolean()) {
                apiStatus = "Failed";
                error = body.has("error") && body.get("error").isJsonObject() ? body.getAsJsonObject("error") : new JsonObject();
            } else {
                JsonObject data = body.has("data") && body.get("data").isJsonObject() ? body.getAsJsonObject("data") : new JsonObject();
                apiStatus = data.has("status") && !data.get("status").isJsonNull() ? data.get("status").getAsString() : "unknown";
                if (data.has("details") && data.get("details").isJsonObject()) details = data.getAsJsonObject("details");
            }

            // Distinguish the "completed but manual review pending" case locally so it
            // doesn't get bucketed with the fully-done jobs.
            boolean manualReviewPending = isManualReviewPending(apiStatus, details);
            String status = manualReviewPending ? "AwaitingManualReview" : apiStatus;

            System.out.println("   - " + jobId + ": " + status);

            if (!status.equals(entry.has("status") ? entry.get("status").getAsString() : "")) {
                entry.addProperty("status", status);
                changed = true;
            }

            if (manualReviewPending) {
                // Show a friendly, actionable note so the user knows exactly what to do.
                // We do NOT save details here (there's no download_url yet).
                System.out.println("     note: " + details.get("message").getAsString());
                System.out.println("     -> log in at https://app.accessibilityondemand.ai/login,");
                System.out.println("        open the batch, select the file, click Review,");
                System.out.println("        then click Complete on the last page.");
                System.out.println("        After that, run this file again to get the download_url.");
            }

            if (status.equalsIgnoreCase("completed") && details != null
                    && details.has("download_url") && !details.get("download_url").isJsonNull()) {
                entry.add("details", details);
                changed = true;
                System.out.println("     download_url: " + details.get("download_url").getAsString());
                System.out.println("     expires_in_seconds: " + (details.has("expires_in_seconds") ? details.get("expires_in_seconds").getAsString() : ""));
            }

            if (error != null) {
                // Failed jobs are not kept in data.json — they go to errors.json (job_errors).
                String code = error.has("code") ? error.get("code").getAsString() : "";
                String detail = error.has("detail") ? error.get("detail").getAsString() : "";
                System.out.println("     error: " + code + " - " + detail);
                AOD.logJobError(jobId, resp.statusCode(), (code + " " + detail).trim(), error);
            }

            if (isFinished(status)) {
                done++;
            } else if (status.equalsIgnoreCase("AwaitingManualReview")) {
                awaiting++;
            } else {
                stillProcessing++;
            }
        }

        if (changed) AOD.saveValue("job_process", jobProcess);

        // Collect the awaiting-review jobs so we can list them by id.
        java.util.List<JsonObject> awaitingList = new java.util.ArrayList<>();
        for (JsonElement el : jobProcess) {
            JsonObject entry = el.getAsJsonObject();
            String s = entry.has("status") ? entry.get("status").getAsString() : "";
            if (s.equalsIgnoreCase("AwaitingManualReview")) awaitingList.add(entry);
        }

        System.out.println("\nSummary:");
        System.out.println("   finished: " + done
                + "  |  awaiting manual review: " + awaiting
                + "  |  still processing: " + stillProcessing);

        if (!awaitingList.isEmpty()) {
            System.out.println("\nJobs ready for manual review:");
            for (JsonObject j : awaitingList) {
                System.out.println("   - job_id: " + (j.has("job_id") ? j.get("job_id").getAsString() : "")
                        + "  |  file_id: " + (j.has("file_id") ? j.get("file_id").getAsString() : ""));
            }
            System.out.println("   Log in at https://app.accessibilityondemand.ai/login, complete the review,");
            System.out.println("   then run this file again to get the download link.");
        }

        if (stillProcessing > 0) {
            System.out.println("\nSome jobs are still processing. Wait a moment and run this file again.");
        }

        if (awaiting == 0 && stillProcessing == 0) {
            System.out.println("[OK] All jobs finished. To get a score report, put a file_id into config.json "
                    + "(\"report\": {\"file_id\": ...}) and run  Step5CreateReport.java");
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
    //   "file_errors" — tied to a file_id (Steps 2, 3, 5)
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
