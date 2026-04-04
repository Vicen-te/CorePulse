"""Sensor readers for CPU and GPU temperature data."""

from sensors.cpu_sensor import CpuCoreSensor, CpuSensorFallback, discover_cpu_sensors
from sensors.gpu_sensor import NvidiaGpuSensor, AmdGpuSensor, discover_gpu_sensors

__all__ = [
    "CpuCoreSensor",
    "CpuSensorFallback",
    "NvidiaGpuSensor",
    "AmdGpuSensor",
    "discover_cpu_sensors",
    "discover_gpu_sensors",
]
