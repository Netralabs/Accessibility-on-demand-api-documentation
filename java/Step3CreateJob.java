/*
 * Step3CreateJob.java  —  STEP 3: Start processing the PDF
 * =========================================================
 * Sends an uploaded file for processing (tagging) and gets back a job_id.
 * You choose the processing LEVEL (1 or 2).
 *
 * How to run (Java 11+):
 *   Mac/Linux:  java -cp ".:lib/gson.jar" Step3CreateJob.java
 *   Windows:    java -cp ".;lib\gson.jar" Step3CreateJob.java
 *
 * What it saves to data.json:
 *   "job_process": [ { "file_id": "....", "job_id": "....", "status": "Queued" }, ... ]
 */

import com.google.gson.*;

public class Step3CreateJob {

    // ===== EDIT HERE =====
    static final String API_KEY = "aod-xxxxxxxxxxx"; // paste your key from Section 3
    static final String FILE_ID = "";                // an uploaded file_id to process
    static final int LEVEL = 1;                      // 1 or 2
    // ===== STOP EDITING =====

    public static void main(String[] args) throws Exception {
        if (FILE_ID == null || FILE_ID.isEmpty()) {
            System.out.println("[X] No file_id given. Paste an uploaded FILE_ID above.");
            return;
        }

        JsonObject payload = new JsonObject();
        payload.addProperty("file_id", FILE_ID);
        payload.addProperty("level", LEVEL);

        System.out.println("Starting a job for file_id " + FILE_ID + " at level " + LEVEL + " ...");
        java.net.http.HttpResponse<String> response = AOD.post(AOD.BASE_URL + "/jobs/", API_KEY, payload.toString());
        JsonObject body = AOD.showResponse(response);

        int code = response.statusCode();
        if (code == 409) {
            System.out.println("\n[Conflict] This is already processed: change file id " + FILE_ID);
        }

        if ((code == 200 || code == 201) && body != null) {
            JsonObject data = body.has("data") && body.get("data").isJsonObject()
                    ? body.getAsJsonObject("data") : new JsonObject();
            String jobId = data.has("job_id") && !data.get("job_id").isJsonNull()
                    ? data.get("job_id").getAsString() : null;

            if (jobId != null) {
                JsonArray jobProcess = AOD.getArray("job_process");
                boolean exists = false;
                for (JsonElement e : jobProcess) {
                    JsonObject j = e.getAsJsonObject();
                    if (j.has("job_id") && j.get("job_id").getAsString().equals(jobId)) { exists = true; break; }
                }
                if (!exists) {
                    JsonObject entry = new JsonObject();
                    entry.addProperty("file_id", FILE_ID);
                    entry.addProperty("job_id", jobId);
                    entry.addProperty("status", "Queued");
                    jobProcess.add(entry);
                    AOD.saveValue("job_process", jobProcess);
                }
                System.out.println("\n[OK] Got job_id: " + jobId);
                System.out.println("Next: run  Step4CheckJob.java");
            } else {
                System.out.println("\n[!] Could not find 'job_id' in the response. "
                        + "Check the printed response above and update the key name.");
            }
        } else {
            System.out.println("\n[X] Could not start the job. Check the file_id, level, and status code above.");
        }
    }
}

/*
 * AOD — shared helper used by every step file.
 * You normally do NOT need to edit this. It holds the Base URL,
 * builds the Authorization header, sends requests, and reads/writes data.json.
 */
class AOD {
    static final String BASE_URL = "https://staging.api.accessibilityondemand.space/api/v1";

    static final java.nio.file.Path DATA_FILE = java.nio.file.Paths.get("data.json");
    static final com.google.gson.Gson GSON =
            new com.google.gson.GsonBuilder().setPrettyPrinting().create();
    static final java.net.http.HttpClient CLIENT = java.net.http.HttpClient.newHttpClient();

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
