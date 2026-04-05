"""
Application startup performance benchmark.

Measures the time each startup phase takes: import, sensor discovery,
and UI initialization. Helps identify bottlenecks in app launch time.

Usage:
    cd CorePulse
    source .venv/bin/activate
    python -m tests.bench_startup
"""

import sys
import time
sys.path.insert(0, "src")


def bench_startup() -> None:
    """Benchmark each phase of application startup."""
    print("Benchmarking startup phases\n")
    print(f"{'Phase':<35} {'Time (ms)':>10}")
    print("-" * 48)

    total = 0.0

    # Phase 1: Import sensor modules
    start = time.perf_counter()
    from sensors.cpu_sensor import discover_cpu_sensors
    from sensors.gpu_sensor import discover_gpu_sensors
    from sensors.system_sensor import discover_memory_sensors, discover_storage_sensors
    elapsed = (time.perf_counter() - start) * 1000
    total += elapsed
    print(f"{'Import sensor modules':<35} {elapsed:>10.2f}")

    # Phase 2: Import Qt
    start = time.perf_counter()
    from PySide6.QtWidgets import QApplication
    elapsed = (time.perf_counter() - start) * 1000
    total += elapsed
    print(f"{'Import PySide6':<35} {elapsed:>10.2f}")

    # Phase 3: Sensor discovery
    start = time.perf_counter()
    sensors = []
    sensors.extend(discover_cpu_sensors())
    sensors.extend(discover_gpu_sensors())
    sensors.extend(discover_memory_sensors())
    sensors.extend(discover_storage_sensors())
    elapsed = (time.perf_counter() - start) * 1000
    total += elapsed
    print(f"{'Sensor discovery ({n} sensors)':<35} {elapsed:>10.2f}".format(n=len(sensors)))

    # Phase 4: QApplication creation
    start = time.perf_counter()
    app = QApplication.instance() or QApplication(sys.argv)
    elapsed = (time.perf_counter() - start) * 1000
    total += elapsed
    print(f"{'QApplication creation':<35} {elapsed:>10.2f}")

    # Phase 5: Theme detection
    start = time.perf_counter()
    from utils.config import detect_dark_mode
    is_dark = detect_dark_mode()
    elapsed = (time.perf_counter() - start) * 1000
    total += elapsed
    print(f"{'Theme detection (dark={d})':<35} {elapsed:>10.2f}".format(d=is_dark))

    # Phase 6: Window creation
    start = time.perf_counter()
    from ui.main_window import MainWindow
    window = MainWindow()
    elapsed = (time.perf_counter() - start) * 1000
    total += elapsed
    print(f"{'MainWindow creation':<35} {elapsed:>10.2f}")

    print("-" * 48)
    print(f"{'Total startup time':<35} {total:>10.2f}")
    print()

    if total > 2000:
        print(f"[!] Startup takes {total/1000:.1f}s — may feel slow.")
    elif total > 1000:
        print(f"[~] Startup takes {total/1000:.1f}s — acceptable.")
    else:
        print(f"[+] Startup takes {total/1000:.1f}s — fast.")

    # Cleanup
    window.close()


if __name__ == "__main__":
    bench_startup()
