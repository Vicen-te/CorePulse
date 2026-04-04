"""
CPU sensor readers.

Reads CPU temperatures (psutil/sysfs), clock speeds, and per-core load.
"""

# Standard library
import glob
import time
from pathlib import Path

# Third-party
import psutil

# Local
from sensors.base_sensor import BaseSensor, SensorType


class CpuCoreSensor(BaseSensor):
    """
    Reads a single CPU core temperature from psutil coretemp.

    Attributes:
        label: Human-readable core identifier.
        high: High temperature threshold from hardware.
        critical: Critical temperature threshold from hardware.
    """

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
        temps = psutil.sensors_temperatures()
        entries = temps.get(self._sensor_key, [])
        if self._index < len(entries):
            return entries[self._index].current
        return 0.0

    def get_name(self) -> str:
        """Return the sensor name."""
        return self._label

    def is_available(self) -> bool:
        """Check whether this core sensor is still readable."""
        temps = psutil.sensors_temperatures()
        entries = temps.get(self._sensor_key, [])
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
            raw = self._zone_path.read_text().strip()
            return int(raw) / 1000
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
        freq = psutil.cpu_freq()
        return freq.current if freq else 0.0

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


class _CpuLoadCache:
    """Shared cache for per-core CPU load to avoid multiple psutil calls per poll cycle."""

    _percpu: list[float] = []
    _last_poll: float = 0.0
    _CACHE_TTL: float = 0.5

    @classmethod
    def get_percpu(cls) -> list[float]:
        """Return cached per-core CPU load, refreshing if stale."""
        now = time.monotonic()
        if now - cls._last_poll > cls._CACHE_TTL:
            result = psutil.cpu_percent(interval=None, percpu=True)
            if result:
                cls._percpu = result
            cls._last_poll = now
        return cls._percpu


class CpuTotalLoadSensor(BaseSensor):
    """Reads total CPU load percentage."""

    def get_temperature(self) -> float:
        """Return total CPU load percentage."""
        percpu = _CpuLoadCache.get_percpu()
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
    """Reads per-core CPU load percentage."""

    def __init__(self, core_index: int) -> None:
        """Initialize for a specific core index."""
        self._core_index = core_index

    def get_temperature(self) -> float:
        """Return this core's load percentage."""
        percpu = _CpuLoadCache.get_percpu()
        if self._core_index < len(percpu):
            return percpu[self._core_index]
        return 0.0

    def get_name(self) -> str:
        """Return the sensor name."""
        return f"Core #{self._core_index}"

    def is_available(self) -> bool:
        """Check availability."""
        return self._core_index < psutil.cpu_count(logical=True)

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

        # Read max range for overflow detection
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
                delta += self._max_range  # handle overflow
            # energy_uj is in microjoules; POLL_INTERVAL is ~1s
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

    Returns temperature, clock, load, and power sensors.

    Returns:
        A list of BaseSensor instances for each detected CPU sensor.
    """
    sensors: list[BaseSensor] = []

    # --- Temperatures: psutil coretemp ---
    temps = psutil.sensors_temperatures()
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
        # Fallback: sysfs thermal zones
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

    # --- Clock ---
    clock_sensor = CpuClockSensor()
    if clock_sensor.is_available():
        sensors.append(clock_sensor)

    # --- Load: total + per-core ---
    # Initialize cpu_percent tracking
    psutil.cpu_percent(interval=None, percpu=True)

    sensors.append(CpuTotalLoadSensor())
    core_count = psutil.cpu_count(logical=True) or 0
    for i in range(core_count):
        sensors.append(CpuCoreLoadSensor(i))

    # --- Power: Intel RAPL ---
    rapl_path = "/sys/class/powercap/intel-rapl:0/energy_uj"
    if Path(rapl_path).exists():
        try:
            Path(rapl_path).read_text()
            sensors.append(CpuPowerSensor(rapl_path))
        except PermissionError:
            pass  # RAPL often requires root

    return sensors
