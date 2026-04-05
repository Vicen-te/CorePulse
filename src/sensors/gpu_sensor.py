"""
GPU sensor readers.

Supports NVIDIA GPUs via pynvml with temperature, clock, load, VRAM,
power, and fan speed. AMD GPUs via sysfs hwmon (temperature only).
"""

# Standard library
import glob
from pathlib import Path

# Local
from sensors.base_sensor import BaseSensor, SensorType
from utils.logger import get_logger

log = get_logger("corepulse.gpu")

try:
    import pynvml
    _NVML_AVAILABLE = True
except ImportError:
    _NVML_AVAILABLE = False

_nvml_initialized: bool = False


def _ensure_nvml() -> bool:
    """Initialize NVML if not already done."""
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
        log.warning("NVML initialization failed — NVIDIA GPU monitoring unavailable")
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


class _NvidiaBaseSensor(BaseSensor):
    """Base class for all NVIDIA GPU sensors sharing a device handle."""

    def __init__(self, handle: object, gpu_name: str) -> None:
        """Initialize with NVML device handle."""
        self._handle = handle
        self._gpu_name = gpu_name

    def is_available(self) -> bool:
        """Check availability."""
        return self._handle is not None

    def get_hardware_group(self) -> str:
        """Return GPU hardware group."""
        return "GPU"


class NvidiaGpuTempSensor(_NvidiaBaseSensor):
    """NVIDIA GPU core temperature."""

    def get_temperature(self) -> float:
        """Return GPU temperature in Celsius."""
        try:
            return float(pynvml.nvmlDeviceGetTemperature(self._handle, pynvml.NVML_TEMPERATURE_GPU))
        except pynvml.NVMLError:
            return 0.0

    def get_name(self) -> str:
        """Return sensor name."""
        return "GPU Core"

    def get_sensor_type(self) -> SensorType:
        """Return type."""
        return SensorType.TEMPERATURE


class NvidiaGpuClockSensor(_NvidiaBaseSensor):
    """NVIDIA GPU clock speed."""

    def __init__(self, handle: object, gpu_name: str, clock_type: int, name: str) -> None:
        """Initialize with clock type (0=Graphics, 2=Memory)."""
        super().__init__(handle, gpu_name)
        self._clock_type = clock_type
        self._name = name

    def get_temperature(self) -> float:
        """Return clock speed in MHz."""
        try:
            return float(pynvml.nvmlDeviceGetClockInfo(self._handle, self._clock_type))
        except pynvml.NVMLError:
            return 0.0

    def get_name(self) -> str:
        """Return sensor name."""
        return self._name

    def get_sensor_type(self) -> SensorType:
        """Return type."""
        return SensorType.CLOCK

    def get_type_group(self) -> str:
        """Return type group."""
        return "Clocks"


class NvidiaGpuLoadSensor(_NvidiaBaseSensor):
    """NVIDIA GPU utilization percentage."""

    def __init__(self, handle: object, gpu_name: str, use_memory: bool = False) -> None:
        """Initialize. use_memory=True reads memory controller load."""
        super().__init__(handle, gpu_name)
        self._use_memory = use_memory

    def get_temperature(self) -> float:
        """Return GPU load percentage."""
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(self._handle)
            return float(util.memory if self._use_memory else util.gpu)
        except pynvml.NVMLError:
            return 0.0

    def get_name(self) -> str:
        """Return sensor name."""
        return "Memory Controller" if self._use_memory else "GPU Core"

    def get_sensor_type(self) -> SensorType:
        """Return type."""
        return SensorType.LOAD

    def get_type_group(self) -> str:
        """Return type group."""
        return "Load"


