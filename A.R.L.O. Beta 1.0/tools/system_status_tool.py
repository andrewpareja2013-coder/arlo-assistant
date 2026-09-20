# =============================================================
# SYSTEM_STATUS_TOOL.PY
# Reports live CPU/GPU usage and temperature via LibreHardwareMonitor.
# Warns if temps exceed the account's personalized thresholds
# (set automatically by hardware_limits.py).
# =============================================================

import asyncio
from librehardwaremonitor_api import LibreHardwareMonitorClient
from tools.registry import register
from hardware_limits import get_cpu_temp_warn, get_gpu_temp_warn


async def _fetch_hardware_data():
    client = LibreHardwareMonitorClient("localhost", 8085)
    return await client.get_data()


def get_system_status():
    """Fetches live CPU/GPU usage and temperature, with warnings against personalized thresholds."""
    try:
        data = asyncio.run(_fetch_hardware_data())
    except Exception:
        return "I'm unable to reach the hardware monitor right now, sir. Please ensure LibreHardwareMonitor is running with its remote web server enabled."

    cpu_percent = 0
    ram_percent = 0
    cpu_temp = None
    gpu_temp = None
    gpu_load = None

    for sensor_id, sensor in data.sensor_data.items():
        name = sensor.name.lower()
        device_type = sensor.device_type

        if sensor.type == "Load" and device_type == "CPU" and "total" in name:
            cpu_percent = sensor.value
        if sensor.type == "Load" and device_type == "RAM" and "memory load" in name:
            ram_percent = sensor.value
        if sensor.type == "Temperature" and device_type == "CPU" and "package" in name:
            cpu_temp = sensor.value
        if sensor.type == "Temperature" and device_type == "ATI" and "core" in name:
            gpu_temp = sensor.value
        if sensor.type == "Load" and device_type == "ATI" and "core" in name:
            gpu_load = sensor.value

    warnings = []
    cpu_warn = get_cpu_temp_warn()
    gpu_warn = get_gpu_temp_warn()

    if cpu_temp is not None and cpu_temp >= cpu_warn:
        warnings.append(f"CPU temp is high ({cpu_temp}°C, warning threshold {cpu_warn}°C)")
    if gpu_temp is not None and gpu_temp >= gpu_warn:
        warnings.append(f"GPU temp is high ({gpu_temp}°C, warning threshold {gpu_warn}°C)")

    summary = f"CPU: {cpu_percent}% at {cpu_temp}°C, RAM: {ram_percent}%"
    if gpu_load is not None:
        summary += f", GPU: {gpu_load}% at {gpu_temp}°C"

    if warnings:
        summary += "\nWarning: " + "; ".join(warnings)

    return summary


register(
    name="get_system_status",
    description="Get the current CPU usage, CPU temperature, RAM usage, and GPU usage/temperature. Use ONLY when the user explicitly asks about system performance, temps, or resource usage.",
    parameters={"type": "object", "properties": {}},
    function=get_system_status,
    safe_to_test=True,
)