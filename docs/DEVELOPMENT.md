# Development Log

This document describes the full development process of ThermalCore: the motivation behind the project, how the architecture evolved, what technical challenges were solved, and the reasoning behind every major decision.

---

## Why ThermalCore?

On Windows, tools like HWMonitor and HWiNFO make it easy to check CPU/GPU temperatures, clock speeds, power draw, and fan status in a single window. On Linux, the equivalent workflow involves running `sensors` in a terminal, checking `nvidia-smi` separately, and piecing together information from multiple tools. There's no single, lightweight desktop app that shows everything in one place.

ThermalCore was built to fill that gap — a real-time hardware monitoring app for Linux desktops, built with Python and Qt (PySide6). It reads from lm-sensors, NVML, psutil, and sysfs to display all sensor data in a clean tree view with live updates, alerts, and CSV export.

## How it was built

The project went through multiple iterations over two days, starting from a basic sensor reader and evolving into a polished desktop application with full GNOME integration. Each version addressed specific problems discovered during real-world testing.

---

## v1 — First Working Version

**Goal:** Get a window on screen that shows CPU and GPU temperatures updating in real time.

### Sensor layer

The foundation is a sensor abstraction. Every sensor in the app implements a common interface defined in `base_sensor.py`:

- `read()` — poll the hardware and return the current value
- `name` — human-readable label (e.g., "Core 0", "GPU Core")
- `sensor_type` — enum: TEMPERATURE, CLOCK, LOAD, POWER, FAN, DATA
- `format_value()` — returns the value with its unit (e.g., "45.0°C", "4200 MHz")

**CPU** (`cpu_sensor.py`) reads temperatures from `psutil.sensors_temperatures()`, which under the hood reads lm-sensors. Clock speed comes from `psutil.cpu_freq()`, and load from `psutil.cpu_percent(percpu=True)`. CPU power is read directly from Intel RAPL via sysfs (`/sys/class/powercap/intel-rapl:0/energy_uj`), computing the delta between two readings to get watts.

**GPU** (`gpu_sensor.py`) supports NVIDIA via pynvml and AMD via sysfs hwmon. For NVIDIA, the NVML library is initialized once at startup and provides temperature, clocks (core + memory), utilization (GPU + memory), VRAM usage, power draw, and fan speed — all in a single call per poll cycle. If no GPU is found, the section simply doesn't appear.

**System** (`system_sensor.py`) covers memory (via psutil) and storage. Storage sensors detect NVMe drives with temperature readings (from `psutil.sensors_temperatures()`) and show free disk space per partition, filtering out snap/squashfs/tmpfs virtual mounts.

### UI

The first UI version used individual sensor cards with sparkline charts (pyqtgraph). This was abandoned in v2 because pyqtgraph added complexity and the charts weren't adding much value for a monitoring tool — numbers are what matter.

### Polling

