# =============================================================
# WINDOW_CONTROL_TOOL.PY
# Controls window position and state: minimize, maximize, switch
# focus, and snap to screen layouts.
# Windows only for now: the pygetwindow library can't control windows
# on Linux, so there this file loads without registering any tools.
# =============================================================

import os
from tools.registry import register

try:
    import pygetwindow as gw
    _AVAILABLE = os.name == "nt"
except Exception:
    gw = None
    _AVAILABLE = False

# Each layout is (x, y, width, height) as fractions of the screen.
LAYOUTS = {
    "left": (0, 0, 2 / 3, 1),
    "right": (2 / 3, 0, 1 / 3, 1),
    "full": (0, 0, 1, 1),
    "half-left": (0, 0, 1 / 2, 1),
    "half-right": (1 / 2, 0, 1 / 2, 1),
    "top-right-quarter": (1 / 2, 0, 1 / 2, 1 / 2),
    "bottom-right-quarter": (1 / 2, 1 / 2, 1 / 2, 1 / 2),
}


def _find_window(title_part):
    title_part = str(title_part).lower().strip()
    if not title_part:
        return None
    try:
        for w in gw.getAllWindows():
            if w.title.strip() and title_part in w.title.lower():
                return w
    except Exception:
        return None
    return None


def _get_screen_size():
    import ctypes
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def _activate(w):
    """pygetwindow often raises an error even when activation worked, so errors are ignored."""
    try:
        w.activate()
    except Exception:
        pass


def _not_found(app_name):
    return f"I couldn't find an open window for {app_name}, sir."


def _failed(action, app_name):
    return f"I couldn't {action} {app_name}, sir."


def minimize_window(app_name):
    w = _find_window(app_name)
    if not w:
        return _not_found(app_name)
    try:
        w.minimize()
    except Exception:
        return _failed("minimize", app_name)
    return f"Minimized {app_name}, sir."


def maximize_window(app_name):
    w = _find_window(app_name)
    if not w:
        return _not_found(app_name)
    try:
        if w.isMinimized:
            w.restore()
        _activate(w)
        w.maximize()
    except Exception:
        return _failed("maximize", app_name)
    return f"Maximized {app_name}, sir."


def switch_to_window(app_name):
    w = _find_window(app_name)
    if not w:
        return _not_found(app_name)
    try:
        if w.isMinimized:
            w.restore()
    except Exception:
        pass
    _activate(w)
    return f"Switched to {app_name}, sir."


def snap_window(app_name, position):
    layout_name = str(position).lower().strip().replace(" ", "-").replace("_", "-")
    if layout_name not in LAYOUTS:
        return f"I don't recognize the layout '{position}', sir."

    w = _find_window(app_name)
    if not w:
        return _not_found(app_name)

    try:
        if w.isMinimized:
            w.restore()
        _activate(w)

        screen_w, screen_h = _get_screen_size()
        fx, fy, fw, fh = LAYOUTS[layout_name]
        w.moveTo(int(screen_w * fx), int(screen_h * fy))
        w.resizeTo(int(screen_w * fw), int(screen_h * fh))
    except Exception:
        return _failed("snap", app_name)

    return f"Snapped {app_name} to {layout_name}, sir."


if _AVAILABLE:
    register(
        name="minimize_window",
        description="Minimize a currently open application's window.",
        parameters={"type": "object", "properties": {"app_name": {"type": "string", "description": "Name of the app/window."}}, "required": ["app_name"]},
        function=minimize_window,
    )

    register(
        name="maximize_window",
        description="Maximize a currently open application's window.",
        parameters={"type": "object", "properties": {"app_name": {"type": "string", "description": "Name of the app/window."}}, "required": ["app_name"]},
        function=maximize_window,
    )

    register(
        name="switch_to_window",
        description="Switch focus to a currently open application's window.",
        parameters={"type": "object", "properties": {"app_name": {"type": "string", "description": "Name of the app/window."}}, "required": ["app_name"]},
        function=switch_to_window,
    )

    register(
        name="snap_window",
        description="Snap a window into a screen layout position: left, right, full, half-left, half-right, top-right-quarter, bottom-right-quarter.",
        parameters={
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "Name of the app/window."},
                "position": {"type": "string", "description": "Layout position."},
            },
            "required": ["app_name", "position"],
        },
        function=snap_window,
    )