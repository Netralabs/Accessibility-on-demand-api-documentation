/*
 * Step2CheckUpload.java  —  STEP 2: Check upload status
 * ======================================================
 * Checks every file saved by Step 1 and updates its status.
 * Files already "uploaded" are skipped. Status is 'Uploading' or 'Uploaded'.
 *
 * How to run (Java 11+):
 *   Mac/Linux:  java -cp ".:lib/gson.jar" Step2CheckUpload.java
 *   Windows:    java -cp ".;lib\gson.jar" Step2CheckUpload.java
 */

import com.google.gson.*;

public class Step2CheckUpload {

    // ===== EDIT HERE =====
    static final String API_KEY = "aod-xxxxxxxxxxx"; // paste your key from Section 3
    // ===== STOP EDITING =====

    static String readStatus(JsonObject body) {
        if (body.has("status") && !body.get("status").isJsonNull()) {
            return body.get("status").getAsString();
        }
        if (body.has("data") && body.get("data").isJsonObject()) {
            JsonObject data = body.getAsJsonObject("data");
            if (data.has("uploading_status") && !data.get("uploading_status").isJsonNull()) {
                return data.get("uploading_status").getAsString();
            }
        }
        return null;
    }

    public static void main(String[] args) throws Exception {
        JsonArray fileUploads = AOD.getArray("file_uploads");

        if (fileUploads.size() == 0) {
            System.out.println("[X] No files found. Run Step1Upload.java first.");
            return;
        }

        boolean changed = false;
        int uploaded = 0, pending = 0;

        System.out.println("Checking " + fileUploads.size() + " file(s)...\n");

        for (JsonElement el : fileUploads) {
            JsonObject entry = el.getAsJsonObject();
            String fileId = entry.get("file_id").getAsString();
            String current = entry.has("status") ? entry.get("status").getAsString() : "";

            if (current.equalsIgnoreCase("uploaded")) {
                System.out.println("   - " + fileId + ": already uploaded (skipped)");
                uploaded++;
                continue;
            }

            java.net.http.HttpResponse<String> resp = AOD.get(AOD.BASE_URL + "/file-upload/" + fileId, API_KEY);
            if (resp.statusCode() != 200) {
                System.out.println("   - " + fileId + ": could not check (status code " + resp.statusCode() + ")");
                pending++;
                continue;
            }

            JsonObject body;
            try {
                body = JsonParser.parseString(resp.body()).getAsJsonObject();
            } catch (Exception e) {
                System.out.println("   - " + fileId + ": could not read response");
                pending++;
                continue;
            }

            String newStatus = readStatus(body);
            if (newStatus == null) newStatus = "unknown";
            System.out.println("   - " + fileId + ": " + newStatus);

            if (newStatus.equalsIgnoreCase("uploaded")) {
                entry.addProperty("status", "uploaded");
                changed = true;
                uploaded++;
            } else {
                pending++;
            }
        }

        if (changed) AOD.saveValue("file_uploads", fileUploads);

        System.out.println("\nSummary:");
        System.out.println("   uploaded: " + uploaded + "  |  still uploading: " + pending);

        if (pending > 0) {
            System.out.println("Some files are still uploading. Wait a moment and run this file again.");
        } else {
            System.out.println("[OK] All files uploaded. Next: run  Step3CreateJob.java");
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