class NvidiaGpuVramSensor(_NvidiaBaseSensor):
    """NVIDIA GPU VRAM usage in GB."""

    def __init__(self, handle: object, gpu_name: str, report_total: bool = False) -> None:
        """Initialize. report_total=True reports total, else used."""
        super().__init__(handle, gpu_name)
        self._report_total = report_total

    def get_temperature(self) -> float:
        """Return VRAM in GB."""
        try:
            mem = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
            val = mem.total if self._report_total else mem.used
            return val / (1024 ** 3)
        except pynvml.NVMLError:
            return 0.0

    def get_name(self) -> str:
        """Return sensor name."""
        return "VRAM Total" if self._report_total else "VRAM Used"

    def get_sensor_type(self) -> SensorType:
        """Return type."""
        return SensorType.DATA

    def get_type_group(self) -> str:
        """Return type group."""
        return "Data"


class NvidiaGpuPowerSensor(_NvidiaBaseSensor):
    """NVIDIA GPU power draw in watts."""

    def get_temperature(self) -> float:
        """Return power in watts."""
        try:
            return pynvml.nvmlDeviceGetPowerUsage(self._handle) / 1000
        except pynvml.NVMLError:
            return 0.0

    def get_name(self) -> str:
        """Return sensor name."""
        return "GPU Power"

    def get_sensor_type(self) -> SensorType:
        """Return type."""
        return SensorType.POWER

    def get_type_group(self) -> str:
        """Return type group."""
        return "Power"


class NvidiaGpuFanSensor(_NvidiaBaseSensor):
    """NVIDIA GPU fan speed percentage."""

    def get_temperature(self) -> float:
        """Return fan speed percentage."""
        try:
            return float(pynvml.nvmlDeviceGetFanSpeed(self._handle))
        except pynvml.NVMLError:
            return 0.0

    def get_name(self) -> str:
        """Return sensor name."""
        return "GPU Fan"

    def get_sensor_type(self) -> SensorType:
        """Return type."""
        return SensorType.FAN

    def get_type_group(self) -> str:
        """Return type group."""
        return "Fans"


class AmdGpuSensor(BaseSensor):
    """Reads AMD GPU temperature via sysfs hwmon."""

    def __init__(self, temp_path: str, card_name: str) -> None:
        """Initialize an AMD GPU sensor."""
        self._temp_path = Path(temp_path)
        self._card_name = card_name

    def get_temperature(self) -> float:
        """Return GPU temperature in Celsius."""
        try:
            raw = self._temp_path.read_text().strip()
            return int(raw) / 1000
        except (OSError, ValueError):
            return 0.0

    def get_name(self) -> str:
        """Return sensor name."""
        return f"GPU {self._card_name}"

    def is_available(self) -> bool:
        """Check availability."""
        return self._temp_path.exists()

    def get_hardware_group(self) -> str:
        """Return GPU hardware group."""
        return "GPU"


def _discover_nvidia_gpus() -> list[BaseSensor]:
    """Discover NVIDIA GPUs and all available sensor types."""
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
        except pynvml.NVMLError:
            continue

        # Temperature
        sensors.append(NvidiaGpuTempSensor(handle, name))

        # Clocks
        sensors.append(NvidiaGpuClockSensor(handle, name, 0, "GPU Core"))
        sensors.append(NvidiaGpuClockSensor(handle, name, 2, "GPU Memory"))

        # Load
        sensors.append(NvidiaGpuLoadSensor(handle, name, use_memory=False))
        sensors.append(NvidiaGpuLoadSensor(handle, name, use_memory=True))

        # VRAM
        sensors.append(NvidiaGpuVramSensor(handle, name, report_total=False))
        sensors.append(NvidiaGpuVramSensor(handle, name, report_total=True))

        # Power
        sensors.append(NvidiaGpuPowerSensor(handle, name))

        # Fan
        sensors.append(NvidiaGpuFanSensor(handle, name))

    return sensors


def _discover_amd_gpus() -> list[BaseSensor]:
    """Discover AMD GPUs via sysfs hwmon."""
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
    """Discover all available GPU sensors."""
    sensors: list[BaseSensor] = []
    sensors.extend(_discover_nvidia_gpus())
    sensors.extend(_discover_amd_gpus())
    return sensors
