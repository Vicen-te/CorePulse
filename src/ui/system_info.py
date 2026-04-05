"""
System information gathering for the header bar.

Collects hostname, CPU model, GPU model, and uptime
for display in the main window header.
"""

# Standard library
import platform
import socket
from datetime import timedelta


def get_system_info() -> dict[str, str]:
    """
    Gather system information for the header bar.

    Returns:
        Dict with keys: hostname, os, cpu_model, gpu_model, uptime.
    """
    info: dict[str, str] = {}
    info["hostname"] = socket.gethostname()
    info["os"] = f"{platform.system()} {platform.release()}"

    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    info["cpu_model"] = line.split(":", 1)[1].strip()
                    break
    except OSError:
        info["cpu_model"] = "Unknown"

    try:
        from sensors.gpu_sensor import _ensure_nvml
        import pynvml
        _ensure_nvml()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info["gpu_model"] = pynvml.nvmlDeviceGetName(handle)
    except Exception:
        info["gpu_model"] = "No GPU"

    try:
        with open("/proc/uptime") as f:
            secs = float(f.read().split()[0])
            delta = timedelta(seconds=int(secs))
            d, h, m = delta.days, delta.seconds // 3600, (delta.seconds % 3600) // 60
            info["uptime"] = f"{d}d {h}h {m}m"
    except OSError:
        info["uptime"] = "?"

    return info
