# =============================================================
# SYSTEM_STATUS_TOOL.PY
# Reports live CPU/GPU usage and temperature. Uses LibreHardwareMonitor
# on Windows, and lm-sensors ('sensors' command) on Linux.
# Warns if temps exceed the account's personalized thresholds.
# =============================================================

import os
import re
import asyncio
from tools.registry import register
from hardware import get_cpu_temp_warn, get_gpu_temp_warn, _fetch_hardware_data_linux

GPU_DEVICE_TYPES = {"ati", "amd", "nvidia", "gpu"}
AMD_CPU_TEMP_NAMES = ("tctl", "tdie", "core (max)")


async def _fetch_hardware_data_windows():
    from librehardwaremonitor_api import LibreHardwareMonitorClient
    client = LibreHardwareMonitorClient("localhost", 8085)
    return await client.get_data()


def _get_status_windows():
    try:
        data = asyncio.run(_fetch_hardware_data_windows())
    except Exception:
        return None

    cpu_percent = None
    ram_percent = None
    cpu_temp = None
    cpu_temp_fallback = None
    gpu_temp = None
    gpu_load = None

    for sensor_id, sensor in data.sensor_data.items():
        name = str(sensor.name).lower()
        device_type = str(sensor.device_type).lower()

        try:
            value = float(sensor.value)
        except (TypeError, ValueError):
            continue

        if sensor.type == "Load" and device_type == "cpu" and "total" in name:
            cpu_percent = value
        if sensor.type == "Load" and device_type == "ram" and "memory load" in name:
            ram_percent = value
        if sensor.type == "Temperature" and device_type == "cpu":
            if "package" in name:
                cpu_temp = value
            elif any(key in name for key in AMD_CPU_TEMP_NAMES):
                cpu_temp_fallback = value
        if sensor.type == "Temperature" and device_type in GPU_DEVICE_TYPES and "core" in name:
            gpu_temp = value
        if sensor.type == "Load" and device_type in GPU_DEVICE_TYPES and "core" in name:
            gpu_load = value

    if cpu_temp is None:
        cpu_temp = cpu_temp_fallback

    return cpu_percent, ram_percent, cpu_temp, gpu_temp, gpu_load


def _get_status_linux():
    try:
        output = _fetch_hardware_data_linux() or ""
    except Exception:
        output = ""

    cpu_temp = None
    match = re.search(r"Package id 0:\s*\+?([\d.]+)°C", output)
    if match:
        cpu_temp = float(match.group(1))
    else:
        match = re.search(r"Tctl:\s*\+?([\d.]+)°C", output)
        if match:
            cpu_temp = float(match.group(1))

    gpu_temp = None
    match = re.search(r"edge:\s*\+?([\d.]+)°C", output)
    if match:
        gpu_temp = float(match.group(1))

    try:
        with open("/proc/loadavg") as f:
            load_1min = float(f.read().split()[0])
        cpu_percent = min(load_1min * 100 / os.cpu_count(), 100)
    except Exception:
        cpu_percent = None

    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        total = int(lines[0].split()[1])
        available = int(next(l for l in lines if l.startswith("MemAvailable")).split()[1])
        ram_percent = round((total - available) / total * 100, 1)
    except Exception:
        ram_percent = None

    return cpu_percent, ram_percent, cpu_temp, gpu_temp, None


def _num(value):
    return f"{value:.1f}".rstrip("0").rstrip(".")


def get_system_status():
    if os.name == "nt":
        result = _get_status_windows()
        if result is None:
            return "I'm unable to reach the hardware monitor right now, sir."
    else:
        result = _get_status_linux()

    cpu_percent, ram_percent, cpu_temp, gpu_temp, gpu_load = result

    warnings = []
    cpu_warn = get_cpu_temp_warn()
    gpu_warn = get_gpu_temp_warn()

    if cpu_temp is not None and cpu_temp >= cpu_warn:
        warnings.append(f"CPU temp is high ({_num(cpu_temp)}°C, warning threshold {cpu_warn}°C)")
    if gpu_temp is not None and gpu_temp >= gpu_warn:
        warnings.append(f"GPU temp is high ({_num(gpu_temp)}°C, warning threshold {gpu_warn}°C)")

    cpu_text = f"CPU: {_num(cpu_percent)}%" if cpu_percent is not None else "CPU: usage unavailable"
    if cpu_temp is not None:
        cpu_text += f" at {_num(cpu_temp)}°C"
    ram_text = f"RAM: {_num(ram_percent)}%" if ram_percent is not None else "RAM: unavailable"
    summary = f"{cpu_text}, {ram_text}"

    if gpu_load is not None:
        summary += f", GPU: {_num(gpu_load)}%"
        if gpu_temp is not None:
            summary += f" at {_num(gpu_temp)}°C"
    elif gpu_temp is not None:
        summary += f", GPU temp: {_num(gpu_temp)}°C"

    if warnings:
        summary += "\nWarning: " + "; ".join(warnings)

    return summary


register(
    name="get_system_status",
    description="Get the current CPU usage, CPU temperature, RAM usage, and GPU usage/temperature.",
    parameters={"type": "object", "properties": {}},
    function=get_system_status,
    safe_to_test=True,
)