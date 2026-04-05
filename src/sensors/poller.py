"""
Background sensor polling thread.

Polls all sensors on a background QThread and emits results via signal.
"""

# Standard library
from dataclasses import dataclass

# Third-party
from PySide6.QtCore import QThread, Signal

# Local
from sensors.base_sensor import BaseSensor, SensorType
from sensors.cpu_sensor import refresh_caches
from utils.config import POLL_INTERVAL_MS

_TRACK_ZERO_TYPES = frozenset({SensorType.LOAD, SensorType.FAN, SensorType.POWER})


@dataclass(slots=True)
class SensorReading:
    """
    A single sensor reading with current, min, and max values.

    Attributes:
        name: Unique sensor key.
        current: Current value in its native unit.
        min_val: Minimum value since tracking started.
        max_val: Maximum value since tracking started.
        sensor_type: Type of sensor for formatting.
        changed: Whether the current value changed since last cycle.
    """

    name: str
    current: float = 0.0
    min_val: float = float("inf")
    max_val: float = float("-inf")
    sensor_type: SensorType = SensorType.TEMPERATURE
    changed: bool = True

    def update(self, value: float) -> None:
        """Update the reading with a new value."""
        self.changed = value != self.current
        self.current = value
        if value > 0 or (value == 0 and self.sensor_type in _TRACK_ZERO_TYPES):
            if value < self.min_val:
                self.min_val = value
                self.changed = True
            if value > self.max_val:
                self.max_val = value
                self.changed = True


class SensorPoller(QThread):
    """
    Background thread that polls all sensors at a fixed interval.

    Emits readings_updated with the readings dict each cycle.
    """

    readings_updated = Signal(dict)

    def __init__(self, sensors: list[BaseSensor]) -> None:
        """Initialize the poller with sensors to poll."""
        super().__init__()
        self._sensors = sensors
        self._readings: dict[str, SensorReading] = {}
        self._keys: list[str] = []
        self._running = True

        for sensor in sensors:
            key = self._sensor_key(sensor)
            self._keys.append(key)
            self._readings[key] = SensorReading(
                name=key, sensor_type=sensor.get_sensor_type()
            )

    @staticmethod
    def _sensor_key(sensor: BaseSensor) -> str:
        """Build a unique key for a sensor."""
        return f"{sensor.get_hardware_group()}|{sensor.get_type_group()}|{sensor.get_name()}"

    def run(self) -> None:
        """Poll sensors in a loop, emitting results each cycle."""
        sensors = self._sensors
        keys = self._keys
        readings = self._readings

        while self._running:
            refresh_caches()

            for i, sensor in enumerate(sensors):
                if not self._running:
                    break
                readings[keys[i]].update(sensor.get_temperature())

            self.readings_updated.emit(readings)
            self.msleep(POLL_INTERVAL_MS)

    def reset_min_max(self) -> None:
        """Reset min/max values for all readings."""
        for reading in self._readings.values():
            reading.min_val = float("inf")
            reading.max_val = float("-inf")
            reading.changed = True

    def stop(self) -> None:
        """Signal the thread to stop and wait."""
        self._running = False
        self.wait(500)
