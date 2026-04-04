"""
Background sensor polling thread.

Polls all temperature sensors on a background QThread and emits
results via a signal, keeping the UI thread completely unblocked.
"""

# Standard library
from dataclasses import dataclass, field
from datetime import datetime

# Third-party
from PySide6.QtCore import QThread, Signal

# Local
from sensors.base_sensor import BaseSensor
from utils.config import POLL_INTERVAL_MS


@dataclass
class SensorReading:
    """
    A single sensor reading with current, min, and max values.

    Attributes:
        name: Sensor display name.
        current: Current temperature in Celsius.
        min_temp: Minimum temperature since tracking started.
        max_temp: Maximum temperature since tracking started.
    """

    name: str
    current: float = 0.0
    min_temp: float = float("inf")
    max_temp: float = float("-inf")

    def update(self, value: float) -> None:
        """Update the reading with a new temperature value.

        Args:
            value: New temperature in Celsius.
        """
        self.current = value
        if value > 0:
            if value < self.min_temp:
                self.min_temp = value
            if value > self.max_temp:
                self.max_temp = value


class SensorPoller(QThread):
    """
    Background thread that polls all sensors at a fixed interval.

    Emits readings_updated with a dict mapping sensor names to
    their SensorReading (current/min/max). The UI thread connects
    to this signal and updates the tree widget.

    Attributes:
        sensors: List of sensors to poll.
        readings: Current state of all sensor readings.
    """

    readings_updated = Signal(dict)

    def __init__(self, sensors: list[BaseSensor]) -> None:
        """Initialize the poller with a list of sensors.

        Args:
            sensors: Sensors to poll each cycle.
        """
        super().__init__()
        self._sensors = sensors
        self._readings: dict[str, SensorReading] = {}
        self._running = True

        for sensor in sensors:
            name = sensor.get_name()
            self._readings[name] = SensorReading(name=name)

    def run(self) -> None:
        """Poll sensors in a loop, emitting results each cycle."""
        while self._running:
            for sensor in self._sensors:
                if not self._running:
                    break
                name = sensor.get_name()
                temp = sensor.get_temperature()
                self._readings[name].update(temp)

            # Emit a copy so the UI thread doesn't share mutable state
            snapshot = {
                name: SensorReading(
                    name=r.name,
                    current=r.current,
                    min_temp=r.min_temp,
                    max_temp=r.max_temp,
                )
                for name, r in self._readings.items()
            }
            self.readings_updated.emit(snapshot)
            self.msleep(POLL_INTERVAL_MS)

    def stop(self) -> None:
        """Signal the thread to stop and wait for it to finish."""
        self._running = False
        self.wait(2000)
