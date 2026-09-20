# =============================================================
# APP_CONTROL_TOOL.PY
# Opens and closes applications by name. Known apps come from
# config.py's KNOWN_APPS. If an app isn't known, this searches the
# user's Desktop for a matching shortcut before falling back to
# asking the user for a manual path. Anything discovered this way
# gets written permanently into config.py.
# =============================================================

import os
import subprocess
import config
from tools.registry import register

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.py")


def _save_app_to_config(app_name, path):
    """Inserts a new entry into config.py's KNOWN_APPS dictionary, right before its closing brace."""
    with open(CONFIG_FILE, "r") as f:
        lines = f.readlines()

    exe_name = path.split("\\")[-1]
    new_line = f'    {app_name!r}: {{"open": {path!r}, "close": {exe_name!r}}},\n'

    in_known_apps = False
    insert_index = None

    for i, line in enumerate(lines):
        if line.strip().startswith("KNOWN_APPS = {"):
            in_known_apps = True
            continue
        if in_known_apps and line.strip() == "}":
            insert_index = i
            break

    if insert_index is not None:
        lines.insert(insert_index, new_line)
        with open(CONFIG_FILE, "w") as f:
            f.writelines(lines)
        return True
    return False


def _search_desktop(app_name):
    """Searches the user's Desktop for shortcuts matching the app name."""
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    matches = []
    if os.path.exists(desktop_path):
        for file in os.listdir(desktop_path):
            if app_name.lower() in file.lower() and (file.lower().endswith(".lnk") or file.lower().endswith(".url")):
                matches.append(os.path.join(desktop_path, file))
    return matches


def open_app(app_name):
    """Opens a known application by name, checking the Desktop if not already known or if the known path is invalid."""
    app_name = app_name.lower().strip()
    app_name = config.APP_ALIASES.get(app_name, app_name)

    program = None
    if app_name in config.KNOWN_APPS:
        candidate = config.KNOWN_APPS[app_name]["open"]
        if not os.path.isabs(candidate):
            program = candidate
        elif os.path.exists(candidate):
            program = candidate

    if not program:
        matches = _search_desktop(app_name)
        if matches:
            found_path = matches[0]
            config.KNOWN_APPS[app_name] = {"open": found_path, "close": found_path.split("\\")[-1]}
            _save_app_to_config(app_name, found_path)
            program = found_path
        else:
            return f"NEEDS_APP_PATH:{app_name}"

    try:
        subprocess.Popen(
            program,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.DETACHED_PROCESS
        )
        return f"Opening {app_name}, sir."
    except Exception as e:
        return f"I'm sorry sir, I was unable to open {app_name}. It may not be installed correctly."


def close_app(app_name):
    """Closes a known, currently running application by name."""
    app_name = app_name.lower().strip()
    app_name = config.APP_ALIASES.get(app_name, app_name)

    if app_name not in config.KNOWN_APPS:
        return f"I don't recognize an application called {app_name}, sir."

    exe_name = config.KNOWN_APPS[app_name]["close"]
    subprocess.run(
        ["taskkill", "/f", "/im", exe_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return f"Closing {app_name}, sir."


def add_and_open_app(app_name, path):
    """Adds a new app to KNOWN_APPS, saves it permanently in config.py, then opens it."""
    config.KNOWN_APPS[app_name] = {"open": path, "close": path.split("\\")[-1]}
    _save_app_to_config(app_name, path)
    return open_app(app_name)


register(
    name="open_app",
    description="Open an application on the user's PC. Use ONLY when the user explicitly asks to open, launch, or start a specific application.",
    parameters={
        "type": "object",
        "properties": {"app_name": {"type": "string", "description": "Name of the app to open, e.g. 'notepad' or 'chrome'."}},
        "required": ["app_name"],
    },
    function=open_app,
)

register(
    name="close_app",
    description="Close a running application. Use ONLY when the user explicitly asks to close, quit, or exit a specific application.",
    parameters={
        "type": "object",
        "properties": {"app_name": {"type": "string", "description": "Name of the app to close, e.g. 'notepad' or 'chrome'."}},
        "required": ["app_name"],
    },
    function=close_app,
    requires_confirmation=True,
)

register(
    name="add_and_open_app",
    description="Internal use only.",
    parameters={
        "type": "object",
        "properties": {
            "app_name": {"type": "string"},
            "path": {"type": "string"},
        },
        "required": ["app_name", "path"],
    },
    function=add_and_open_app,
)