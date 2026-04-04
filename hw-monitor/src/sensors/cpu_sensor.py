"""
CPU temperature sensor reader.

Reads CPU core temperatures using psutil as the primary source,
with a fallback to sysfs thermal zones. Supports per-core readings
on multi-core systems.
"""

# Standard library
import glob
from pathlib import Path

# Third-party
import psutil

# Local
from sensors.base_sensor import BaseSensor


class CpuCoreSensor(BaseSensor):
    """
    Reads a single CPU core temperature.

    Uses psutil.sensors_temperatures() to get the reading for a
    specific core identified by its label and index within the
    coretemp sensor group.

    Attributes:
        label: Human-readable core identifier (e.g. "Core 0").
        high: High temperature threshold reported by the hardware.
        critical: Critical temperature threshold reported by the hardware.
    """

    def __init__(self, label: str, sensor_key: str, index: int,
                 high: float | None = None, critical: float | None = None) -> None:
        """Initialize a CPU core sensor.

        Args:
            label: The core label from psutil (e.g. "Core 0").
            sensor_key: The psutil sensor group key (e.g. "coretemp").
            index: Index of this entry within the sensor group.
            high: High temperature threshold in Celsius.
            critical: Critical temperature threshold in Celsius.
        """
        self._label = label
        self._sensor_key = sensor_key
        self._index = index
        self.high = high
        self.critical = critical

    def get_temperature(self) -> float:
        """Return the current core temperature in Celsius.

        Returns:
            Temperature reading, or 0.0 if unavailable.
        """
        temps = psutil.sensors_temperatures()
        entries = temps.get(self._sensor_key, [])
        if self._index < len(entries):
            return entries[self._index].current
        return 0.0

    def get_name(self) -> str:
        """Return the human-readable sensor name."""
        return f"CPU {self._label}"

    def is_available(self) -> bool:
        """Check whether this core sensor is still readable."""
        temps = psutil.sensors_temperatures()
        entries = temps.get(self._sensor_key, [])
        return self._index < len(entries)


class CpuSensorFallback(BaseSensor):
    """
    Fallback CPU temperature reader using sysfs thermal zones.

    Used when psutil.sensors_temperatures() returns no coretemp data.
    Reads from /sys/class/thermal/thermal_zone*/temp files.

    Attributes:
        zone_path: Path to the thermal zone temp file.
        zone_name: Identifier for this thermal zone.
    """

    def __init__(self, zone_path: str, zone_name: str) -> None:
        """Initialize a sysfs thermal zone sensor.

        Args:
            zone_path: Full path to the temp file (e.g. /sys/class/thermal/thermal_zone0/temp).
            zone_name: Human-readable zone name.
        """
        self._zone_path = Path(zone_path)
        self._zone_name = zone_name

    def get_temperature(self) -> float:
        """Return the current temperature in Celsius.

        Returns:
            Temperature reading, or 0.0 if the file cannot be read.
        """
        try:
            raw = self._zone_path.read_text().strip()
            return int(raw) / 1000  # sysfs reports millidegrees
        except (OSError, ValueError):
            return 0.0

    def get_name(self) -> str:
        """Return the human-readable sensor name."""
        return f"CPU {self._zone_name}"

    def is_available(self) -> bool:
        """Check whether the thermal zone file is readable."""
        return self._zone_path.exists()


def discover_cpu_sensors() -> list[BaseSensor]:
    """
    Discover all available CPU temperature sensors.

    Uses psutil coretemp data as the primary source. If no coretemp
    entries are found, falls back to sysfs thermal zones.

    Returns:
        A list of BaseSensor instances for each detected CPU sensor.
    """
    sensors: list[BaseSensor] = []

    # --- Primary: psutil coretemp ---
    temps = psutil.sensors_temperatures()

    # Try common CPU sensor keys in order of preference
    cpu_keys = ["coretemp", "k10temp", "zenpower", "cpu_thermal"]
    sensor_key = None
    for key in cpu_keys:
        if key in temps and temps[key]:
            sensor_key = key
            break

    if sensor_key is not None:
        for index, entry in enumerate(temps[sensor_key]):
            label = entry.label if entry.label else f"Sensor {index}"
            sensors.append(CpuCoreSensor(
                label=label,
                sensor_key=sensor_key,
                index=index,
                high=entry.high,
                critical=entry.critical,
            ))
        return sensors

    # --- Fallback: sysfs thermal zones ---
    zone_paths = sorted(glob.glob("/sys/class/thermal/thermal_zone*/temp"))
    for zone_path in zone_paths:
        zone_dir = Path(zone_path).parent
        zone_name = zone_dir.name
        # Try to read the zone type for a better name
        type_file = zone_dir / "type"
        try:
            zone_type = type_file.read_text().strip()
            display_name = f"{zone_name} ({zone_type})"
        except OSError:
            display_name = zone_name

        fallback = CpuSensorFallback(zone_path, display_name)
        if fallback.is_available():
            try:
                temp = fallback.get_temperature()
                if temp > 0:
                    sensors.append(fallback)
            except OSError:
                continue

    return sensors
