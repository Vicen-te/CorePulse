"""
CPU sensor readers.

Reads CPU temperatures (psutil/sysfs), clock speeds, and per-core load.
"""

# Standard library
import glob
from pathlib import Path

# Third-party
import psutil

# Local
from sensors.base_sensor import BaseSensor, SensorType

# Shared poll data — refreshed once per cycle by the poller via refresh_caches()
_cache: dict = {
    "temps": {},
    "percpu": [],
    "freq": 0.0,
    "mem": None,
}


def refresh_caches() -> None:
    """Refresh all cached sensor data. Called once per poll cycle by the poller."""
    _cache["temps"] = psutil.sensors_temperatures()
    result = psutil.cpu_percent(interval=None, percpu=True)
    if result:
        _cache["percpu"] = result
    freq = psutil.cpu_freq()
    _cache["freq"] = freq.current if freq else 0.0
    _cache["mem"] = psutil.virtual_memory()


class CpuCoreSensor(BaseSensor):
    """Reads a single CPU core temperature from psutil coretemp."""

    def __init__(self, label: str, sensor_key: str, index: int,
                 high: float | None = None, critical: float | None = None) -> None:
        """Initialize a CPU core temperature sensor."""
        self._label = label
        self._sensor_key = sensor_key
        self._index = index
        self.high = high
        self.critical = critical

    def get_temperature(self) -> float:
        """Return the current core temperature in Celsius."""
        entries = _cache["temps"].get(self._sensor_key, [])
        return entries[self._index].current if self._index < len(entries) else 0.0

    def get_name(self) -> str:
        """Return the sensor name."""
        return self._label

    def is_available(self) -> bool:
        """Check whether this core sensor is still readable."""
        entries = _cache["temps"].get(self._sensor_key, [])
        return self._index < len(entries)

    def get_sensor_type(self) -> SensorType:
        """Return TEMPERATURE type."""
        return SensorType.TEMPERATURE

    def get_hardware_group(self) -> str:
        """Return CPU hardware group."""
        return "CPU"

    def get_type_group(self) -> str:
        """Return Temperatures type group."""
        return "Temperatures"


class CpuSensorFallback(BaseSensor):
    """Fallback CPU temperature reader using sysfs thermal zones."""

    def __init__(self, zone_path: str, zone_name: str) -> None:
        """Initialize a sysfs thermal zone sensor."""
        self._zone_path = Path(zone_path)
        self._zone_name = zone_name

    def get_temperature(self) -> float:
        """Return the current temperature in Celsius."""
        try:
            return int(self._zone_path.read_text().strip()) / 1000
        except (OSError, ValueError):
            return 0.0

    def get_name(self) -> str:
        """Return the sensor name."""
        return self._zone_name

    def is_available(self) -> bool:
        """Check whether the thermal zone file is readable."""
        return self._zone_path.exists()

    def get_hardware_group(self) -> str:
        """Return CPU hardware group."""
        return "CPU"


class CpuClockSensor(BaseSensor):
    """Reads current CPU clock speed from psutil."""

    def get_temperature(self) -> float:
        """Return the current CPU clock in MHz."""
        return _cache["freq"]

    def get_name(self) -> str:
        """Return the sensor name."""
        return "CPU Clock"

    def is_available(self) -> bool:
        """Check availability."""
        return psutil.cpu_freq() is not None

    def get_sensor_type(self) -> SensorType:
        """Return CLOCK type."""
        return SensorType.CLOCK

    def get_hardware_group(self) -> str:
        """Return CPU hardware group."""
        return "CPU"

    def get_type_group(self) -> str:
        """Return Clocks type group."""
        return "Clocks"


class CpuTotalLoadSensor(BaseSensor):
    """Reads total CPU load percentage."""

    def get_temperature(self) -> float:
        """Return total CPU load percentage."""
        percpu = _cache["percpu"]
        return sum(percpu) / len(percpu) if percpu else 0.0

    def get_name(self) -> str:
        """Return the sensor name."""
        return "CPU Total"

    def is_available(self) -> bool:
        """Always available."""
        return True

    def get_sensor_type(self) -> SensorType:
        """Return LOAD type."""
        return SensorType.LOAD

    def get_hardware_group(self) -> str:
        """Return CPU hardware group."""
        return "CPU"

    def get_type_group(self) -> str:
        """Return Load type group."""
        return "Load"


