"""
Abstract base class for temperature sensors.

Defines the interface that all sensor readers must implement,
ensuring consistent behavior across CPU and GPU sensors.
"""

from abc import ABC, abstractmethod


class BaseSensor(ABC):
    """
    Abstract base class for hardware temperature sensors.

    All concrete sensor implementations must provide methods
    to read the current temperature, report their name,
    and indicate whether the sensor hardware is available.
    """

    @abstractmethod
    def get_temperature(self) -> float:
        """
        Return the current temperature in degrees Celsius.

        Returns:
            The current sensor temperature.
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
