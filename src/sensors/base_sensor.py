"""
Abstract base class for hardware sensors.

Defines the interface that all sensor readers must implement.
Supports different sensor types (temperature, voltage, clock, etc.).
"""

# Standard library
from abc import ABC, abstractmethod
from enum import Enum


class SensorType(Enum):
    """Type of hardware sensor reading."""

    TEMPERATURE = "temperature"
    VOLTAGE = "voltage"
    CLOCK = "clock"
    LOAD = "load"
    FAN = "fan"
    POWER = "power"
    DATA = "data"
    THROUGHPUT = "throughput"


# Display format per sensor type
SENSOR_FORMATS: dict[SensorType, tuple[str, str]] = {
    SensorType.TEMPERATURE: ("{:.1f}", "°C"),
    SensorType.VOLTAGE: ("{:.3f}", " V"),
    SensorType.CLOCK: ("{:.0f}", " MHz"),
    SensorType.LOAD: ("{:.1f}", " %"),
    SensorType.FAN: ("{:.0f}", " %"),
    SensorType.POWER: ("{:.1f}", " W"),
    SensorType.DATA: ("{:.1f}", " GB"),
    SensorType.THROUGHPUT: ("{:.1f}", " MB/s"),
}


def format_value(value: float, sensor_type: SensorType) -> str:
    """
    Format a sensor value with appropriate units.

    Args:
        value: The raw sensor value.
        sensor_type: The type of sensor.

    Returns:
        Formatted string with units (e.g. "42.0°C", "210 MHz").
    """
    fmt, unit = SENSOR_FORMATS.get(sensor_type, ("{:.1f}", ""))
    return fmt.format(value) + unit


class BaseSensor(ABC):
    """
    Abstract base class for hardware sensors.

    All concrete sensor implementations must provide methods
    to read the current value, report their name, type,
    and indicate whether the sensor hardware is available.
    """

    @abstractmethod
    def get_temperature(self) -> float:
        """
        Return the current reading value.

        Returns:
            The current sensor value in its native unit.
        """

    @abstractmethod
    def get_name(self) -> str:
        """
        Return the human-readable sensor name.

        Returns:
            A descriptive name for this sensor.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check whether this sensor is available on the system.

        Returns:
            True if the sensor hardware is detected and readable.
        """

    def get_sensor_type(self) -> SensorType:
        """
        Return the type of this sensor.

        Returns:
            SensorType.TEMPERATURE by default; override in subclasses.
        """
        return SensorType.TEMPERATURE

    def get_hardware_group(self) -> str:
        """
        Return the hardware group this sensor belongs to.

        Returns:
            Hardware group name (e.g. "CPU", "GPU", "Storage").
        """
        return "Unknown"

    def get_type_group(self) -> str:
        """
        Return the sensor type group name for the tree.

        Returns:
            Type group name (e.g. "Temperatures", "Clocks", "Load").
        """
        type_map = {
            SensorType.TEMPERATURE: "Temperatures",
            SensorType.VOLTAGE: "Voltages",
            SensorType.CLOCK: "Clocks",
            SensorType.LOAD: "Load",
            SensorType.FAN: "Fans",
            SensorType.POWER: "Power",
            SensorType.DATA: "Data",
            SensorType.THROUGHPUT: "Throughput",
        }
        return type_map.get(self.get_sensor_type(), "Other")

    def format_reading(self, value: float) -> str:
        """
        Format a reading value for display.

        Override in subclasses for custom formats (e.g. "X / Y GB").

        Args:
            value: The raw sensor value.

        Returns:
            Formatted string with units.
        """
        return format_value(value, self.get_sensor_type())
