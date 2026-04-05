"""
Polling cycle performance benchmark.

Simulates what the background poller does each cycle:
reads all sensors and measures total cycle time, memory usage,
and CPU overhead.

Usage:
    cd ThermalCore
    source .venv/bin/activate
    python -m tests.bench_polling
"""

import sys
import time
import os
sys.path.insert(0, "src")

import psutil

from sensors.cpu_sensor import discover_cpu_sensors
from sensors.gpu_sensor import discover_gpu_sensors
from sensors.system_sensor import discover_memory_sensors, discover_storage_sensors


def get_process_memory_mb() -> float:
    """Return current process RSS memory in MB."""
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)


def bench_poll_cycle(cycles: int = 50) -> None:
    """Simulate polling cycles and measure performance."""
    print(f"Benchmarking poll cycle ({cycles} cycles)\n")

    all_sensors = []
    all_sensors.extend(discover_cpu_sensors())
    all_sensors.extend(discover_gpu_sensors())
    all_sensors.extend(discover_memory_sensors())
    all_sensors.extend(discover_storage_sensors())

    mem_before = get_process_memory_mb()
    cycle_times = []

    for i in range(cycles):
        start = time.perf_counter()
        for sensor in all_sensors:
            sensor.get_temperature()
        elapsed = (time.perf_counter() - start) * 1000
        cycle_times.append(elapsed)

    mem_after = get_process_memory_mb()

    avg = sum(cycle_times) / len(cycle_times)
    print(f"{'Sensors polled':<30} {len(all_sensors):>10}")
    print(f"{'Cycles run':<30} {cycles:>10}")
    print(f"{'Avg cycle time':<30} {avg:>9.2f}ms")
    print(f"{'Min cycle time':<30} {min(cycle_times):>9.2f}ms")
    print(f"{'Max cycle time':<30} {max(cycle_times):>9.2f}ms")
    print(f"{'Std deviation':<30} {_stddev(cycle_times):>9.2f}ms")
    print(f"{'Memory before':<30} {mem_before:>8.1f}MB")
    print(f"{'Memory after':<30} {mem_after:>8.1f}MB")
    print(f"{'Memory delta':<30} {mem_after - mem_before:>8.1f}MB")
    print()

    budget_ms = 1000
    overhead_pct = (avg / budget_ms) * 100
    print(f"{'Poll interval budget':<30} {budget_ms:>8}ms")
    print(f"{'CPU time used':<30} {overhead_pct:>8.1f}%")
    print(f"{'Headroom':<30} {100 - overhead_pct:>8.1f}%")

    if overhead_pct > 50:
        print("\n[!] WARNING: Polling uses >50% of the interval budget.")
    else:
        print(f"\n[+] OK: {overhead_pct:.1f}% of budget — plenty of headroom.")


def _stddev(values: list[float]) -> float:
    """Compute standard deviation."""
    avg = sum(values) / len(values)
    variance = sum((x - avg) ** 2 for x in values) / len(values)
    return variance ** 0.5


if __name__ == "__main__":
    bench_poll_cycle()
