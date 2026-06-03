"""
helper.py
---------
Shared code used by all 6 scripts. You normally do NOT need to edit this file.

It does these things:
  1. Reads your values from the shared ../config.json (repo root).
  2. Builds the Base URL and the Authorization header for you.
  3. Saves clean tracked values (file_ids, job_ids) into the local data.json.
  4. Logs anything that is NOT a clean success into the local errors.json.

ALL editable values live in  ../config.json  — you never edit the .py files.
"""

import json
import os
import sys
from datetime import datetime, timezone

# The web address all the APIs live under (from Section 1 of the README).
BASE_URL = "https://staging.api.accessibilityondemand.space/api/v1"

# Shared config lives in the REPO ROOT (one level up from this folder).
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config.json")
# data.json (clean tracked items) is created in THIS folder.
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")
# errors.json (anything that is NOT a clean success) also stays in this folder.
ERRORS_FILE = os.path.join(os.path.dirname(__file__), "errors.json")


# ---------- config.json (the one file you edit) ----------

def load_config():
    """Reads ../config.json. Exits with a friendly message if missing/invalid."""
    if not os.path.exists(CONFIG_FILE):
        print(
            "[X] config.json was not found at ../config.json (the repo root). "
            "Run these scripts from inside this folder, with config.json in the folder above it."
        )
        sys.exit(1)
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[X] Could not read config.json (is the JSON valid?): {e}")
        sys.exit(1)


def api_key():
    """Reads the API key, with a friendly error if it's still the placeholder."""
    key = str(load_config().get("api_key", "")).strip()
    if not key or key == "aod-xxxxxxxxxxx":
        print('[X] Please set your real "api_key" in config.json (it is still the placeholder).')
        sys.exit(1)
    return key


def get_string_array(cfg, key):
    """Reads a string list (e.g. signed_urls), ignoring blank/placeholder entries."""
    arr = cfg.get(key) or []
    out = []
    for v in arr:
        if not isinstance(v, str):
            continue
        v = v.strip()
        if not v or v.startswith("https://your-signed-url"):
            continue
        out.append(v)
    return out


def build_headers(key):
    """Builds the headers (including your API key) sent with every request."""
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


# ---------- data.json (clean tracked items) ----------

def load_data():
    """Reads data.json. Returns an empty dict if the file doesn't exist yet."""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_value(key, value):
    """Saves one value into data.json (keeps everything already stored)."""
    data = load_data()
    data[key] = value
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[saved] '{key}' was saved to data.json")


def get_value(key, fallback=""):
    """Reads one value from data.json. Returns fallback if not found."""
    return load_data().get(key, fallback)


def show_response(response):
    """Prints the status code and the response body in a readable way."""
    print("Status code:", response.status_code)
    try:
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except ValueError:
        print("Response (text):", response.text)


# ---------- errors.json (anything that is NOT a clean success) ----------
#
# Grouped, append-only history. Sections:
#   "url_errors"  — tied to a signed URL (Step 1 uploads)
#   "file_errors" — tied to a file_id (Steps 2, 3, 5)
#   "job_errors"  — tied to a job_id  (Steps 4, 6)
#   "other"       — anything not clearly tied to one of the above
# Every entry carries a UTC timestamp (ISO-8601, e.g. 2025-06-03T10:07:42Z).

def load_errors():
    if not os.path.exists(ERRORS_FILE):
        return {}
    try:
        with open(ERRORS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def utc_now():
    # 2025-06-03T10:07:42Z  (seconds precision, no microseconds)
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_error(ref_key, ref_value, status_code, message, raw):
    """
    Log one error to errors.json. Pick the section by what it relates to:
      ref_key = "url" | "file_id" | "job_id"  (or None/"" -> goes to "other")
    ref_value is the actual URL / file_id / job_id (may be empty for "other").
    raw is the original response body or detail (any JSON-able value), or None.
    """
    if ref_key == "url":
        section = "url_errors"
    elif ref_key == "file_id":
        section = "file_errors"
    elif ref_key == "job_id":
        section = "job_errors"
    else:
        section = "other"

    try:
        all_errors = load_errors()
        arr = all_errors.get(section)
        if not isinstance(arr, list):
            arr = []

        entry = {"timestamp_utc": utc_now()}
        if ref_key and ref_value:
            entry[ref_key] = ref_value  # "url" / "file_id" / "job_id"
        entry["status_code"] = status_code
        if message:
            entry["message"] = message
        if raw is not None:
            entry["raw"] = raw

        arr.append(entry)  # append (full history, keeps growing)
        all_errors[section] = arr
        with open(ERRORS_FILE, "w") as f:
            json.dump(all_errors, f, indent=2)
        suffix = f"  {ref_key}: {ref_value}" if ref_value else ""
        print(f"[error logged] -> errors.json ({section}){suffix}")
    except OSError as e:
        print(f"[!] Could not write to errors.json: {e}")


# Convenience wrappers
def log_url_error(url, status_code, message, raw):
    log_error("url", url, status_code, message, raw)


def log_file_error(file_id, status_code, message, raw):
    log_error("file_id", file_id, status_code, message, raw)


def log_job_error(job_id, status_code, message, raw):
    log_error("job_id", job_id, status_code, message, raw)


def log_other(status_code, message, raw):
    log_error("other", "", status_code, message, raw)
