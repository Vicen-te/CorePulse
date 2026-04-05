# ThermalCore — HW Monitor

A lightweight, real-time hardware monitoring application for Linux desktops. Built with Python and Qt6 (PySide6), it reads CPU, GPU, memory, and storage sensors and displays them in a tree view with live updates, per-sensor alerts, and CSV export.

Designed to use minimal resources: **0.1% CPU**, **~50 MB RAM**, **200ms startup**.

## Features

**Monitoring**
- CPU: per-core temperatures (lm-sensors), clock speed, per-core load, package power (Intel RAPL)
- NVIDIA GPU: temperature, core/memory clocks, GPU/memory load, VRAM, power draw, fan speed (via pynvml)
- AMD GPU: temperature via sysfs hwmon
- Memory: usage percentage, used/available GB
- Storage: NVMe drive temperatures, free disk space per partition

**Interface**
- Tree view with 3-level hierarchy: Hardware > Sensor Type > Individual Sensor
- 5 columns: Sensor | Value | Min | Max | Alert
- Auto dark/light theme following system preference (Ubuntu color palette)
- Color-coded temperatures: green (<50C), yellow (50-70), orange (70-85), red (>85)
- System tray icon with hottest temperature tooltip
- Expand/collapse hardware sections

**Actions**
- Per-sensor alerts: double-click the Alert column to set a threshold, desktop notification when exceeded
- Reset Min/Max: clear all tracked minimums and maximums
- Clear Alerts: remove all configured thresholds
- Export CSV: save all recorded sensor data with timestamps

**IPC**
- Unix socket at `/tmp/thermalcore.sock` broadcasts alert events as JSON
- External apps can connect and react to overheating (e.g., auto-shutdown workloads)
- See `examples/` for demo apps

## Screenshot layout

```
+-------------------------+---------+---------+---------+----------+
| Host: vicen  CPU: i7-14700K  GPU: RTX 4070 Ti SUPER  Up: 2d 3h |
+-------------------------+---------+---------+---------+----------+
| Sensor                  | Value   | Min     | Max     | Alert    |
+-------------------------+---------+---------+---------+----------+
| > CPU - Intel i7-14700K                                         |
|   > Temperatures        |         |         |         |          |
|     Package id 0        | 45.0 C  | 38.0 C  | 72.0 C  | 85.0 C  |
|     Core 0              | 42.0 C  | 36.0 C  | 68.0 C  |          |
|   > Clocks              |         |         |         |          |
|     CPU Clock           | 4200MHz | 800MHz  | 5000MHz |          |
|   > Load                |         |         |         |          |
|     CPU Total           | 12.3 %  |  0.0 %  | 98.5 %  | 90.0 %  |
| > GPU - RTX 4070 Ti SUPER                                       |
|   > Temperatures        |         |         |         |          |
|     GPU Core            | 41.0 C  | 38.0 C  | 78.0 C  | 85.0 C  |
|   > Power               |         |         |         |          |
|     GPU Power           | 15.8 W  | 12.0 W  | 280.0 W |          |
|   > Fans                |         |         |         |          |
|     GPU Fan             |    0 %  |    0 %  |   75 %  |          |
| > Memory - 32 GB        |         |         |         |          |
|   > Load                |         |         |         |          |
|     Memory              | 31.1 %  | 28.0 %  | 85.0 %  |          |
| > Storage               |         |         |         |          |
|   > Temperatures        |         |         |         |          |
|     Composite (Drv 1)   | 30.9 C  | 28.0 C  | 42.0 C  |          |
|   > Usage               |         |         |         |          |
|     Free Space (/)      | 388.9 / 456.3 GB  |         |          |
+-------------------------+---------+---------+---------+----------+
| [Reset Min/Max]  [Clear Alerts]                    [Export CSV]  |
+-------------------------+---------+---------+---------+----------+
```

## How it works

### Tech stack

| Component | Technology | Role |
|---|---|---|
| GUI framework | **PySide6** (Qt6 for Python) | Window, tree view, system tray, dialogs |
| CPU sensors | **psutil** + **lm-sensors** | Temperatures, clock, load via `/sys/class/hwmon/` |
| CPU power | **Intel RAPL** via sysfs | Reads `/sys/class/powercap/intel-rapl:0/energy_uj` directly |
| GPU sensors | **pynvml** (nvidia-ml-py) | Direct NVML C library calls via ctypes, <0.01ms per read |
| AMD GPU | sysfs hwmon | Reads `/sys/class/drm/card*/device/hwmon/*/temp1_input` |
| Memory/disk | **psutil** | `virtual_memory()`, `disk_usage()`, `disk_partitions()` |
| Theme detection | **gsettings** + **DBus** | Reads GNOME color-scheme, watches for live changes |
| IPC | **Unix domain socket** | JSON-line protocol for external app communication |

### Architecture

```
main.py                       Entry point
  +-- app.py                  Creates QApplication, applies QSS theme
        +-- MainWindow        Tree view, alerts, tray, CSV, IPC
              +-- Poller (QThread)
              |     +-- refresh_caches()    <-- 1 syscall per source per cycle
              |     +-- CpuSensor (psutil + RAPL sysfs)
              |     +-- GpuSensor (pynvml / AMD sysfs)
              |     +-- SystemSensor (memory + storage)
              +-- ThemeWatcher (gdbus monitor process)
              +-- AlertBroadcaster (Unix socket server)
```

### Data flow

1. **Poller thread** (background `QThread`) calls `refresh_caches()` once per cycle — this makes exactly **4 syscalls**: `sensors_temperatures()`, `cpu_percent()`, `cpu_freq()`, `virtual_memory()`. All 64 sensors then read from the cached results without any additional syscalls.

