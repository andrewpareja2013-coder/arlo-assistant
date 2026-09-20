# =============================================================
# HARDWARE_LIMITS.PY
# Detects the user's actual CPU/GPU and sets sensible temperature
# warning thresholds automatically, rather than one fixed value
# for everyone in config.py.
# =============================================================

import asyncio
from librehardwaremonitor_api import LibreHardwareMonitorClient
import security


async def _fetch_hardware_data():
    client = LibreHardwareMonitorClient("localhost", 8085)
    return await client.get_data()


def detect_and_save_thresholds():
    """
    Checks if this account already has saved thresholds; if not,
    detects the hardware and picks reasonable safe limits.
    """
    username = security.get_current_username()
    existing_cpu = security.get_setting(username, "cpu_temp_warn", None)
    existing_gpu = security.get_setting(username, "gpu_temp_warn", None)

    if existing_cpu is not None and existing_gpu is not None:
        return

    try:
        data = asyncio.run(_fetch_hardware_data())
        is_intel = any("intel" in s.name.lower() or "core" in s.name.lower() for s in data.sensor_data.values())

        cpu_warn = 95 if is_intel else 90
        gpu_warn = 90

        security.save_setting(username, "cpu_temp_warn", cpu_warn)
        security.save_setting(username, "gpu_temp_warn", gpu_warn)
    except Exception:
        security.save_setting(username, "cpu_temp_warn", 90)
        security.save_setting(username, "gpu_temp_warn", 85)


def get_cpu_temp_warn():
    return security.get_setting(security.get_current_username(), "cpu_temp_warn", 90)


def get_gpu_temp_warn():
    return security.get_setting(security.get_current_username(), "gpu_temp_warn", 85)