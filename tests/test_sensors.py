"""
Unit tests for sensor readers.

Verifies that all sensor classes return valid data, implement
the BaseSensor interface correctly, and handle edge cases.

Usage:
    cd ThermalCore
    source .venv/bin/activate
    python -m pytest tests/test_sensors.py -v
"""

import sys
import unittest
sys.path.insert(0, "src")

from sensors.base_sensor import BaseSensor, SensorType, format_value, SENSOR_FORMATS
from sensors.cpu_sensor import discover_cpu_sensors
from sensors.gpu_sensor import discover_gpu_sensors
from sensors.system_sensor import discover_memory_sensors, discover_storage_sensors


class TestSensorInterface(unittest.TestCase):
    """Verify all discovered sensors implement the BaseSensor interface."""

    def setUp(self) -> None:
        """Discover all available sensors."""
        self.sensors: list[BaseSensor] = []
        self.sensors.extend(discover_cpu_sensors())
        self.sensors.extend(discover_gpu_sensors())
        self.sensors.extend(discover_memory_sensors())
        self.sensors.extend(discover_storage_sensors())

    def test_sensors_discovered(self) -> None:
        """At least some sensors should be found on any Linux system."""
        self.assertGreater(len(self.sensors), 0, "No sensors discovered")

    def test_all_have_name(self) -> None:
        """Every sensor must return a non-empty name."""
        for sensor in self.sensors:
            name = sensor.get_name()
            self.assertIsInstance(name, str)
            self.assertTrue(len(name) > 0, f"Empty name for {sensor}")

    def test_all_have_sensor_type(self) -> None:
        """Every sensor must return a valid SensorType."""
        for sensor in self.sensors:
            st = sensor.get_sensor_type()
            self.assertIsInstance(st, SensorType)

    def test_all_have_hardware_group(self) -> None:
        """Every sensor must return a non-empty hardware group."""
        for sensor in self.sensors:
            group = sensor.get_hardware_group()
            self.assertIsInstance(group, str)
            self.assertTrue(len(group) > 0)

    def test_all_have_type_group(self) -> None:
        """Every sensor must return a non-empty type group."""
        for sensor in self.sensors:
            group = sensor.get_type_group()
            self.assertIsInstance(group, str)
            self.assertTrue(len(group) > 0)

    def test_all_return_numeric_value(self) -> None:
        """Every sensor must return a float from get_temperature()."""
        for sensor in self.sensors:
            value = sensor.get_temperature()
            self.assertIsInstance(value, (int, float), f"{sensor.get_name()} returned {type(value)}")

    def test_all_have_format_reading(self) -> None:
        """Every sensor must return a formatted string."""
        for sensor in self.sensors:
            value = sensor.get_temperature()
            formatted = sensor.format_reading(value)
            self.assertIsInstance(formatted, str)
            self.assertTrue(len(formatted) > 0)

    def test_is_available_returns_bool(self) -> None:
        """is_available() must return a boolean."""
        for sensor in self.sensors:
            result = sensor.is_available()
            self.assertIsInstance(result, bool)


class TestFormatValue(unittest.TestCase):
    """Test the format_value utility function."""

    def test_temperature_format(self) -> None:
        """Temperature values should show one decimal + unit."""
        result = format_value(45.0, SensorType.TEMPERATURE)
        self.assertEqual(result, "45.0°C")

    def test_clock_format(self) -> None:
        """Clock values should show integer MHz."""
        result = format_value(4200.0, SensorType.CLOCK)
        self.assertEqual(result, "4200 MHz")

    def test_load_format(self) -> None:
        """Load values should show one decimal + %."""
        result = format_value(12.3, SensorType.LOAD)
        self.assertEqual(result, "12.3 %")

    def test_power_format(self) -> None:
        """Power values should show one decimal + W."""
        result = format_value(125.5, SensorType.POWER)
        self.assertEqual(result, "125.5 W")

    def test_fan_format(self) -> None:
        """Fan values should show integer + %."""
        result = format_value(75.0, SensorType.FAN)
        self.assertEqual(result, "75 %")

    def test_data_format(self) -> None:
        """Data values should show one decimal + GB."""
        result = format_value(8.5, SensorType.DATA)
        self.assertEqual(result, "8.5 GB")

    def test_all_sensor_types_have_format(self) -> None:
        """Every SensorType should have a format entry."""
        for st in SensorType:
            self.assertIn(st, SENSOR_FORMATS, f"Missing format for {st}")


