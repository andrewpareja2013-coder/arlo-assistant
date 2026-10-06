# =============================================================
# UPDATER.PY
# Checks GitHub for a newer version of A.R.L.O. on startup.
# Normal updates show a one-line reminder; updates marked "force"
# (critical fixes) are downloaded and applied automatically.
# Apps and websites a user added on their own PC survive updates.
# =============================================================

import ast
import io
import json
import os
import shutil
import zipfile
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_VERSION_FILE = os.path.join(BASE_DIR, "version.json")
LOCAL_CONFIG_FILE = os.path.join(BASE_DIR, "config.py")
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/andrewpareja2013-coder/arlo-assistant/main/A.R.L.O%20PRODUCTION%20VERSION/version.json"
REPO_ZIP_URL = "https://github.com/andrewpareja2013-coder/arlo-assistant/archive/refs/heads/main.zip"

# Dictionaries in config.py that tools add entries to as the user opens new apps/websites
USER_EDITABLE_DICTS = ("KNOWN_APPS", "KNOWN_WEBSITES")


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


def _read_config_dict(name):
    """Reads a plain dict like KNOWN_APPS out of config.py without running the file."""
    try:
        with open(LOCAL_CONFIG_FILE, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        return ast.literal_eval(node.value)
    except Exception:
        pass
    return {}


def _add_dict_entries(name, entries):
    """Inserts entries into the NAME = { ... } block of config.py, just before its closing brace.
    The file is only written if the result is still valid Python."""
    if not entries:
        return
    with open(LOCAL_CONFIG_FILE, encoding="utf-8") as f:
        lines = f.readlines()

    in_block = False
    insert_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{name} = {{"):
            in_block = True
            continue
        if in_block and line.strip() == "}":
            insert_index = i
            break
    if insert_index is None:
        return

    lines[insert_index:insert_index] = [f"    {key!r}: {value!r},\n" for key, value in entries.items()]
    new_text = "".join(lines)
    ast.parse(new_text)  # raises if the edit broke the file, so nothing gets written
    with open(LOCAL_CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(new_text)


def apply_update():
    """Downloads the latest version and overwrites local files. Keeps local_accounts.json and any
    apps/websites the user added to config.py. Returns True on success, False if anything failed."""
    extract_path = os.path.join(BASE_DIR, "_update_temp")
    try:
        response = requests.get(REPO_ZIP_URL, timeout=30)
        response.raise_for_status()
        zip_data = zipfile.ZipFile(io.BytesIO(response.content))
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
        zip_data.extractall(extract_path)

        extracted_root = os.path.join(extract_path, "arlo-assistant-main", "A.R.L.O PRODUCTION VERSION")
        saved = {name: _read_config_dict(name) for name in USER_EDITABLE_DICTS}

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
    except Exception:
        return False
    finally:
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path, ignore_errors=True)

    # Put back anything the user added that the new config.py doesn't already have
    for name in USER_EDITABLE_DICTS:
        try:
            defaults = _read_config_dict(name)
            missing = {key: value for key, value in saved[name].items() if key not in defaults}
            _add_dict_entries(name, missing)
        except Exception:
            pass

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
        if apply_update():
            return f"A critical update ({remote_version}) was installed automatically. Please restart A.R.L.O., sir."
        return f"A critical update ({remote_version}) is available but couldn't be installed. Type /update to try again."

    return f"An update ({remote_version}) is available. Type /update to install it."