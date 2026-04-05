# ThermalCore — HW Monitor

A lightweight, real-time hardware monitoring application for Linux desktops. Built with **Python** and **Qt6** ([PySide6](https://doc.qt.io/qtforpython-6/)), it reads CPU, GPU, memory, and storage sensors and displays them in a tree view with live updates, per-sensor alerts, and CSV export.

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
- Configurable update rate (0.5s / 1s / 2s / 4s)

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
| [0.5s|1s|2s|4s] [Reset Min/Max] [Clear Alerts]    [Export CSV]  |
+-------------------------+---------+---------+---------+----------+
```

---

## Installation

### Quick install (Ubuntu)

```bash
git clone https://github.com/Vicen-te/ThermalCore.git
cd ThermalCore
bash setup.sh
```

The script installs system dependencies (`lm-sensors`, `libxcb-cursor0`, `python3-venv`), creates a virtual environment, installs Python packages, sets up persistent CPU power monitoring (Intel RAPL udev rule), and registers the app in your desktop launcher with its icon.

It requires `sudo` for system packages and the udev rule. It's idempotent — running it again skips completed steps.

### Manual install

```bash
# System dependencies (Ubuntu/Debian)
sudo apt install lm-sensors libxcb-cursor0 python3-venv
sudo sensors-detect

# Clone and setup
git clone https://github.com/Vicen-te/ThermalCore.git
cd ThermalCore
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For **Fedora**: `sudo dnf install lm_sensors python3-devel` then `sudo sensors-detect`.
For **Arch**: `sudo pacman -S lm_sensors python` then `sudo sensors-detect`.

### CPU power monitoring (optional, Intel only)

```bash
# Persistent (survives reboots) — setup.sh does this automatically
echo 'SUBSYSTEM=="powercap", ACTION=="add", RUN+="/bin/chmod o+r /sys/class/powercap/intel-rapl:0/energy_uj"' \
    | sudo tee /etc/udev/rules.d/99-thermalcore-rapl.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=powercap
```

Without this, CPU Power shows 0.0 W. The app works normally otherwise.

### Desktop integration (optional)

```bash
# setup.sh does this automatically
mkdir -p ~/.local/share/icons/hicolor/scalable/apps
cp assets/icons/thermalcore.svg ~/.local/share/icons/hicolor/scalable/apps/thermalcore.svg
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
sed "s|__INSTALL_DIR__|$(pwd)|g" thermalcore.desktop > ~/.local/share/applications/thermalcore.desktop
update-desktop-database ~/.local/share/applications/
```

---

## Usage

Search **ThermalCore** in your app launcher (after running `setup.sh`).

Or from the terminal:

```bash
cd ThermalCore
./thermalcore.sh
```

- **Double-click** the Alert column to set a per-sensor threshold
- **Update rate selector** (bottom bar) — choose 0.5s, 1s, 2s, or 4s
- **Reset Min/Max** clears tracked minimums and maximums
- **Clear Alerts** removes all configured thresholds
- **Export CSV** saves all recorded data with timestamps

### Updating

```bash
cd ThermalCore && git pull
source .venv/bin/activate && pip install -r requirements.txt
```

### Uninstalling

```bash
rm ~/.local/share/applications/thermalcore.desktop
rm ~/.local/share/icons/hicolor/scalable/apps/thermalcore.svg
sudo rm -f /etc/udev/rules.d/99-thermalcore-rapl.rules
rm -rf /path/to/ThermalCore
```

---

## How it works

### Tech stack

| Component | Technology | Role |
|---|---|---|
| GUI | [PySide6](https://doc.qt.io/qtforpython-6/) (Qt6 for Python) | Window, tree view, system tray, dialogs, QSS theming |
| CPU sensors | [psutil](https://github.com/giampaolo/psutil) + [lm-sensors](https://hwmon.wiki.kernel.org/) | Temperatures, clock, load via `/sys/class/hwmon/` |
| CPU power | Intel RAPL via sysfs | Reads `/sys/class/powercap/intel-rapl:0/energy_uj` directly |
| GPU sensors | [pynvml](https://github.com/gpuopenanalytics/pynvml) (nvidia-ml-py) | Direct NVML C library calls via ctypes |
| AMD GPU | sysfs hwmon | Reads `/sys/class/drm/card*/device/hwmon/*/temp1_input` |
| Memory/disk | [psutil](https://github.com/giampaolo/psutil) | `virtual_memory()`, `disk_usage()`, `disk_partitions()` |
| Theme | gsettings + DBus | Reads GNOME `color-scheme`, watches for live changes via `gdbus monitor` |
| IPC | Unix domain socket | JSON-line protocol at `/tmp/thermalcore.sock` |

### Architecture

```
main.py                       Entry point
  +-- app.py                  Creates QApplication, applies QSS theme
        +-- MainWindow        Tree view, alerts, tray, CSV, IPC
              +-- Poller (QThread)
              |     +-- refresh_caches()    <-- 4 syscalls per cycle
              |     +-- CpuSensor (psutil + RAPL sysfs)
              |     +-- GpuSensor (pynvml / AMD sysfs)
              |     +-- SystemSensor (memory + storage)
              +-- ThemeWatcher (gdbus monitor subprocess)
              +-- AlertBroadcaster (Unix socket server)
```

### Data flow

1. **Poller thread** (background `QThread`) calls `refresh_caches()` once — this makes exactly **4 syscalls** per cycle: `sensors_temperatures()`, `cpu_percent()`, `cpu_freq()`, `virtual_memory()`. All 64 sensors then read from the cached results.

2. Poller emits a Qt signal. The **main thread** updates only the tree cells whose values changed (`reading.changed` flag), skipping unnecessary Qt repaints.

3. When a sensor exceeds its threshold, a **desktop notification** fires and the event is **broadcast via IPC** to connected external apps.

4. **ThemeWatcher** runs `gdbus monitor` and listens for GNOME `SettingChanged` signals — regenerates the QSS stylesheet live without restarting.

### Performance

Measured on Intel i7-14700K + RTX 4070 Ti SUPER + 2x NVMe (Ubuntu 24.04):

| Metric | Value |
|---|---|
| Poll cycle time | **0.47ms** avg (64 sensors) |
| CPU overhead | **0.1%** of 1s budget |
| Max sustainable poll rate | ~1400 Hz |
| Startup time | **200ms** |
| Memory (RSS) | **~50 MB** |

The bottleneck is `psutil.sensors_temperatures()` (~30ms) which reads all hwmon nodes including NVMe drives. This is called **once per cycle** via the shared cache — not once per sensor (which would be 25x slower).

---

## IPC — External app communication

ThermalCore opens a Unix socket at `/tmp/thermalcore.sock`. When an alert fires, it sends:

```json
{"event": "alert", "sensor": "GPU Core", "value": 85.0, "threshold": 80.0, "unit": "\u00b0C"}
```

Any app can connect and react. Two examples included:

```bash
# CLI watcher — prints alerts, optionally kills a process
python examples/alert_watcher.py
python examples/alert_watcher.py --kill firefox

# GUI demo — window that auto-closes when an alert fires
python examples/demo_app.py
```

---

## Contributing

### Project structure

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
|       |-- bench_polling.py     # Full poll cycle + memory
|       `-- bench_startup.py     # Startup phase breakdown
|-- examples/
|   |-- alert_watcher.py         # CLI: react to alerts
|   `-- demo_app.py              # GUI: auto-close on alert
|-- docs/
|   |-- CODING_STANDARDS.md      # How to write code (for AI and contributors)
|   `-- COMMIT_STANDARDS.md      # Git commit conventions
|-- assets/icons/
|   `-- thermalcore.svg
|-- requirements.txt
|-- pyproject.toml
|-- setup.sh                     # One-command installer
|-- thermalcore.sh               # Launcher script
`-- thermalcore.desktop          # GNOME desktop integration
```

### How to add a new sensor

1. Create a class extending `BaseSensor` in the appropriate file (or a new one under `src/sensors/`)
2. Implement `get_temperature()`, `get_name()`, `is_available()`, `get_hardware_group()`, `get_type_group()`
3. Add a `discover_*()` function and call it from `MainWindow._discover_sensors()`
4. If the sensor reads from a syscall that others share, add it to `refresh_caches()` in `cpu_sensor.py`
5. Run `python -m pytest tests/ -v` to verify

### Running tests

```bash
source .venv/bin/activate

# Unit tests (41 tests)
python -m pytest tests/ -v

# Performance benchmarks
python -m tests.benchmarks.bench_sensors
python -m tests.benchmarks.bench_polling
python -m tests.benchmarks.bench_startup
```

### Code standards

See [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md) for naming, type hints, docstrings, and file structure.
See [docs/COMMIT_STANDARDS.md](docs/COMMIT_STANDARDS.md) for git commit format.

---

## Known issues

- **CPU Fan RPM** — not available on all motherboards. Depends on the sensor chip (nct6775, it87) being loaded by lm-sensors. Some boards only expose ACPI on/off state.
- **RAM Temperature** — requires DIMM/SPD temperature sensors, which most consumer boards don't expose.
- **AMD GPU** — basic support (temperature only). Clocks, load, and power require ROCm-SMI integration.
- **Multi-GPU** — currently reads only the first NVIDIA GPU (device index 0).
- **Wayland** — Qt6 system tray icons may not appear on all Wayland compositors.
- **Dock visibility** — the app only appears in the GNOME dock when launched from the app launcher (Show Apps), not from a terminal. This is standard GNOME behavior.

## Troubleshooting

| Problem | Solution |
|---|---|
| No temperatures shown | Run `sudo sensors-detect` then `sensors` to verify |
| No GPU detected | Normal without NVIDIA proprietary drivers. Check with `nvidia-smi` |
| CPU Power shows 0.0 W | Run `setup.sh` or apply RAPL udev rule manually (see above) |
| PySide6 xcb error | `sudo apt install libxcb-cursor0` |
| App not in dock | Launch from Show Apps, not terminal |

## License

MIT License — Copyright (c) 2026 Vicen-te
