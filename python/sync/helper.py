"""
helper.py
---------
Shared code used by all 6 scripts. You normally do NOT need to edit this file.

It does three things:
  1. Builds the Base URL and the Authorization header for you.
  2. Saves important values (file_ids, job_ids) into 'data.json'.
  3. Reads those values back so the next script can use them automatically.
"""

import json
import os

# ============================================================
# ===== EDIT HERE =====
# ============================================================
API_KEY = "aod-xxxxxxxxxxx"   # 👈 paste your key from Section 3

# ============================================================
# ===== STOP EDITING (the rest runs by itself) =====
# ============================================================


# The web address all the APIs live under (from Section 1 of the README).
BASE_URL = "https://staging.api.accessibilityondemand.space/api/v1"

# 'data.json' is created in the same folder as these scripts.
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")


def build_headers(api_key):
    """Builds the headers (including your API key) sent with every request."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


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
