# =============================================================
# HARDWARE.PY
# Detects the user's CPU/GPU and sets personalized temperature
# thresholds, and (on Windows) silently launches LibreHardwareMonitor
# in the background if it's not already running.
# =============================================================

import os
import asyncio
import subprocess
import psutil
import security

if os.name == "nt":
    from librehardwaremonitor_api import LibreHardwareMonitorClient

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LHM_PATH = os.path.join(BASE_DIR, "LibreHardwareMonitor", "LibreHardwareMonitor.exe")


async def _fetch_hardware_data_windows():
    client = LibreHardwareMonitorClient("localhost", 8085)
    return await client.get_data()


def _fetch_hardware_data_linux():
    """Runs the 'sensors' command (from lm-sensors) and returns raw text output."""
    try:
        result = subprocess.run(["sensors"], capture_output=True, text=True, timeout=5)
        return result.stdout
    except Exception:
        return ""


def _detect_is_intel():
    """Checks /proc/cpuinfo on Linux, or sensor names on Windows, to guess the CPU vendor."""
    if os.name == "nt":
        try:
            data = asyncio.run(_fetch_hardware_data_windows())
            return any("intel" in s.name.lower() or "core" in s.name.lower() for s in data.sensor_data.values())
        except Exception:
            return True
    else:
        try:
            with open("/proc/cpuinfo") as f:
                content = f.read().lower()
            return "intel" in content
        except Exception:
            return True


def detect_and_save_thresholds():
    """Checks if this account already has saved thresholds; if not, detects hardware and picks reasonable safe limits."""
    existing_cpu = security.get_setting("cpu_temp_warn", None)
    existing_gpu = security.get_setting("gpu_temp_warn", None)

    if existing_cpu is not None and existing_gpu is not None:
        return

    is_intel = _detect_is_intel()
    cpu_warn = 95 if is_intel else 90
    gpu_warn = 90

    security.save_setting("cpu_temp_warn", cpu_warn)
    security.save_setting("gpu_temp_warn", gpu_warn)


def get_cpu_temp_warn():
    return float(security.get_setting("cpu_temp_warn", 90))


def get_gpu_temp_warn():
    return float(security.get_setting("gpu_temp_warn", 85))


def is_lhm_running():
    """Windows only: checks if LibreHardwareMonitor is already running."""
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] and "librehardwaremonitor" in proc.info["name"].lower():
            return True
    return False


def ensure_lhm_running():
    """Windows only: launches LibreHardwareMonitor silently if it's not already running."""
    if os.name != "nt":
        return
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