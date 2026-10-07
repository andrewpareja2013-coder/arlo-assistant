# =============================================================
# UPDATER.PY
# Checks GitHub for a newer version of A.R.L.O. on startup.
# Normal updates show a one-line reminder; updates marked "force"
# (critical fixes) are downloaded and applied automatically.
# A copy with CHECK_FOR_UPDATES = False in config.py never checks
# for or installs updates (use this on your development copy).
# Updates keep the user's own settings in config.py and never
# delete files that only exist locally, like admin_tool.py.
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

# Settings in config.py that belong to whoever uses this copy. An update keeps their values for
# these. Everything else in config.py (like API_BASE and TEST_MODE) comes from the new version.
# If you add a new user-editable setting to config.py, add its name here too.
USER_SETTINGS = (
    "KNOWN_APPS", "APP_ALIASES", "KNOWN_WEBSITES", "ROUTINES",
    "WAKE_KEYWORD", "VOICE_ENABLED", "MICROPHONE_DEVICE",
    "CHECK_FOR_UPDATES",
    "FALLBACK_LATITUDE", "FALLBACK_LONGITUDE",
    "GPU_TEMP_WARN_C", "CPU_TEMP_WARN_C",
)

# Never overwritten or deleted by an update
PROTECTED_FILES = ("local_accounts.json", "admin_tool.py")
SKIPPED_FOLDERS = ("__pycache__",)


def updates_enabled():
    """False when config.py says CHECK_FOR_UPDATES = False (a development copy)."""
    try:
        import config
        return bool(getattr(config, "CHECK_FOR_UPDATES", True))
    except Exception:
        return True


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


def _read_saved_settings():
    """Reads this copy's own values for USER_SETTINGS out of config.py without running the file."""
    saved = {}
    try:
        with open(LOCAL_CONFIG_FILE, encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception:
        return saved
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in USER_SETTINGS:
                try:
                    saved[name] = ast.literal_eval(node.value)
                except Exception:
                    pass
    return saved


def _format_setting(name, value):
    """Formats a setting the way config.py writes it. Dicts keep their closing brace on its own
    line, because the app/website auto-add code looks for that line."""
    if isinstance(value, dict):
        lines = [f"{name} = {{"]
        for key, item in value.items():
            lines.append(f"    {key!r}: {item!r},")
        lines.append("}")
        return "\n".join(lines)
    return f"{name} = {value!r}"


def _apply_saved_settings(new_text, saved):
    """Puts the saved values into the new config.py text. For dicts, the new version's defaults are
    kept and the saved entries are laid on top, so the user's entries win. The result is checked
    to be valid Python before it is returned."""
    tree = ast.parse(new_text)
    lines = new_text.split("\n")

    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in saved:
                found[name] = node

    # Replace from the bottom up so earlier line numbers stay correct
    for name, node in sorted(found.items(), key=lambda item: item[1].lineno, reverse=True):
        value = saved[name]
        if isinstance(value, dict):
            try:
                default = ast.literal_eval(node.value)
                if isinstance(default, dict):
                    value = {**default, **value}
            except Exception:
                pass
        lines[node.lineno - 1:node.end_lineno] = _format_setting(name, value).split("\n")

    text = "\n".join(lines)

    missing = [name for name in saved if name not in found]
    if missing:
        text = text.rstrip("\n") + "\n\n# --- Restored from your previous config.py ---\n"
        for name in missing:
            text += _format_setting(name, saved[name]) + "\n"

    if not text.endswith("\n"):
        text += "\n"
    ast.parse(text)
    return text


def _merge_copy(source_dir, dest_dir):
    """Copies files one at a time. Files that exist only in dest_dir are never touched."""
    for item in os.listdir(source_dir):
        if item in PROTECTED_FILES or item in SKIPPED_FOLDERS:
            continue
        source = os.path.join(source_dir, item)
        destination = os.path.join(dest_dir, item)
        if os.path.isdir(source):
            os.makedirs(destination, exist_ok=True)
            _merge_copy(source, destination)
        else:
            shutil.copy2(source, destination)


def apply_update():
    """Downloads the latest version and merges it in. Returns True on success, False if anything failed."""
    extract_path = os.path.join(BASE_DIR, "_update_temp")
    try:
        response = requests.get(REPO_ZIP_URL, timeout=30)
        response.raise_for_status()
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
        zipfile.ZipFile(io.BytesIO(response.content)).extractall(extract_path)
        extracted_root = os.path.join(extract_path, "arlo-assistant-main", "A.R.L.O PRODUCTION VERSION")

        saved = _read_saved_settings()
        if os.path.exists(LOCAL_CONFIG_FILE):
            shutil.copy2(LOCAL_CONFIG_FILE, LOCAL_CONFIG_FILE + ".bak")

        with open(os.path.join(extracted_root, "config.py"), encoding="utf-8") as f:
            new_config = f.read()
        try:
            new_config = _apply_saved_settings(new_config, saved)
        except Exception:
            pass  # if the settings can't be merged, the new default config is used (old one is in config.py.bak)

        _merge_copy(extracted_root, BASE_DIR)

        with open(LOCAL_CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(new_config)
    except Exception:
        return False
    finally:
        shutil.rmtree(extract_path, ignore_errors=True)
    return True


def check_for_update():
    """Returns (message, restart_needed). message is None when there is nothing to report.
    restart_needed is True when a forced update was just installed."""
    if not updates_enabled():
        return None, False

    local_version = _get_local_version()
    remote_info = _get_remote_version_info()

    if remote_info is None:
        return None, False

    remote_version = remote_info.get("version", local_version)
    if remote_version == local_version:
        return None, False

    if remote_info.get("force"):
        if apply_update():
            return f"A critical update ({remote_version}) was installed. Please start A.R.L.O. again, sir.", True
        return f"A critical update ({remote_version}) is available but couldn't be installed. Type /update to try again.", False

    return f"An update ({remote_version}) is available. Type /update to install it.", False