/*
 * Step4CheckJob.java  —  STEP 4: Check the job & get the tagged PDF
 * =================================================================
 * Checks every job saved by Step 3 and updates its status.
 *   - Jobs already "Completed" are skipped.
 *   - When a job is Completed, the full "details" block (download_url +
 *     expires_in_seconds) is saved on that job.
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

    public static void main(String[] args) throws Exception {
        String apiKey = AOD.apiKey();

        JsonArray jobProcess = AOD.getArray("job_process");

        if (jobProcess.size() == 0) {
            System.out.println("[X] No jobs found. Run Step3CreateJob.java first.");
            return;
        }

        boolean changed = false;
        int done = 0, pending = 0;

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
                pending++;
                continue;
            }

            String status;
            JsonObject details = null;
            JsonObject error = null;

            if (body.has("success") && !body.get("success").getAsBoolean()) {
                status = "Failed";
                error = body.has("error") && body.get("error").isJsonObject() ? body.getAsJsonObject("error") : new JsonObject();
            } else {
                JsonObject data = body.has("data") && body.get("data").isJsonObject() ? body.getAsJsonObject("data") : new JsonObject();
                status = data.has("status") && !data.get("status").isJsonNull() ? data.get("status").getAsString() : "unknown";
                if (data.has("details") && data.get("details").isJsonObject()) details = data.getAsJsonObject("details");
            }

            System.out.println("   - " + jobId + ": " + status);

            if (!status.equals(entry.has("status") ? entry.get("status").getAsString() : "")) {
                entry.addProperty("status", status);
                changed = true;
            }

            if (status.equalsIgnoreCase("completed") && details != null) {
                entry.add("details", details);
                entry.remove("error");
                changed = true;
                System.out.println("     download_url: " + (details.has("download_url") ? details.get("download_url").getAsString() : ""));
                System.out.println("     expires_in_seconds: " + (details.has("expires_in_seconds") ? details.get("expires_in_seconds").getAsString() : ""));
            }

            if (error != null) {
                entry.add("error", error);
                changed = true;
                System.out.println("     error: " + (error.has("code") ? error.get("code").getAsString() : "")
                        + " - " + (error.has("detail") ? error.get("detail").getAsString() : ""));
            }

            if (isFinished(status)) done++; else pending++;
        }

        if (changed) AOD.saveValue("job_process", jobProcess);

        System.out.println("\nSummary:");
        System.out.println("   finished: " + done + "  |  still processing: " + pending);

        if (pending > 0) {
            System.out.println("Some jobs are still processing. Wait a moment and run this file again.");
        } else {
            System.out.println("[OK] All jobs finished. To get a score report, put a file_id into config.json "
                    + "(\"report\": {\"file_id\": ...}) and run  Step5CreateReport.java");
        }
    }
}


/*
 * AOD — shared helper used by every step file.
 * You normally do NOT need to edit this. It holds the Base URL, builds the
 * Authorization header, sends requests, reads your values from config.json,
 * and reads/writes data.json.
 *
 * ALL editable values live in  config.json  — you never edit the .java files.
 */
class AOD {
    static final String BASE_URL = "https://staging.api.accessibilityondemand.space/api/v1";

    // Shared config lives in the REPO ROOT (one level up from this language folder).
    static final java.nio.file.Path CONFIG_FILE = java.nio.file.Paths.get("..", "config.json");
    // data.json stays inside THIS language folder.
    static final java.nio.file.Path DATA_FILE = java.nio.file.Paths.get("data.json");
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

    /** Read a String array from config (e.g. "signed_urls"), ignoring blank/placeholder entries. */
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
}
