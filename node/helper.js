/*
 * helper.js
 * ---------
 * Shared code used by all 6 scripts. You normally do NOT need to edit this file.
 *
 * It does three things:
 *   1. Builds the Base URL and the Authorization header for you.
 *   2. Saves important values (file_ids, job_ids) into 'data.json'.
 *   3. Reads those values back so the next script can use them automatically.
 *
 * Uses the built-in fetch (Node 18+) and the built-in fs module. No installs needed.
 */

const fs = require("fs");
const path = require("path");

// The web address all the APIs live under (from Section 1 of the README).
const BASE_URL = "https://staging.api.accessibilityondemand.space/api";

// 'data.json' is created in the same folder as these scripts.
const DATA_FILE = path.join(__dirname, "data.json");

function buildHeaders(apiKey) {
  return {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  };
}

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

module.exports = {
  BASE_URL,
  buildHeaders,
  loadData,
  saveValue,
  getValue,
  showResponse,
};
