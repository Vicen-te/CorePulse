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
from utils.config import POLL_INTERVAL_MS


@dataclass
class SensorReading:
    """
    A single sensor reading with current, min, and max values.

    Attributes:
        name: Unique sensor key.
        current: Current value in its native unit.
        min_val: Minimum value since tracking started.
        max_val: Maximum value since tracking started.
        sensor_type: Type of sensor for formatting.
    """

    name: str
    current: float = 0.0
    min_val: float = float("inf")
    max_val: float = float("-inf")
    sensor_type: SensorType = SensorType.TEMPERATURE

    def update(self, value: float) -> None:
        """Update the reading with a new value."""
        self.current = value
        track_zero = self.sensor_type in (SensorType.LOAD, SensorType.FAN)
        if value > 0 or (value == 0 and track_zero):
            if value < self.min_val:
                self.min_val = value
            if value > self.max_val:
                self.max_val = value


class SensorPoller(QThread):
    """
    Background thread that polls all sensors at a fixed interval.

    Emits readings_updated with dict[str, SensorReading] each cycle.
    """

    readings_updated = Signal(dict)

    def __init__(self, sensors: list[BaseSensor]) -> None:
        """Initialize the poller with sensors to poll."""
        super().__init__()
        self._sensors = sensors
        self._readings: dict[str, SensorReading] = {}
        self._running = True

        for sensor in sensors:
            key = self._sensor_key(sensor)
            self._readings[key] = SensorReading(
                name=key, sensor_type=sensor.get_sensor_type()
            )

    @staticmethod
    def _sensor_key(sensor: BaseSensor) -> str:
        """Build a unique key for a sensor."""
        return f"{sensor.get_hardware_group()}|{sensor.get_type_group()}|{sensor.get_name()}"

    def run(self) -> None:
        """Poll sensors in a loop, emitting results each cycle."""
        while self._running:
            for sensor in self._sensors:
                if not self._running:
                    break
                key = self._sensor_key(sensor)
                value = sensor.get_temperature()
                self._readings[key].update(value)

            snapshot = {
                k: SensorReading(
                    name=r.name, current=r.current,
                    min_val=r.min_val, max_val=r.max_val,
                    sensor_type=r.sensor_type,
                )
                for k, r in self._readings.items()
            }
            self.readings_updated.emit(snapshot)
            self.msleep(POLL_INTERVAL_MS)

    def stop(self) -> None:
        """Signal the thread to stop and wait."""
        self._running = False
        self.wait(2000)
