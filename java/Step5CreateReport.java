/*
 * Step5CreateReport.java  —  STEP 5: Request an axes4 score report
 * =================================================================
 * Asks the API to generate an axes4 accessibility score report for a file.
 * Returns a report job_id.
 *
 * How to run (Java 11+):
 *   Mac/Linux:  java -cp ".:lib/gson.jar" Step5CreateReport.java
 *   Windows:    java -cp ".;lib\gson.jar" Step5CreateReport.java
 *
 * What it saves to data.json:
 *   "report_process": [ { "file_id": "....", "job_id": "....", "status": "Processing" }, ... ]
 */

import com.google.gson.*;

public class Step5CreateReport {

    // ===== EDIT HERE =====
    static final String API_KEY = "aod-xxxxxxxxxxx"; // paste your key from Section 3
    static final String FILE_ID = "";                // the file_id to generate a report for
    // ===== STOP EDITING =====

    public static void main(String[] args) throws Exception {
        if (FILE_ID == null || FILE_ID.isEmpty()) {
            System.out.println("[X] No file_id given. Paste a FILE_ID above.");
            return;
        }

        JsonObject payload = new JsonObject();
        payload.addProperty("file_id", FILE_ID);

        System.out.println("Requesting a score report for file_id " + FILE_ID + " ...");
        java.net.http.HttpResponse<String> response = AOD.post(AOD.BASE_URL + "/report/", API_KEY, payload.toString());
        JsonObject body = AOD.showResponse(response);

        int code = response.statusCode();
        if ((code == 200 || code == 201) && body != null) {
            JsonObject data = body.has("data") && body.get("data").isJsonObject()
                    ? body.getAsJsonObject("data") : new JsonObject();
            String jobId = data.has("job_id") && !data.get("job_id").isJsonNull()
                    ? data.get("job_id").getAsString() : null;

            if (jobId != null) {
                JsonArray reportProcess = AOD.getArray("report_process");
                boolean exists = false;
                for (JsonElement e : reportProcess) {
                    JsonObject r = e.getAsJsonObject();
                    if (r.has("job_id") && r.get("job_id").getAsString().equals(jobId)) { exists = true; break; }
                }
                if (!exists) {
                    JsonObject entry = new JsonObject();
                    entry.addProperty("file_id", FILE_ID);
                    entry.addProperty("job_id", jobId);
                    entry.addProperty("status", "Processing");
                    reportProcess.add(entry);
                    AOD.saveValue("report_process", reportProcess);
                }
                System.out.println("\n[OK] Got report job_id: " + jobId);
                System.out.println("Next: run  Step6CheckReport.java");
            } else {
                System.out.println("\n[!] Could not find 'job_id' in the response. "
                        + "Check the printed response above and update the key name.");
            }
        } else {
            System.out.println("\n[X] Could not request the report. Check the file_id and status code above.");
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
