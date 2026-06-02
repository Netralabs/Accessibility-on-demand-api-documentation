/*
 * Step6CheckReport.java  —  STEP 6: Get the score report
 * =======================================================
 * Checks every report saved by Step 5 and updates its status.
 *   - Reports already "Completed" are skipped.
 *   - When a report is Completed, the full "details" block (download_url +
 *     expires_in_seconds) is saved, and any old error is removed.
 *
 * How to run (Java 11+):
 *   Mac/Linux:  java -cp ".:lib/gson.jar" Step6CheckReport.java
 *   Windows:    java -cp ".;lib\gson.jar" Step6CheckReport.java
 *
 * Note: the download_url expires after a short time (expires_in_seconds).
 * Download the score report PDF soon, or re-run this file.
 */

import com.google.gson.*;

public class Step6CheckReport {

    // ===== EDIT HERE =====
    static final String API_KEY = "aod-xxxxxxxxxxx"; // paste your key from Section 3
    // ===== STOP EDITING =====

    static boolean isFinished(String status) {
        return status != null && status.equalsIgnoreCase("completed");
    }

    public static void main(String[] args) throws Exception {
        JsonArray reportProcess = AOD.getArray("report_process");

        if (reportProcess.size() == 0) {
            System.out.println("[X] No reports found. Run Step5CreateReport.java first.");
            return;
        }

        boolean changed = false;
        int done = 0, pending = 0;

        System.out.println("Checking " + reportProcess.size() + " report(s)...\n");

        for (JsonElement el : reportProcess) {
            JsonObject entry = el.getAsJsonObject();
            String jobId = entry.get("job_id").getAsString();
            String current = entry.has("status") ? entry.get("status").getAsString() : "";

            if (isFinished(current)) {
                System.out.println("   - " + jobId + ": already " + current + " (skipped)");
                done++;
                continue;
            }

            java.net.http.HttpResponse<String> resp = AOD.get(AOD.BASE_URL + "/report/" + jobId, API_KEY);
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

        if (changed) AOD.saveValue("report_process", reportProcess);

        System.out.println("\nSummary:");
        System.out.println("   finished: " + done + "  |  still generating: " + pending);

        if (pending > 0) {
            System.out.println("Some reports are still generating. Wait a moment and run this file again.");
        } else {
            System.out.println("[OK] All reports finished. Download your score report PDF(s) using the URL(s) above.");
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
