"""
System-level sensors: memory, storage, and NVMe temperatures.

Provides memory usage, disk usage, and NVMe temperature readings
following the LibreHardwareMonitor pattern.
"""

# Third-party
import psutil

# Local
from sensors.base_sensor import BaseSensor, SensorType


# --- Memory sensors ---

class MemoryUsedSensor(BaseSensor):
    """Reports used RAM in GB."""

    def get_temperature(self) -> float:
        """Return used memory in GB."""
        return psutil.virtual_memory().used / (1024 ** 3)

    def get_name(self) -> str:
        """Return sensor name."""
        return "Memory Used"

    def is_available(self) -> bool:
        """Always available."""
        return True

    def get_sensor_type(self) -> SensorType:
        """Return DATA type."""
        return SensorType.DATA

    def get_hardware_group(self) -> str:
        """Return Memory group."""
        return "Memory"

    def get_type_group(self) -> str:
        """Return Data type group."""
        return "Data"


class MemoryAvailableSensor(BaseSensor):
    """Reports available RAM in GB."""

    def get_temperature(self) -> float:
        """Return available memory in GB."""
        return psutil.virtual_memory().available / (1024 ** 3)

    def get_name(self) -> str:
        """Return sensor name."""
        return "Memory Available"

    def is_available(self) -> bool:
        """Always available."""
        return True

    def get_sensor_type(self) -> SensorType:
        """Return DATA type."""
        return SensorType.DATA

    def get_hardware_group(self) -> str:
        """Return Memory group."""
        return "Memory"

    def get_type_group(self) -> str:
        """Return Data type group."""
        return "Data"


class MemoryLoadSensor(BaseSensor):
    """Reports memory usage percentage."""

    def get_temperature(self) -> float:
        """Return memory usage percentage."""
        return psutil.virtual_memory().percent

    def get_name(self) -> str:
        """Return sensor name."""
        return "Memory"

    def is_available(self) -> bool:
        """Always available."""
        return True

    def get_sensor_type(self) -> SensorType:
        """Return LOAD type."""
        return SensorType.LOAD

    def get_hardware_group(self) -> str:
        """Return Memory group."""
        return "Memory"

    def get_type_group(self) -> str:
        """Return Load type group."""
        return "Load"


# --- Storage sensors ---

class DiskUsageSensor(BaseSensor):
    """Reports disk usage for a mount point."""

    def __init__(self, mountpoint: str, report_type: str = "used") -> None:
        """Initialize with mount point and what to report.

        Args:
            mountpoint: Filesystem mount point (e.g. "/").
            report_type: One of "used", "free", "percent".
        """
        self._mountpoint = mountpoint
        self._report_type = report_type

    def get_temperature(self) -> float:
        """Return disk usage value."""
        try:
            usage = psutil.disk_usage(self._mountpoint)
        except OSError:
            return 0.0

        if self._report_type == "used":
            return usage.used / (1024 ** 3)
        elif self._report_type == "free":
            return usage.free / (1024 ** 3)
        elif self._report_type == "percent":
            return usage.percent
        return 0.0

    def get_name(self) -> str:
        """Return sensor name."""
        labels = {"used": "Used Space", "free": "Free Space", "percent": "Usage"}
        name = labels.get(self._report_type, self._report_type)
        return f"{name} ({self._mountpoint})"

    def is_available(self) -> bool:
        """Check availability."""
        try:
            psutil.disk_usage(self._mountpoint)
            return True
        except OSError:
            return False

    def get_sensor_type(self) -> SensorType:
        """Return appropriate type."""
        if self._report_type == "percent":
            return SensorType.LOAD
        return SensorType.DATA

    def get_hardware_group(self) -> str:
        """Return Storage group."""
        return "Storage"

    def get_type_group(self) -> str:
        """Return type group."""
        if self._report_type == "percent":
            return "Load"
        return "Data"


class NvmeTempSensor(BaseSensor):
    """Reads NVMe disk temperature from psutil."""

    def __init__(self, sensor_key: str, index: int, label: str) -> None:
        """Initialize with psutil sensor key and index."""
        self._sensor_key = sensor_key
        self._index = index
        self._label = label

    def get_temperature(self) -> float:
        """Return NVMe temperature in Celsius."""
        temps = psutil.sensors_temperatures()
        entries = temps.get(self._sensor_key, [])
        if self._index < len(entries):
            return entries[self._index].current
        return 0.0

    def get_name(self) -> str:
        """Return sensor name."""
        return self._label

    def is_available(self) -> bool:
        """Check availability."""
        temps = psutil.sensors_temperatures()
        entries = temps.get(self._sensor_key, [])
        return self._index < len(entries)

    def get_sensor_type(self) -> SensorType:
        """Return TEMPERATURE type."""
        return SensorType.TEMPERATURE

    def get_hardware_group(self) -> str:
        """Return Storage group."""
        return "Storage"

    def get_type_group(self) -> str:
        """Return Temperatures type group."""
        return "Temperatures"


def discover_memory_sensors() -> list[BaseSensor]:
    """Discover memory sensors."""
    return [MemoryLoadSensor(), MemoryUsedSensor(), MemoryAvailableSensor()]


def discover_storage_sensors() -> list[BaseSensor]:
    """Discover storage and NVMe sensors."""
    sensors: list[BaseSensor] = []

    # NVMe temperatures
    temps = psutil.sensors_temperatures()
    nvme_entries = temps.get("nvme", [])
    for i, entry in enumerate(nvme_entries):
        label = entry.label if entry.label else f"Sensor {i}"
        sensors.append(NvmeTempSensor("nvme", i, label))

    # Disk usage for mounted partitions
    seen: set[str] = set()
    for part in psutil.disk_partitions(all=False):
        mp = part.mountpoint
        if mp in seen:
            continue
        seen.add(mp)
        sensors.append(DiskUsageSensor(mp, "used"))
        sensors.append(DiskUsageSensor(mp, "free"))
        sensors.append(DiskUsageSensor(mp, "percent"))

    return sensors
