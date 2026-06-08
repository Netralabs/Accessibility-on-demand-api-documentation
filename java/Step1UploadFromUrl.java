/*
 * Step1UploadFromUrl.java  —  STEP 1 (option B): Upload from signed URLs
 * =====================================================================
 * Sends your signed URLs to the API and gets back a file_id for each
 * file that was accepted. Use this if your files already live in S3 or
 * Google Drive (or you already have signed URLs).
 *
 *   • Have PDFs on your computer instead? Use  Step1Upload.java  (direct upload).
 *   • Need a signed URL? See ../docs/getting-signed-urls.md
 *
 * EDIT NOTHING HERE. All your values live in  config.json
 *   (api_key, signed_urls, description).
 *
 * How to run (Java 11+):
 *   Mac/Linux:  java -cp ".:lib/gson.jar" Step1UploadFromUrl.java
 *   Windows:    java -cp ".;lib\gson.jar" Step1UploadFromUrl.java
 *
 * What it saves to data.json:
 *   "file_uploads": [ { "file_id": "....", "url": "....", "status": "Uploading" }, ... ]
 */

import com.google.gson.*;

public class Step1UploadFromUrl {

    public static void main(String[] args) throws Exception {
        // --- read everything from config.json ---
        JsonObject cfg = AOD.loadConfig();
        String apiKey = AOD.apiKey();
        String description = AOD.getString(cfg, "description", "");
        java.util.List<String> signedUrls = AOD.getStringArray(cfg, "signed_urls");

        if (signedUrls.isEmpty()) {
            System.out.println("[X] No signed URLs found. Add at least one real URL to "
                    + "\"signed_urls\" in config.json.");
            System.out.println("    (Or drop PDFs into the uploads/ folder and run  Step1Upload.java  instead.)");
            return;
        }

        String endpoint = AOD.BASE_URL + "/files/upload-from-url/";

        JsonObject payload = new JsonObject();
        JsonArray urls = new JsonArray();
        for (String u : signedUrls) urls.add(u);
        payload.add("sign_urls", urls);
        payload.addProperty("description", description);

        System.out.println("Uploading " + signedUrls.size() + " file(s)...");
        java.net.http.HttpResponse<String> response = AOD.post(endpoint, apiKey, payload.toString());
        JsonObject body = AOD.showResponse(response);

        int code = response.statusCode();
        if ((code == 200 || code == 207) && body != null) {
            JsonArray fileUploads = AOD.getArray("file_uploads");
            java.util.List<JsonObject> failed = new java.util.ArrayList<>();

            for (JsonElement blockEl : AOD.extractDetailBlocks(body)) {
                JsonObject block = blockEl.getAsJsonObject();
                if (block.has("successful_uploads")) {
                    for (JsonElement itEl : block.getAsJsonArray("successful_uploads")) {
                        JsonObject it = itEl.getAsJsonObject();
                        if (it.has("file_id") && !it.get("file_id").isJsonNull()) {
                            JsonObject entry = new JsonObject();
                            entry.addProperty("file_id", it.get("file_id").getAsString());
                            entry.addProperty("url", it.has("url") && !it.get("url").isJsonNull()
                                    ? it.get("url").getAsString() : "");
                            entry.addProperty("status", it.has("status") && !it.get("status").isJsonNull()
                                    ? it.get("status").getAsString() : "Uploading");
                            fileUploads.add(entry);
                        }
                    }
                }
                if (block.has("failed_uploads")) {
                    for (JsonElement itEl : block.getAsJsonArray("failed_uploads")) {
                        failed.add(itEl.getAsJsonObject());
                    }
                }
            }

            if (fileUploads.size() > 0) {
                AOD.saveValue("file_uploads", fileUploads);
                System.out.println("\n[OK] Uploaded files (status will be 'Uploading' at first):");
                for (JsonElement e : fileUploads) {
                    JsonObject f = e.getAsJsonObject();
                    System.out.println("   - file_id: " + f.get("file_id").getAsString()
                            + "  |  status: " + f.get("status").getAsString());
                }
                System.out.println("\nNext: run  Step2CheckUpload.java");
            } else {
                System.out.println("\n[!] No files were accepted. See the failures below.");
            }

            if (!failed.isEmpty()) {
                System.out.println("\n[!] Some files failed (logged to errors.json):");
                for (JsonObject f : failed) {
                    String fUrl = f.has("url") && !f.get("url").isJsonNull() ? f.get("url").getAsString() : "";
                    String reason = f.has("detail") && !f.get("detail").isJsonNull() ? f.get("detail").getAsString() : "";
                    System.out.println("   - URL: " + fUrl);
                    System.out.println("     reason: " + reason);
                    // 207 partial-failure item -> goes to errors.json under url_errors
                    AOD.logUrlError(fUrl, code, reason, f);
                }
            }
        } else {
            System.out.println("\n[X] Upload request failed. Check your api_key, your signed_urls, "
                    + "and the status code above.");
            // whole-request failure (non-2xx) -> errors.json
            AOD.logOther(code, "File-upload request failed", body != null ? body : null);
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
    static final String BASE_URL = "https://staging.api.accessibilityondemand.space/api/v1";

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

    // ---------- direct file upload (multipart/form-data) ----------

    // uploads/ folder (repo root) — where users drop PDFs for direct upload (Step 1).
    static final java.nio.file.Path UPLOADS_DIR = java.nio.file.Paths.get("..", "uploads");

    /** Returns a sorted list of every .pdf in the repo-root uploads/ folder (empty if none). */
    static java.util.List<java.nio.file.Path> findLocalPdfs() {
        java.util.List<java.nio.file.Path> out = new java.util.ArrayList<>();
        if (!java.nio.file.Files.isDirectory(UPLOADS_DIR)) return out;
        try {
            java.util.List<java.nio.file.Path> all = new java.util.ArrayList<>();
            try (java.util.stream.Stream<java.nio.file.Path> s = java.nio.file.Files.list(UPLOADS_DIR)) {
                s.forEach(all::add);
            }
            all.sort(java.util.Comparator.comparing(p -> p.getFileName().toString().toLowerCase()));
            for (java.nio.file.Path p : all) {
                if (java.nio.file.Files.isRegularFile(p)
                        && p.getFileName().toString().toLowerCase().endsWith(".pdf")) {
                    out.add(p);
                }
            }
        } catch (Exception ignored) {}
        return out;
    }

    /*
     * POST one or more local files as multipart/form-data.
     * java.net.http has no built-in multipart writer, so we build the body by hand:
     * each file becomes a "files" part; an optional "description" text part is added.
     * Do NOT set Content-Type yourself elsewhere — we set the boundary here.
     */
    static java.net.http.HttpResponse<String> postMultipart(
            String url, String apiKey, java.util.List<java.nio.file.Path> files, String description)
            throws Exception {
        String boundary = "----aodBoundary" + System.currentTimeMillis();
        byte[] CRLF = "\r\n".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();

        for (java.nio.file.Path p : files) {
            String name = p.getFileName().toString();
            baos.write(("--" + boundary).getBytes(java.nio.charset.StandardCharsets.UTF_8));
            baos.write(CRLF);
            baos.write(("Content-Disposition: form-data; name=\"files\"; filename=\"" + name + "\"")
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8));
            baos.write(CRLF);
            baos.write("Content-Type: application/pdf".getBytes(java.nio.charset.StandardCharsets.UTF_8));
            baos.write(CRLF);
            baos.write(CRLF);
            baos.write(java.nio.file.Files.readAllBytes(p));
            baos.write(CRLF);
        }

        if (description != null && !description.isEmpty()) {
            baos.write(("--" + boundary).getBytes(java.nio.charset.StandardCharsets.UTF_8));
            baos.write(CRLF);
            baos.write("Content-Disposition: form-data; name=\"description\""
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8));
            baos.write(CRLF);
            baos.write(CRLF);
            baos.write(description.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            baos.write(CRLF);
        }

        baos.write(("--" + boundary + "--").getBytes(java.nio.charset.StandardCharsets.UTF_8));
        baos.write(CRLF);

        java.net.http.HttpRequest req = java.net.http.HttpRequest.newBuilder()
                .uri(java.net.URI.create(url))
                .header("Authorization", "Bearer " + apiKey)
                .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                .POST(java.net.http.HttpRequest.BodyPublishers.ofByteArray(baos.toByteArray()))
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
