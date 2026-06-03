/*
 * helper.js
 * ---------
 * Shared code used by all 6 scripts. You normally do NOT need to edit this file.
 *
 * It does these things:
 *   1. Reads your values from the shared ../config.json (repo root).
 *   2. Builds the Base URL and the Authorization header for you.
 *   3. Saves clean tracked values (file_ids, job_ids) into the local data.json.
 *   4. Logs anything that is NOT a clean success into the local errors.json.
 *
 * ALL editable values live in  ../config.json  — you never edit the .js files.
 * Uses the built-in fetch (Node 18+) and the built-in fs module. No installs needed.
 */

const fs = require("fs");
const path = require("path");

// The web address all the APIs live under (from Section 1 of the README).
const BASE_URL = "https://staging.api.accessibilityondemand.space/api/v1";

// Shared config lives in the REPO ROOT (one level up from this node folder).
const CONFIG_FILE = path.join(__dirname, "..", "config.json");
// data.json (clean tracked items) is created in THIS node folder.
const DATA_FILE = path.join(__dirname, "data.json");
// errors.json (anything that is NOT a clean success) also stays in this folder.
const ERRORS_FILE = path.join(__dirname, "errors.json");

// ---------- config.json (the one file you edit) ----------

function loadConfig() {
  if (!fs.existsSync(CONFIG_FILE)) {
    console.log(
      "[X] config.json was not found at ../config.json (the repo root). " +
        "Run these scripts from inside the node folder, with config.json in the folder above it."
    );
    process.exit(1);
  }
  try {
    return JSON.parse(fs.readFileSync(CONFIG_FILE, "utf8"));
  } catch (e) {
    console.log("[X] Could not read config.json (is the JSON valid?): " + e.message);
    process.exit(1);
  }
}

// Read the API key, with a friendly error if it's still the placeholder.
function apiKey() {
  const cfg = loadConfig();
  const key = (cfg.api_key || "").trim();
  if (!key || key === "aod-xxxxxxxxxxx") {
    console.log('[X] Please set your real "api_key" in config.json (it is still the placeholder).');
    process.exit(1);
  }
  return key;
}

// Read a string array (e.g. signed_urls), ignoring blank/placeholder entries.
function getStringArray(cfg, key) {
  const arr = Array.isArray(cfg[key]) ? cfg[key] : [];
  return arr
    .map((v) => (typeof v === "string" ? v.trim() : ""))
    .filter((v) => v && !v.startsWith("https://your-signed-url"));
}

function buildHeaders(key) {
  return {
    Authorization: `Bearer ${key}`,
    "Content-Type": "application/json",
  };
}

// ---------- data.json (clean tracked items) ----------

function loadData() {
  if (!fs.existsSync(DATA_FILE)) return {};
  try {
    return JSON.parse(fs.readFileSync(DATA_FILE, "utf8"));
  } catch (e) {
    return {};
  }
}

function saveValue(key, value) {
  const data = loadData();
  data[key] = value;
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
  console.log(`[saved] '${key}' was saved to data.json`);
}

function getValue(key, fallback) {
  const data = loadData();
  return key in data ? data[key] : fallback;
}

// Prints the status code and the response body in a readable way.
// Returns the parsed JSON body (or null if the body was not JSON).
async function showResponse(response) {
  console.log("Status code:", response.status);
  const text = await response.text();
  try {
    const body = JSON.parse(text);
    console.log("Response:");
    console.log(JSON.stringify(body, null, 2));
    return body;
  } catch (e) {
    console.log("Response (text):", text);
    return null;
  }
}

// ---------- errors.json (anything that is NOT a clean success) ----------
//
// Grouped, append-only history. Sections:
//   "url_errors"  — tied to a signed URL (Step 1 uploads)
//   "file_errors" — tied to a file_id (Steps 2, 3, 5)
//   "job_errors"  — tied to a job_id  (Steps 4, 6)
//   "other"       — anything not clearly tied to one of the above
// Every entry carries a UTC timestamp (ISO-8601, e.g. 2025-06-03T10:07:42Z).

function loadErrors() {
  if (!fs.existsSync(ERRORS_FILE)) return {};
  try {
    return JSON.parse(fs.readFileSync(ERRORS_FILE, "utf8"));
  } catch (e) {
    return {};
  }
}

function utcNow() {
  // 2025-06-03T10:07:42Z  (seconds precision, no milliseconds)
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

/*
 * Log one error to errors.json. Pick the section by what the error relates to:
 *   refKey = "url" | "file_id" | "job_id"  (or null/"" -> goes to "other")
 * refValue is the actual URL / file_id / job_id (may be empty for "other").
 * raw is the original response body or detail object, or null.
 */
function logError(refKey, refValue, statusCode, message, raw) {
  let section;
  if (refKey === "url") section = "url_errors";
  else if (refKey === "file_id") section = "file_errors";
  else if (refKey === "job_id") section = "job_errors";
  else section = "other";

  try {
    const all = loadErrors();
    const arr = Array.isArray(all[section]) ? all[section] : [];

    const entry = { timestamp_utc: utcNow() };
    if (refKey && refValue) entry[refKey] = refValue; // "url" / "file_id" / "job_id"
    entry.status_code = statusCode;
    if (message) entry.message = message;
    if (raw !== undefined && raw !== null) entry.raw = raw;

    arr.push(entry); // append (full history, keeps growing)
    all[section] = arr;
    fs.writeFileSync(ERRORS_FILE, JSON.stringify(all, null, 2));
    console.log(
      `[error logged] -> errors.json (${section})` +
        (refValue ? `  ${refKey}: ${refValue}` : "")
    );
  } catch (e) {
    console.log("[!] Could not write to errors.json: " + e.message);
  }
}

// Convenience wrappers
const logUrlError = (url, code, msg, raw) => logError("url", url, code, msg, raw);
const logFileError = (fileId, code, msg, raw) => logError("file_id", fileId, code, msg, raw);
const logJobError = (jobId, code, msg, raw) => logError("job_id", jobId, code, msg, raw);
const logOther = (code, msg, raw) => logError("other", "", code, msg, raw);

module.exports = {
  BASE_URL,
  loadConfig,
  apiKey,
  getStringArray,
  buildHeaders,
  loadData,
  saveValue,
  getValue,
  showResponse,
  loadErrors,
  utcNow,
  logError,
  logUrlError,
  logFileError,
  logJobError,
  logOther,
};
