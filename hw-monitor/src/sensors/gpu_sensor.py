"""
GPU temperature sensor reader.

Supports NVIDIA GPUs via nvidia-smi and AMD GPUs via sysfs hwmon.
If no GPU is detected, is_available() returns False gracefully.
"""

# Standard library
import glob
import subprocess
from pathlib import Path

# Local
from sensors.base_sensor import BaseSensor


class NvidiaGpuSensor(BaseSensor):
    """
    Reads NVIDIA GPU temperature using nvidia-smi.

    Queries the GPU at a specific index for its current temperature.
    Handles missing nvidia-smi or driver errors gracefully.

    Attributes:
        gpu_index: Zero-based index of the NVIDIA GPU.
        gpu_name: Model name reported by nvidia-smi.
    """

    def __init__(self, gpu_index: int, gpu_name: str) -> None:
        """Initialize an NVIDIA GPU sensor.

        Args:
            gpu_index: Zero-based GPU index for nvidia-smi queries.
            gpu_name: Human-readable GPU model name.
        """
        self._gpu_index = gpu_index
        self._gpu_name = gpu_name
        self._available = True

    def get_temperature(self) -> float:
        """Return the current GPU temperature in Celsius.

        Returns:
            Temperature reading, or 0.0 if nvidia-smi fails.
        """
        try:
            output = subprocess.check_output(
                [
                    "nvidia-smi",
                    f"--id={self._gpu_index}",
                    "--query-gpu=temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                text=True,
                timeout=5,
                stderr=subprocess.DEVNULL,
            ).strip()
            return float(output)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
                FileNotFoundError, ValueError):
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
    Discover NVIDIA GPUs via nvidia-smi.

    Returns:
        A list of NvidiaGpuSensor instances, one per detected GPU.
    """
    sensors: list[BaseSensor] = []
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,name",
                "--format=csv,noheader",
            ],
            text=True,
            timeout=5,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired):
        return sensors

    for line in output.splitlines():
        parts = line.split(",", 1)
        if len(parts) == 2:
            try:
                gpu_index = int(parts[0].strip())
                gpu_name = parts[1].strip()
                sensors.append(NvidiaGpuSensor(gpu_index, gpu_name))
            except ValueError:
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
        # Extract card name from path (e.g. "card0")
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
