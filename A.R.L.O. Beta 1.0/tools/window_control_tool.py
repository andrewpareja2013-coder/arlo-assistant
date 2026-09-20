# =============================================================
# WINDOW_CONTROL_TOOL.PY
# Controls window position and state: minimize, maximize, switch
# focus, and snap to screen layouts.
# =============================================================

import pygetwindow as gw
import tkinter as tk
from tools.registry import register


def _find_window(title_part):
    windows = gw.getAllWindows()
    for w in windows:
        if title_part.lower() in w.title.lower() and w.title.strip():
            return w
    return None


def _get_screen_size():
    root = tk.Tk()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.destroy()
    return width, height


def minimize_window(app_name):
    w = _find_window(app_name)
    if not w:
        return f"I couldn't find an open window for {app_name}, sir."
    w.minimize()
    return f"Minimized {app_name}, sir."


def maximize_window(app_name):
    w = _find_window(app_name)
    if not w:
        return f"I couldn't find an open window for {app_name}, sir."
    if w.isMinimized:
        w.restore()
    w.activate()
    w.maximize()
    return f"Maximized {app_name}, sir."


def switch_to_window(app_name):
    w = _find_window(app_name)
    if not w:
        return f"I couldn't find an open window for {app_name}, sir."
    w.activate()
    return f"Switched to {app_name}, sir."


def snap_window(app_name, position):
    w = _find_window(app_name)
    if not w:
        return f"I couldn't find an open window for {app_name}, sir."

    if w.isMinimized:
        w.restore()
    w.activate()

    screen_w, screen_h = _get_screen_size()
    position = position.lower().strip()

    if position == "left":
        w.moveTo(0, 0)
        w.resizeTo(int(screen_w * 2 / 3), screen_h)
    elif position == "right":
        w.moveTo(int(screen_w * 2 / 3), 0)
        w.resizeTo(int(screen_w * 1 / 3), screen_h)
    elif position == "full":
        w.moveTo(0, 0)
        w.resizeTo(screen_w, screen_h)
    elif position == "half-left":
        w.moveTo(0, 0)
        w.resizeTo(int(screen_w / 2), screen_h)
    elif position == "half-right":
        w.moveTo(int(screen_w / 2), 0)
        w.resizeTo(int(screen_w / 2), screen_h)
    elif position == "top-right-quarter":
        w.moveTo(int(screen_w / 2), 0)
        w.resizeTo(int(screen_w / 2), int(screen_h / 2))
    elif position == "bottom-right-quarter":
        w.moveTo(int(screen_w / 2), int(screen_h / 2))
        w.resizeTo(int(screen_w / 2), int(screen_h / 2))
    else:
        return f"I don't recognize the layout '{position}', sir. Options are: left, right, full, half-left, half-right, top-right-quarter, bottom-right-quarter."

    return f"Snapped {app_name} to {position}, sir."


register(
    name="minimize_window",
    description="Minimize a currently open application's window.",
    parameters={"type": "object", "properties": {"app_name": {"type": "string", "description": "Name of the app/window to minimize."}}, "required": ["app_name"]},
    function=minimize_window,
)

register(
    name="maximize_window",
    description="Maximize a currently open application's window.",
    parameters={"type": "object", "properties": {"app_name": {"type": "string", "description": "Name of the app/window to maximize."}}, "required": ["app_name"]},
    function=maximize_window,
)

register(
    name="switch_to_window",
    description="Switch focus to a currently open application's window.",
    parameters={"type": "object", "properties": {"app_name": {"type": "string", "description": "Name of the app/window to switch to."}}, "required": ["app_name"]},
    function=switch_to_window,
)

register(
    name="snap_window",
    description="Snap a window into a screen layout position. Options: left (two-thirds), right (one-third), full, half-left, half-right, top-right-quarter, bottom-right-quarter.",
    parameters={
        "type": "object",
        "properties": {
            "app_name": {"type": "string", "description": "Name of the app/window to snap."},
            "position": {"type": "string", "description": "One of: left, right, full, half-left, half-right, top-right-quarter, bottom-right-quarter."},
        },
        "required": ["app_name", "position"],
    },
    function=snap_window,
)