2. Poller emits a Qt signal with the readings dict. The **main thread** receives it and updates only the tree cells whose values actually changed (`reading.changed` flag), skipping unnecessary `setText()` calls and Qt repaints.

3. When a sensor exceeds its alert threshold, a **desktop notification** is shown and the event is **broadcast via IPC** to any connected external apps.

4. The **ThemeWatcher** runs `gdbus monitor` as a subprocess and listens for GNOME `SettingChanged` signals. When the system switches between dark/light mode, it regenerates the QSS stylesheet and reapplies all colors without restarting.

### Performance

Measured on Intel i7-14700K + RTX 4070 Ti SUPER + 2x NVMe (Ubuntu 24.04):

| Metric | Value |
|---|---|
| Poll cycle time | **0.47ms** avg (64 sensors) |
| CPU overhead | **0.1%** of 1s budget |
| Max sustainable poll rate | ~1400 Hz |
| Startup time | **200ms** |
| Memory (RSS) | **~50 MB** |
| Sensor log memory | ~18 MB for 10 hours (compact tuples) |

The bottleneck is `psutil.sensors_temperatures()` (~30ms) which reads all hwmon nodes including NVMe drives. This is called **once per cycle** via the shared cache, not once per sensor (which would be 25x slower). GPU reads via NVML are <0.01ms each. The only sensor above 0.1ms is GPU fan speed (~0.6ms), which is an NVML hardware query.

## Requirements

- **Python** 3.10+
- **Linux** with a desktop environment (tested on Ubuntu 24.04)
- **lm-sensors** for CPU temperature readings
- **NVIDIA driver** (optional, for GPU monitoring via pynvml)

## Installation

```bash
git clone https://github.com/Vicen-te/ThermalCore.git
cd ThermalCore
bash setup.sh
```

For manual installation, alternative distros, or troubleshooting, see [docs/INSTALL.md](docs/INSTALL.md).

## Usage

Search **ThermalCore** in your app launcher (after running `setup.sh`).

Or from the terminal:

```bash
cd ThermalCore
./thermalcore.sh
```

- **Double-click** the Alert column to set a per-sensor threshold
- **Reset Min/Max** clears tracked minimums and maximums
- **Clear Alerts** removes all configured thresholds
- **Export CSV** saves all recorded data with timestamps
- CPU Power (RAPL): `setup.sh` configures persistent permissions (survives reboots)

## IPC — External app communication

ThermalCore opens a Unix socket at `/tmp/thermalcore.sock`. When an alert fires, it sends a JSON message:

```json
{"event": "alert", "sensor": "GPU Core", "value": 85.0, "threshold": 80.0, "unit": "\u00b0C"}
```

Any app can connect and react. Two examples are included:

```bash
# CLI watcher — prints alerts, optionally kills a process
python examples/alert_watcher.py
python examples/alert_watcher.py --kill firefox

# GUI demo — small window that auto-closes on alert
python examples/demo_app.py
```

## Project structure

```
ThermalCore/
|-- src/
|   |-- main.py                  # Entry point
|   |-- app.py                   # QApplication setup + QSS theme
|   |-- sensors/
|   |   |-- base_sensor.py       # BaseSensor ABC, SensorType enum
|   |   |-- cpu_sensor.py        # CPU temps, clock, load, power + shared cache
|   |   |-- gpu_sensor.py        # NVIDIA (pynvml) + AMD (sysfs)
|   |   |-- system_sensor.py     # Memory, storage, NVMe
|   |   `-- poller.py            # Background QThread + SensorReading
|   |-- ui/
|   |   |-- main_window.py       # Tree view, alerts, tray, CSV
|   |   |-- icons.py             # App icon (SVG) + tree branch arrows
|   |   |-- system_info.py       # Header bar: hostname, CPU, GPU, uptime
|   |   |-- theme_watcher.py     # DBus listener for theme changes
|   |   `-- styles.py            # QSS stylesheet generator
|   `-- utils/
|       |-- config.py            # Constants, palettes, theme detection
|       `-- ipc.py               # Unix socket alert broadcaster
|-- tests/
|   |-- test_sensors.py          # 27 sensor unit tests
|   |-- test_config.py           # 14 config/theme unit tests
|   `-- benchmarks/
|       |-- bench_sensors.py     # Per-sensor read time profiling
|       |-- bench_polling.py     # Full poll cycle + memory measurement
|       `-- bench_startup.py     # Startup phase breakdown
|-- examples/
|   |-- alert_watcher.py         # CLI: react to alerts, kill processes
|   `-- demo_app.py              # GUI: auto-close on alert
|-- docs/
|   |-- INSTALL.md               # Full installation guide
|   |-- DEVELOPMENT.md           # Development log and decisions
|   |-- CONVENTIONS.md           # Code and commit standards
|   `-- PROGRESS.md              # Version history
|-- assets/icons/
|   `-- thermalcore.svg          # App icon (Ubuntu-style thermometer)
|-- requirements.txt
|-- pyproject.toml
|-- setup.sh                     # One-command installer
|-- thermalcore.sh               # Launcher script
`-- thermalcore.desktop          # GNOME desktop integration
```

For the full development story, architecture decisions, and changelog, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Tests

```bash
source .venv/bin/activate

# Unit tests (41 tests)
python -m pytest tests/ -v

# Performance benchmarks
python -m tests.benchmarks.bench_sensors    # Per-sensor read times
python -m tests.benchmarks.bench_polling    # Poll cycle overhead
python -m tests.benchmarks.bench_startup    # Startup phase breakdown
```

## License

MIT License — Copyright (c) 2026 Vicen-te