Initially, sensor reading happened on a `QTimer` in the main thread. This worked but could cause brief UI freezes when sensors took longer to respond (especially NVIDIA's first NVML call). This was fixed in v2 with a background thread.

---

## v2 — Architecture Rewrite

**Goal:** Replace the card-based UI with a tree view. Move polling off the main thread. Remove pyqtgraph.

### Tree view

The UI was rebuilt around a `QTreeWidget` with a 3-level hierarchy:

```
Hardware (CPU — Intel i7-14700K)
  └── Sensor Type (Temperatures)
        └── Individual Sensor (Core 0: 45.0°C)
```

Columns: Sensor | Value | Min | Max | Alert

This structure mirrors how HWiNFO organizes sensors and makes it easy to scan the data. Hardware groups show the model name in the header. Type groups (Temperatures, Clocks, Load, etc.) are collapsible sub-nodes.

### Background polling

Sensor reads moved to a `QThread` (`poller.py`). The poller runs a loop at the configured interval (default 1 second), reads all sensors, and emits a Qt signal with the results. The main thread receives the signal and updates the tree — never touches hardware directly.

This eliminated all UI freezes. The poller also handles the shared CPU load cache: `psutil.cpu_percent(percpu=True)` must be called once per cycle (not per-core), so the poller calls it once and distributes the values to individual core sensors.

### NVIDIA via pynvml

The v1 GPU sensor used `nvidia-smi` as a subprocess, parsing its CSV output. This worked but was slow (~50ms per call) and fragile. v2 switched to pynvml (the `nvidia-ml-py` package), which calls NVML directly via ctypes. Each sensor read takes <0.01ms and is much more reliable.

---

## v2.1–v2.6 — Fixes and Polish

These versions were about fixing real-world issues discovered during testing on the development machine (Intel i7-14700K + RTX 4070 Ti SUPER + NVMe SSDs on Ubuntu 24.04).

### 3-level tree hierarchy (v2.1)

The initial tree view was flat — just a list of sensors. v2.1 introduced a proper 3-level hierarchy: Hardware → Sensor Type → Individual Sensor. Each hardware group (CPU, GPU, Memory, Storage) shows its model name in the header. Under each hardware group, sensors are organized by type (Temperatures, Clocks, Load, Power, Fans, Usage). This makes it easy to find any specific reading at a glance.

### Bugfixes and storage redesign (v2.2)

Several issues were found during real-world testing:

- **CPU load was wrong for cores 1+** — `psutil.cpu_percent(percpu=True)` must be called once per poll cycle, not once per core. The fix introduced a shared poll cache in the poller thread.
- **GPU header was blank** — NVML wasn't initialized before querying the GPU name. Moved initialization earlier.
- **Duplicate NVMe sensor names** — systems with multiple NVMe drives had duplicate "Composite" entries. Fixed by adding drive numbers (Drv 1, Drv 2, etc.).
- **Storage cleanup** — removed snap/squashfs/tmpfs virtual mounts from the storage list, and redesigned the section to show free/total GB instead of load percentages.

### Auto-hiding empty sensors (v2.4)

Not all sensors report data on all hardware. Rather than showing "N/A" everywhere, sensors that produce no data after 3 poll cycles are automatically hidden, along with their parent type group if all children are hidden. This keeps the tree clean.

### GPU fan at 0% (v2.5)

Modern GPUs use a 0-RPM fan mode when idle. The original code treated 0 as "no data" and hid the sensor. Fixed by changing the GPU fan sensor type from LOAD to FAN and allowing 0 as a valid value for min/max tracking.

### Physical core mapping (v2.6)

One of the trickier bugs. lm-sensors reports temperatures for physical cores (Core 0, Core 4, Core 8...) while `psutil.cpu_percent(percpu=True)` returns loads for logical CPUs (0, 1, 2, 3...). On a CPU with hyperthreading, Core 0 (physical) maps to logical CPUs 0 and 1.

The fix reads `/proc/cpuinfo` to build a physical→logical core map, then averages the load of both hyperthreaded siblings to produce a single load value per physical core. This makes the Load section match the Temperature section — Core 0's load corresponds to Core 0's temperature.

---

## v2.5 — Per-Metric Alerts

**Goal:** Let the user set a temperature/load threshold on any individual sensor.

The original design had a single global temperature threshold. This was replaced with a per-sensor system:

- A new **Alert** column was added to the tree view
- Double-clicking the Alert cell on any leaf sensor opens an input dialog
- The user sets a threshold value (e.g., 85.0 for a temperature sensor)
- When the sensor value exceeds the threshold, the row turns red and a desktop notification is sent (via `QSystemTrayIcon.showMessage()`)
- The alert only fires once per threshold crossing (not on every poll)

---

## v2.7–v2.8 — Theme and Permissions

### Auto dark/light theme

The app detects the system theme preference using two methods:

1. GNOME `color-scheme` setting (gsettings: `org.gnome.desktop.interface color-scheme`)
2. GTK theme name as fallback (themes containing "dark" in the name)

Two complete color palettes are defined in `config.py` — dark and light. The active palette is selected at startup and monitored via a DBus signal watcher that listens for theme changes. When the system theme switches, the app updates its stylesheet and redraws everything in real time.

Temperature colors also adapt: green/yellow/orange/red in dark mode use brighter tones, while light mode uses darker, more readable versions.

### Persistent RAPL permissions

Intel RAPL energy counters (`/sys/class/powercap/intel-rapl:0/energy_uj`) are readable only by root by default. The setup script installs a udev rule that automatically sets read permissions when the powercap subsystem loads. This survives reboots, so `setup.sh` only needs to run once.

---

## v2.9 — Ubuntu Theme and Desktop Integration

### Ubuntu color palette

The original dark theme used a navy blue palette (#1a1a2e, #16213e, #0f3460) which didn't match Ubuntu's visual style. The palettes were rebuilt using Ubuntu's design language:

- **Dark:** grey tones (#2b2b2b, #333333, #444444) with Ubuntu orange (#e95420) as the accent
- **Light:** clean whites (#fafafa, #ebebeb) with the same orange accent
- Temperature colors use GNOME/Ubuntu-adjacent tones (Tango-inspired greens, yellows, reds)

### App icon

The old icon was a red ring with a green circle inside — programmatically drawn and not very recognizable. The new icon is an SVG: a thermometer on a rounded dark square, using Ubuntu orange for the mercury. It's stored in `assets/icons/thermalcore.svg` and loaded at runtime. A programmatic fallback exists if the SVG file is missing.

### Desktop integration

Getting the app to show correctly in the GNOME dock required several pieces:

1. **`thermalcore.sh`** — a launcher script that activates the venv and runs the app. The original `.desktop` file had `bash -c '...'` with unescaped `'` and `&&` characters, which made it fail `desktop-file-validate` and prevented GNOME's window matcher (BAMF) from recognizing it
2. **`StartupWMClass=thermalcore`** in the `.desktop` file — tells GNOME which X11 WM_CLASS to associate with this app entry
3. **`setDesktopFileName("thermalcore")`** in the Qt app — sets the `_GTK_APPLICATION_ID` window property on X11 and the app-id on Wayland
4. **Icon in XDG location** — copying the SVG to `~/.local/share/icons/hicolor/scalable/apps/` so GNOME's icon theme system can find it, instead of using an absolute file path

---

## v3.0 — Code Refactoring and Tests

### Module extraction

`main_window.py` had grown to 760 lines with mixed concerns: UI layout, icon generation, system info gathering, and theme watching. These were extracted into dedicated modules:

- **`ui/icons.py`** — app icon (SVG loader + programmatic fallback) and tree branch arrow icons
- **`ui/system_info.py`** — hostname, CPU model, GPU model, uptime collection for the header bar
- **`ui/theme_watcher.py`** — DBus `gdbus monitor` process that listens for GNOME theme changes

This reduces `main_window.py` to pure UI logic (tree view, alerts, tray, CSV export) and makes each module independently testable.

### Documentation reorganized

All documentation moved to a `docs/` folder:

- `docs/INSTALL.md` — complete installation guide (quick, manual, Fedora/Arch, troubleshooting)
- `docs/DEVELOPMENT.md` — this file
- `docs/CONVENTIONS.md` — code and commit standards
- `docs/PROGRESS.md` — version history

Only `README.md` and `CLAUDE.md` stay at the project root (standard practice for GitHub repos).

### Unit tests

41 unit tests covering:

- **Sensor interface** — all sensors implement `BaseSensor` correctly (name, type, group, reading)
- **Format values** — every `SensorType` formats correctly (°C, MHz, %, W, GB)
- **CPU sensors** — discovery, temperature ranges, load values
- **Memory sensors** — load in 0-100%, positive used/available
- **Storage sensors** — positive free space
- **GPU sensors** — graceful behavior with and without GPU
- **Config** — palette keys, hex colors, theme detection, threshold ordering

Run: `python -m pytest tests/ -v`

### Performance benchmarks

Three benchmarks in `tests/benchmarks/`:

- **bench_sensors** — measures individual sensor read times. Identifies slow sensors.
- **bench_polling** — simulates full poll cycles. Reports average cycle time, memory usage, and CPU overhead percentage.
- **bench_startup** — times each startup phase (imports, discovery, Qt init, window creation).

Key findings from benchmarking:
- Startup: ~380ms total (fast)
- Memory: ~50MB RSS (lightweight)
- Sensor discovery: 130ms (NVML init is the slowest part)

---

## Architecture Summary

```
main.py                     Entry point, sets argv[0] for WM_CLASS
  +-- app.py                Creates QApplication, applies theme
        +-- MainWindow      Tree view, tray icon, alerts, CSV export
              +-- Poller (QThread)
              |     +-- CpuSensor (psutil + RAPL sysfs)
              |     +-- GpuSensor (pynvml / AMD sysfs)
              |     +-- SystemSensor (memory + storage)
              +-- ThemeWatcher (DBus signal listener)
```

### Module map

| Module                | Lines | Responsibility                                |
|-----------------------|------:|-----------------------------------------------|
| `ui/main_window.py`  |   580 | Tree view, polling, alerts, tray, CSV export  |
| `sensors/cpu_sensor.py` | 352 | CPU temp, clock, load, power (RAPL)           |
| `sensors/gpu_sensor.py` | 309 | NVIDIA (pynvml) + AMD (sysfs) sensors         |
| `sensors/system_sensor.py` | 230 | Memory and storage sensors                 |
| `sensors/base_sensor.py` | 139 | Abstract base class, SensorType enum        |
| `utils/config.py`    |   113 | Constants, palettes, theme detection          |
| `sensors/poller.py`  |    99 | Background QThread sensor polling             |
| `ui/styles.py`       |    64 | QSS stylesheet generation                    |
| `ui/theme_watcher.py`|    48 | DBus theme change monitoring                  |
| `ui/system_info.py`  |    46 | System info for header bar                    |
| `ui/icons.py`        |    82 | App icon + branch arrows                      |

**Data flow:** Poller reads all sensors in background -> emits signal with results -> MainWindow updates tree widget on main thread -> temperature colors, min/max, and alerts evaluated per row.

**Config:** All constants, thresholds, color palettes, and theme detection live in `config.py`. The QSS stylesheet is generated dynamically in `styles.py` based on the active palette.

---

## Known Limitations

- **CPU Fan RPM** — not available on all motherboards. Depends on the sensor chip (nct6775, it87, etc.) being loaded by lm-sensors. Some boards only expose ACPI on/off state.
- **RAM Temperature** — requires DIMM/SPD temperature sensors on the motherboard, which most consumer boards don't expose.
- **AMD GPU** — basic support via sysfs hwmon (temperature only). No clocks, load, or power without ROCm-SMI integration.
- **Multi-GPU** — currently reads only the first NVIDIA GPU (device index 0).
- **Wayland** — Qt6 on Wayland has some quirks with system tray icons. The app works but the tray icon may not appear on all compositors.

---

## Tools and Dependencies

| Dependency    | Purpose                              | Why chosen                                                    |
|---------------|--------------------------------------|---------------------------------------------------------------|
| PySide6       | GUI framework (Qt6)                  | Official Qt bindings, LGPL license, mature and well-supported |
| psutil        | CPU temps, load, memory, disk        | Cross-platform, widely used, wraps lm-sensors on Linux        |
| nvidia-ml-py  | NVIDIA GPU monitoring                | Direct NVML calls, <0.01ms per read, no subprocess overhead   |
| lm-sensors    | Hardware sensor kernel drivers       | Standard Linux sensor infrastructure, required by psutil      |