class TestCpuSensors(unittest.TestCase):
    """Test CPU sensor discovery and readings."""

    def setUp(self) -> None:
        """Discover CPU sensors."""
        self.sensors = discover_cpu_sensors()

    def test_cpu_sensors_found(self) -> None:
        """CPU sensors should always be found on Linux."""
        self.assertGreater(len(self.sensors), 0)

    def test_has_temperature_sensors(self) -> None:
        """At least one temperature sensor should exist on real hardware."""
        temps = [s for s in self.sensors if s.get_sensor_type() == SensorType.TEMPERATURE]
        if not temps:
            self.skipTest("No CPU temperature sensors (CI/VM environment)")
        self.assertGreater(len(temps), 0)

    def test_has_load_sensors(self) -> None:
        """At least one load sensor (CPU Total) should exist."""
        loads = [s for s in self.sensors if s.get_sensor_type() == SensorType.LOAD]
        self.assertGreater(len(loads), 0, "No CPU load sensors")

    def test_temperature_values_reasonable(self) -> None:
        """CPU temperatures should be between 0 and 120."""
        for sensor in self.sensors:
            if sensor.get_sensor_type() == SensorType.TEMPERATURE:
                temp = sensor.get_temperature()
                self.assertGreaterEqual(temp, 0, f"{sensor.get_name()} too low: {temp}")
                self.assertLessEqual(temp, 120, f"{sensor.get_name()} too high: {temp}")

    def test_all_in_cpu_group(self) -> None:
        """All CPU sensors should report 'CPU' as hardware group."""
        for sensor in self.sensors:
            self.assertEqual(sensor.get_hardware_group(), "CPU")


class TestMemorySensors(unittest.TestCase):
    """Test memory sensor discovery and readings."""

    def setUp(self) -> None:
        """Discover memory sensors."""
        self.sensors = discover_memory_sensors()

    def test_memory_sensors_found(self) -> None:
        """Memory sensors should always be available."""
        self.assertEqual(len(self.sensors), 3, "Expected 3 memory sensors (load, used, available)")

    def test_memory_load_in_range(self) -> None:
        """Memory load should be between 0% and 100%."""
        load_sensors = [s for s in self.sensors if s.get_sensor_type() == SensorType.LOAD]
        for sensor in load_sensors:
            value = sensor.get_temperature()
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)

    def test_memory_values_positive(self) -> None:
        """Memory used/available should be positive."""
        for sensor in self.sensors:
            value = sensor.get_temperature()
            self.assertGreaterEqual(value, 0, f"{sensor.get_name()} is negative: {value}")


class TestStorageSensors(unittest.TestCase):
    """Test storage sensor discovery and readings."""

    def setUp(self) -> None:
        """Discover storage sensors."""
        self.sensors = discover_storage_sensors()

    def test_storage_sensors_found(self) -> None:
        """At least one storage sensor (root partition) should exist."""
        self.assertGreater(len(self.sensors), 0)

    def test_disk_space_positive(self) -> None:
        """Free disk space should be positive."""
        for sensor in self.sensors:
            if sensor.get_sensor_type() == SensorType.DATA:
                value = sensor.get_temperature()
                self.assertGreater(value, 0, f"{sensor.get_name()} reports 0 free space")


class TestGpuSensors(unittest.TestCase):
    """Test GPU sensor discovery (may be empty if no GPU)."""

    def setUp(self) -> None:
        """Discover GPU sensors."""
        self.sensors = discover_gpu_sensors()

    def test_gpu_discovery_no_crash(self) -> None:
        """GPU discovery should not crash even without a GPU."""
        # Just verifying it didn't raise an exception
        self.assertIsInstance(self.sensors, list)

    def test_gpu_values_if_present(self) -> None:
        """If GPU sensors exist, they should return valid values."""
        for sensor in self.sensors:
            value = sensor.get_temperature()
            self.assertIsInstance(value, (int, float))
            self.assertGreaterEqual(value, 0)


if __name__ == "__main__":
    unittest.main()
