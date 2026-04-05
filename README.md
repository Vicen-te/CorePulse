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

### From .deb package (recommended)

Download the `.deb` from the [releases page](https://github.com/Vicen-te/ThermalCore/releases) and install:

```bash
sudo apt install ./thermalcore_3.0.0_amd64.deb
```

This installs ThermalCore system-wide to `/opt/thermalcore/`, creates the Python environment, configures CPU power monitoring, and adds it to your app launcher. Search **ThermalCore** in your apps or run `thermalcore` from the terminal.

To uninstall:

```bash
sudo apt remove thermalcore
```

### From source

```bash
git clone https://github.com/Vicen-te/ThermalCore.git
cd ThermalCore
make install
```

| Command | Action |
|---|---|
| `make install` | Install deps, venv, pip packages, RAPL, desktop launcher |
| `make run` | Launch the app |
| `make test` | Run unit tests |
| `make benchmark` | Run performance benchmarks |
| `make deb` | Build the `.deb` package |
| `make uninstall` | Remove launcher, icon, and udev rule |
| `make clean` | Delete venv and caches |

### Other distros

The Makefile uses `apt`. For Fedora/Arch, install dependencies manually first:

| Distro | Command |
|---|---|
| Fedora | `sudo dnf install lm_sensors python3-devel && sudo sensors-detect` |
| Arch | `sudo pacman -S lm_sensors python && sudo sensors-detect` |

Then run `make venv pip-deps desktop` to skip the apt step.

---

## Usage

Search **ThermalCore** in your app launcher, or from the terminal:

```bash
thermalcore          # if installed via .deb
make run             # if installed from source
```

- **Double-click** the Alert column to set a per-sensor threshold
- **Update rate selector** (bottom bar) — choose 0.5s, 1s, 2s, or 4s
- **Reset Min/Max** clears tracked minimums and maximums
- **Clear Alerts** removes all configured thresholds
- **Export CSV** saves all recorded data with timestamps

### Updating

```bash
cd ThermalCore
git pull
make install
```

### Uninstalling

```bash
cd ThermalCore
make uninstall
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

## IPC — Using ThermalCore from other projects

ThermalCore exposes a **Unix domain socket** at `/tmp/thermalcore.sock` that any application can connect to. When a sensor alert fires, ThermalCore sends a JSON message through the socket. This lets you build external tools that react to hardware events — for example, pausing a render job when the GPU overheats, or shutting down a game server when CPU temperatures are too high.

### Protocol

The protocol is simple: **one JSON object per line**, newline-delimited. Connect to the socket, read lines, parse JSON.

```json
{"event": "alert", "sensor": "GPU Core", "value": 85.0, "threshold": 80.0, "unit": "\u00b0C"}
```

| Field | Type | Description |
|---|---|---|
| `event` | string | Always `"alert"` (more event types may be added later) |
| `sensor` | string | Human-readable sensor name (e.g., "GPU Core", "CPU Total") |
| `value` | float | Current sensor value that triggered the alert |
| `threshold` | float | The threshold the user configured |
| `unit` | string | Unit of measurement (`°C`, `%`, `W`, `MHz`, `GB`) |

### Connecting from your own code

**Python:**

```python
import socket, json

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("/tmp/thermalcore.sock")

buffer = ""
while True:
    data = sock.recv(4096).decode()
    buffer += data
    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        event = json.loads(line)
        print(f"Alert: {event['sensor']} = {event['value']} {event['unit']}")
        # Your logic here: kill a process, send a notification, etc.
```

**Bash (with socat):**

```bash
socat - UNIX-CONNECT:/tmp/thermalcore.sock
```

**Any language** that supports Unix sockets can connect — Go, Rust, C, Node.js, etc.

### Running the examples

Both examples require ThermalCore to be running first, with at least one alert threshold configured (double-click the Alert column on any sensor).

**alert_watcher.py** — CLI tool that prints alerts and optionally kills a process:

```bash
source .venv/bin/activate

# Just watch and print alerts
python examples/alert_watcher.py

# Kill a process by name when any alert fires
python examples/alert_watcher.py --kill firefox

# Kill a specific PID when any alert fires
python examples/alert_watcher.py --kill-pid 12345
```

To test it quickly: set a very low threshold (e.g., 30°C on Package id 0) so it triggers immediately.

**demo_app.py** — small Qt window that auto-closes when it receives an alert:

```bash
source .venv/bin/activate
python examples/demo_app.py
```

The window shows "Connected to ThermalCore. Waiting for alert..." in green. When an alert fires, it turns red with the sensor info and closes after 2 seconds. This demonstrates how a workload app could self-terminate when the system overheats.

### Use case: leaving the PC unattended

Set alert thresholds on CPU and GPU temperature (e.g., 85°C), then run `alert_watcher.py --kill <your-workload>`. If temperatures exceed the threshold while you're away, ThermalCore will signal the watcher, which kills the workload to protect the hardware.

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

1. Create a class in the appropriate file (or a new one under `src/sensors/`) extending `BaseSensor`:

```python
class MyNewSensor(BaseSensor):
    def get_temperature(self) -> float:   # Return the current value
    def get_name(self) -> str:            # Human-readable name
    def is_available(self) -> bool:       # Can this sensor be read?
    def get_hardware_group(self) -> str:  # "CPU", "GPU", "Memory", "Storage", or new
    def get_type_group(self) -> str:      # "Temperatures", "Clocks", "Load", etc.
    def get_sensor_type(self) -> SensorType:  # For formatting (°C, MHz, %, W...)
```

2. Add a `discover_*()` function that returns `list[BaseSensor]`
3. Call it from `MainWindow._discover_sensors()` in `src/ui/main_window.py`
4. If the sensor reads from a syscall that others share (e.g., `psutil.sensors_temperatures()`), read from `_cache` instead of calling the syscall directly — see `cpu_sensor.py` for the pattern
5. Run tests to verify: `python -m pytest tests/ -v`
6. Add unit tests for the new sensor in `tests/test_sensors.py`

### Running tests

```bash
# Run all 41 unit tests
make test

# Run all performance benchmarks
make benchmark

# Or manually for more control:
source .venv/bin/activate
python -m pytest tests/test_sensors.py -v                                        # one file
python -m pytest tests/test_sensors.py::TestCpuSensors -v                        # one class
python -m pytest tests/test_sensors.py::TestFormatValue::test_temperature_format  # one method
```

### Writing new tests

Tests use `unittest` (stdlib) and run via `pytest`. Each test file is under `tests/` with `sys.path.insert(0, "src")` at the top so imports work.

Example — adding a test for a new sensor:

```python
# tests/test_sensors.py

class TestMyNewSensor(unittest.TestCase):
    def setUp(self) -> None:
        self.sensors = discover_my_sensors()

    def test_sensors_found(self) -> None:
        """At least one sensor should be discovered."""
        self.assertGreater(len(self.sensors), 0)

    def test_values_reasonable(self) -> None:
        """Values should be in a sane range."""
        for sensor in self.sensors:
            value = sensor.get_temperature()
            self.assertGreaterEqual(value, 0)

    def test_all_in_correct_group(self) -> None:
        """All sensors should report the correct hardware group."""
        for sensor in self.sensors:
            self.assertEqual(sensor.get_hardware_group(), "MyGroup")
```

### Running benchmarks

```bash
make benchmark
```

Benchmarks measure real hardware read times (not mocked). If you add a new sensor or change the cache, run `make benchmark` and check that the poll cycle stays under 5ms.

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
