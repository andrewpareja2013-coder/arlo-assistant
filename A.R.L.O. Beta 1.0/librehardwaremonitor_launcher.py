# =============================================================
# LIBREHARDWAREMONITOR_LAUNCHER.PY
# Silently launches LibreHardwareMonitor in the background at
# startup if it's not already running, so system_status_tool.py
# works without the user manually opening it every time.
# =============================================================

import os
import subprocess
import psutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LHM_PATH = os.path.join(BASE_DIR, "LibreHardwareMonitor", "LibreHardwareMonitor.exe")


def is_lhm_running():
    """Checks if LibreHardwareMonitor is already running."""
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] and "librehardwaremonitor" in proc.info["name"].lower():
            return True
    return False


def ensure_lhm_running():
    """Launches LibreHardwareMonitor silently if it's not already running."""
    if is_lhm_running():
        return
    if not os.path.exists(LHM_PATH):
        return

    try:
        subprocess.Popen(
            LHM_PATH,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
        )
    except Exception:
        pass