class CpuCoreLoadSensor(BaseSensor):
    """Reads load for a physical core, averaging its logical threads."""

    def __init__(self, logical_indices: list[int], name: str) -> None:
        """Initialize with logical CPU indices belonging to this physical core."""
        self._logical_indices = logical_indices
        self._name = name

    def get_temperature(self) -> float:
        """Return this physical core's average load percentage."""
        percpu = _cache["percpu"]
        vals = [percpu[i] for i in self._logical_indices if i < len(percpu)]
        return sum(vals) / len(vals) if vals else 0.0

    def get_name(self) -> str:
        """Return the sensor name matching the temperature core label."""
        return self._name

    def is_available(self) -> bool:
        """Check availability."""
        return all(i < psutil.cpu_count(logical=True) for i in self._logical_indices)

    def get_sensor_type(self) -> SensorType:
        """Return LOAD type."""
        return SensorType.LOAD

    def get_hardware_group(self) -> str:
        """Return CPU hardware group."""
        return "CPU"

    def get_type_group(self) -> str:
        """Return Load type group."""
        return "Load"


class CpuPowerSensor(BaseSensor):
    """
    Reads CPU package power from Intel RAPL via sysfs.

    Tracks energy delta between polls to compute watts.
    """

    def __init__(self, energy_path: str) -> None:
        """Initialize with path to energy_uj file."""
        self._energy_path = Path(energy_path)
        self._last_energy: int | None = None
        self._last_power: float = 0.0

        range_path = self._energy_path.parent / "max_energy_range_uj"
        try:
            self._max_range = int(range_path.read_text().strip())
        except (OSError, ValueError):
            self._max_range = 0

    def get_temperature(self) -> float:
        """Return estimated CPU power in watts."""
        try:
            energy = int(self._energy_path.read_text().strip())
        except (OSError, ValueError):
            return self._last_power

        if self._last_energy is not None:
            delta = energy - self._last_energy
            if delta < 0 and self._max_range > 0:
                delta += self._max_range
            self._last_power = delta / 1_000_000
        self._last_energy = energy
        return self._last_power

    def get_name(self) -> str:
        """Return the sensor name."""
        return "CPU Package"

    def is_available(self) -> bool:
        """Check availability."""
        return self._energy_path.exists()

    def get_sensor_type(self) -> SensorType:
        """Return POWER type."""
        return SensorType.POWER

    def get_hardware_group(self) -> str:
        """Return CPU hardware group."""
        return "CPU"

    def get_type_group(self) -> str:
        """Return Power type group."""
        return "Power"


def discover_cpu_sensors() -> list[BaseSensor]:
    """
    Discover all available CPU sensors.

    Returns:
        A list of BaseSensor instances for each detected CPU sensor.
    """
    sensors: list[BaseSensor] = []

    temps = psutil.sensors_temperatures()
    _cache["temps"] = temps
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
                label=label, sensor_key=sensor_key, index=index,
                high=entry.high, critical=entry.critical,
            ))
    else:
        zone_paths = sorted(glob.glob("/sys/class/thermal/thermal_zone*/temp"))
        for zone_path in zone_paths:
            zone_dir = Path(zone_path).parent
            type_file = zone_dir / "type"
            try:
                zone_type = type_file.read_text().strip()
                display_name = f"{zone_dir.name} ({zone_type})"
            except OSError:
                display_name = zone_dir.name
            fallback = CpuSensorFallback(zone_path, display_name)
            if fallback.is_available():
                try:
                    if fallback.get_temperature() > 0:
                        sensors.append(fallback)
                except OSError:
                    continue

    clock_sensor = CpuClockSensor()
    if clock_sensor.is_available():
        sensors.append(clock_sensor)

    psutil.cpu_percent(interval=None, percpu=True)
    sensors.append(CpuTotalLoadSensor())

    core_to_logical: dict[int, list[int]] = {}
    current_proc: int | None = None
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("processor"):
                    current_proc = int(line.split(":", 1)[1].strip())
                elif line.startswith("core id") and current_proc is not None:
                    core_id = int(line.split(":", 1)[1].strip())
                    core_to_logical.setdefault(core_id, []).append(current_proc)
    except OSError:
        core_to_logical = {}

    if core_to_logical:
        for core_id in sorted(core_to_logical):
            sensors.append(CpuCoreLoadSensor(core_to_logical[core_id], f"Core {core_id}"))
    else:
        logical_count = psutil.cpu_count(logical=True) or 0
        for i in range(logical_count):
            sensors.append(CpuCoreLoadSensor([i], f"Core {i}"))

    rapl_path = "/sys/class/powercap/intel-rapl:0/energy_uj"
    if Path(rapl_path).exists():
        sensors.append(CpuPowerSensor(rapl_path))

    return sensors
