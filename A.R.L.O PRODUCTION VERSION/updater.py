# =============================================================
# UPDATER.PY
# Checks GitHub for a newer version of A.R.L.O. on startup.
# Normal updates show a one-line reminder; updates marked "force"
# (critical fixes) are downloaded and applied automatically.
# =============================================================

import os
import json
import shutil
import zipfile
import io
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_VERSION_FILE = os.path.join(BASE_DIR, "version.json")
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/andrewpareja2013-coder/arlo-assistant/main/A.R.L.O%20PRODUCTION%20VERSION/version.json"
REPO_ZIP_URL = "https://github.com/andrewpareja2013-coder/arlo-assistant/archive/refs/heads/main.zip"


def _get_local_version():
    if not os.path.exists(LOCAL_VERSION_FILE):
        return "0.0.0"
    with open(LOCAL_VERSION_FILE) as f:
        return json.load(f).get("version", "0.0.0")


def _get_remote_version_info():
    try:
        response = requests.get(REMOTE_VERSION_URL, timeout=5)
        return response.json()
    except Exception:
        return None


def apply_update():
    """Downloads the latest version and overwrites local files, preserving local_accounts.json."""
    response = requests.get(REPO_ZIP_URL, timeout=30)
    zip_data = zipfile.ZipFile(io.BytesIO(response.content))

    extract_path = os.path.join(BASE_DIR, "_update_temp")
    zip_data.extractall(extract_path)

    extracted_root = os.path.join(extract_path, "arlo-assistant-main", "A.R.L.O PRODUCTION VERSION")

    for item in os.listdir(extracted_root):
        if item == "local_accounts.json":
            continue
        source = os.path.join(extracted_root, item)
        destination = os.path.join(BASE_DIR, item)
        if os.path.isdir(source):
            if os.path.exists(destination):
                shutil.rmtree(destination)
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

    shutil.rmtree(extract_path)
    return True


def check_for_update():
    """Checks for updates. Returns a reminder message string, or None if up to date / check failed."""
    local_version = _get_local_version()
    remote_info = _get_remote_version_info()

    if remote_info is None:
        return None

    remote_version = remote_info.get("version", local_version)
    if remote_version == local_version:
        return None

    if remote_info.get("force"):
        apply_update()
        return f"A critical update ({remote_version}) was installed automatically. Please restart A.R.L.O., sir."
    else:
        return f"An update ({remote_version}) is available. Type /update to install it."