"""
Sensor read performance benchmarks.

Measures the time each sensor takes to read a value, identifying
slow sensors that could affect polling throughput.

Usage:
    cd ThermalCore
    source .venv/bin/activate
    python -m tests.bench_sensors
"""

import sys
import time
sys.path.insert(0, "src")

from sensors.cpu_sensor import discover_cpu_sensors
from sensors.gpu_sensor import discover_gpu_sensors
from sensors.system_sensor import discover_memory_sensors, discover_storage_sensors


def bench_sensor_reads(iterations: int = 100) -> None:
    """Benchmark individual sensor read times."""
    print(f"Benchmarking sensor reads ({iterations} iterations each)\n")
    print(f"{'Sensor':<35} {'Avg (ms)':>10} {'Min (ms)':>10} {'Max (ms)':>10}")
    print("-" * 70)

    all_sensors = []
    all_sensors.extend(discover_cpu_sensors())
    all_sensors.extend(discover_gpu_sensors())
    all_sensors.extend(discover_memory_sensors())
    all_sensors.extend(discover_storage_sensors())

    total_avg = 0.0
    for sensor in all_sensors:
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            sensor.get_temperature()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg = sum(times) / len(times)
        total_avg += avg
        name = f"{sensor.get_hardware_group()}/{sensor.get_name()}"
        print(f"{name:<35} {avg:>10.4f} {min(times):>10.4f} {max(times):>10.4f}")

    print("-" * 70)
    print(f"{'Total per cycle':<35} {total_avg:>10.4f}")
    print(f"{'Sensors':<35} {len(all_sensors):>10}")
    print(f"{'Max poll rate':<35} {1000/total_avg:>9.1f}Hz" if total_avg > 0 else "")


def bench_discovery_time() -> None:
    """Benchmark sensor discovery time."""
    print("\nBenchmarking sensor discovery\n")
    print(f"{'Phase':<30} {'Time (ms)':>10} {'Count':>8}")
    print("-" * 52)

    phases = [
        ("CPU sensors", discover_cpu_sensors),
        ("GPU sensors", discover_gpu_sensors),
        ("Memory sensors", discover_memory_sensors),
        ("Storage sensors", discover_storage_sensors),
    ]

    total_time = 0.0
    total_sensors = 0
    for name, discover_fn in phases:
        start = time.perf_counter()
        sensors = discover_fn()
        elapsed = (time.perf_counter() - start) * 1000
        total_time += elapsed
        total_sensors += len(sensors)
        print(f"{name:<30} {elapsed:>10.2f} {len(sensors):>8}")

    print("-" * 52)
    print(f"{'Total':<30} {total_time:>10.2f} {total_sensors:>8}")


if __name__ == "__main__":
    bench_sensor_reads()
    bench_discovery_time()
