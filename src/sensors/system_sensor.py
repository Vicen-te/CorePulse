"""
System-level sensors: memory, storage, and NVMe temperatures.

Provides memory usage, disk usage, and NVMe temperature readings.
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
    """Reports disk usage for a mount point as value / total GB."""

    def __init__(self, mountpoint: str) -> None:
        """Initialize with mount point.

        Args:
            mountpoint: Filesystem mount point (e.g. "/").
        """
        self._mountpoint = mountpoint

    def get_temperature(self) -> float:
        """Return free disk space in GB."""
        try:
            return psutil.disk_usage(self._mountpoint).free / (1024 ** 3)
        except OSError:
            return 0.0

    def _get_total_gb(self) -> float:
        """Return total disk size in GB."""
        try:
            return psutil.disk_usage(self._mountpoint).total / (1024 ** 3)
        except OSError:
            return 0.0

    def get_name(self) -> str:
        """Return sensor name."""
        return f"Free Space ({self._mountpoint})"

    def is_available(self) -> bool:
        """Check availability."""
        try:
            psutil.disk_usage(self._mountpoint)
            return True
        except OSError:
            return False

    def get_sensor_type(self) -> SensorType:
        """Return DATA type."""
        return SensorType.DATA

    def get_hardware_group(self) -> str:
        """Return Storage group."""
        return "Storage"

    def get_type_group(self) -> str:
        """Return Usage type group."""
        return "Usage"

    def format_reading(self, value: float) -> str:
        """Format as 'X.X / Y.Y GB'."""
        total = self._get_total_gb()
        return f"{value:.1f} / {total:.1f} GB"


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

    # NVMe temperatures — assign drive numbers based on Composite entries
    temps = psutil.sensors_temperatures()
    nvme_entries = temps.get("nvme", [])
    drive_num = 0
    for i, entry in enumerate(nvme_entries):
        raw_label = entry.label if entry.label else f"Sensor {i}"
        if raw_label == "Composite":
            drive_num += 1
        label = f"{raw_label} (Drive {drive_num})"
        sensors.append(NvmeTempSensor("nvme", i, label))

    # Disk usage for real mounted partitions (skip snap/squashfs/tmpfs)
    skip_fs = {"squashfs", "tmpfs", "devtmpfs", "overlay"}
    skip_prefixes = ("/snap/", "/sys/", "/proc/", "/run/", "/dev/")
    seen: set[str] = set()
    for part in psutil.disk_partitions(all=False):
        mp = part.mountpoint
        if mp in seen or part.fstype in skip_fs:
            continue
        if any(mp.startswith(p) for p in skip_prefixes):
            continue
        seen.add(mp)
        sensors.append(DiskUsageSensor(mp))

    return sensors
