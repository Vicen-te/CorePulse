"""
GPU temperature sensor reader.

Supports NVIDIA GPUs via pynvml (NVML C library bindings) and
AMD GPUs via sysfs hwmon. If no GPU is detected, is_available()
returns False gracefully.
"""

# Standard library
import glob
from pathlib import Path

# Local
from sensors.base_sensor import BaseSensor

# Try to import pynvml for NVIDIA support
try:
    import pynvml
    _NVML_AVAILABLE = True
except ImportError:
    _NVML_AVAILABLE = False

_nvml_initialized: bool = False


def _ensure_nvml() -> bool:
    """
    Initialize NVML if not already done.

    Returns:
        True if NVML is ready to use, False otherwise.
    """
    global _nvml_initialized
    if _nvml_initialized:
        return True
    if not _NVML_AVAILABLE:
        return False
    try:
        pynvml.nvmlInit()
        _nvml_initialized = True
        return True
    except pynvml.NVMLError:
        return False


def shutdown_nvml() -> None:
    """Shut down NVML cleanly. Call on application exit."""
    global _nvml_initialized
    if _nvml_initialized:
        try:
            pynvml.nvmlShutdown()
        except pynvml.NVMLError:
            pass
        _nvml_initialized = False


class NvidiaGpuSensor(BaseSensor):
    """
    Reads NVIDIA GPU temperature using pynvml (NVML C library).

    Direct library calls instead of subprocess, typically <1ms per read.

    Attributes:
        gpu_index: Zero-based index of the NVIDIA GPU.
        gpu_name: Model name reported by NVML.
    """

    def __init__(self, gpu_index: int, gpu_name: str) -> None:
        """Initialize an NVIDIA GPU sensor.

        Args:
            gpu_index: Zero-based GPU index.
            gpu_name: Human-readable GPU model name.
        """
        self._gpu_index = gpu_index
        self._gpu_name = gpu_name
        self._handle = None
        self._available = True

        try:
            self._handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
        except pynvml.NVMLError:
            self._available = False

    def get_temperature(self) -> float:
        """Return the current GPU temperature in Celsius.

        Returns:
            Temperature reading, or 0.0 if NVML fails.
        """
        if self._handle is None:
            return 0.0
        try:
            return float(pynvml.nvmlDeviceGetTemperature(
                self._handle, pynvml.NVML_TEMPERATURE_GPU
            ))
        except pynvml.NVMLError:
            return 0.0

    def get_name(self) -> str:
        """Return the human-readable GPU name."""
        return f"GPU {self._gpu_name}"

    def is_available(self) -> bool:
        """Check whether this NVIDIA GPU is accessible."""
        return self._available


class AmdGpuSensor(BaseSensor):
    """
    Reads AMD GPU temperature via sysfs hwmon.

    Looks for temperature files under /sys/class/drm/card*/device/hwmon/
    which is the standard path for AMD GPU temperature reporting on Linux.

    Attributes:
        temp_path: Path to the hwmon temp1_input file.
        card_name: Identifier for this GPU card.
    """

    def __init__(self, temp_path: str, card_name: str) -> None:
        """Initialize an AMD GPU sensor.

        Args:
            temp_path: Full path to temp1_input sysfs file.
            card_name: Human-readable card identifier.
        """
        self._temp_path = Path(temp_path)
        self._card_name = card_name

    def get_temperature(self) -> float:
        """Return the current GPU temperature in Celsius.

        Returns:
            Temperature reading, or 0.0 if the file cannot be read.
        """
        try:
            raw = self._temp_path.read_text().strip()
            return int(raw) / 1000  # sysfs reports millidegrees
        except (OSError, ValueError):
            return 0.0

    def get_name(self) -> str:
        """Return the human-readable GPU name."""
        return f"GPU {self._card_name}"

    def is_available(self) -> bool:
        """Check whether the hwmon temp file is readable."""
        return self._temp_path.exists()


def _discover_nvidia_gpus() -> list[BaseSensor]:
    """
    Discover NVIDIA GPUs via pynvml.

    Returns:
        A list of NvidiaGpuSensor instances, one per detected GPU.
    """
    sensors: list[BaseSensor] = []
    if not _ensure_nvml():
        return sensors

    try:
        count = pynvml.nvmlDeviceGetCount()
    except pynvml.NVMLError:
        return sensors

    for i in range(count):
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            sensors.append(NvidiaGpuSensor(i, name))
        except pynvml.NVMLError:
            continue

    return sensors


def _discover_amd_gpus() -> list[BaseSensor]:
    """
    Discover AMD GPUs via sysfs hwmon.

    Returns:
        A list of AmdGpuSensor instances, one per detected AMD GPU.
    """
    sensors: list[BaseSensor] = []
    paths = sorted(glob.glob("/sys/class/drm/card*/device/hwmon/hwmon*/temp1_input"))
    for temp_path in paths:
        parts = Path(temp_path).parts
        card_name = parts[4] if len(parts) > 4 else "Unknown"
        sensor = AmdGpuSensor(temp_path, card_name)
        if sensor.is_available():
            sensors.append(sensor)

    return sensors


def discover_gpu_sensors() -> list[BaseSensor]:
    """
    Discover all available GPU temperature sensors.

    Checks for NVIDIA GPUs first, then AMD. Returns an empty list
    if no GPUs are found.

    Returns:
        A list of BaseSensor instances for each detected GPU.
    """
    sensors: list[BaseSensor] = []
    sensors.extend(_discover_nvidia_gpus())
    sensors.extend(_discover_amd_gpus())
    return sensors
