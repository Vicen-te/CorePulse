# ThermalCore — HW Monitor

A lightweight hardware monitoring application for Linux. Features a tree view with expandable sections showing temperatures, clocks, load, power, and more.

## Features

- **Tree view** with 3-level hierarchy:
  - **Hardware** → **Sensor Type** → **Individual Sensor**
- **Columns**: Sensor | Value | Min | Max
- **CPU monitoring**: per-core temperatures, clock speed, per-core load, package power (Intel RAPL)
- **NVIDIA GPU**: temperature, core/memory clocks, GPU/memory load, VRAM usage, power draw, fan speed
- **AMD GPU**: temperature via sysfs hwmon
- **Memory**: usage percentage, used/available GB
- **Storage**: NVMe temperatures, disk usage per partition (used / total GB)
- **Background polling** — zero UI blocking via QThread
- **NVIDIA via pynvml** — direct NVML library calls (<0.01ms per read)
- **Dark theme** with color-coded temperatures
- **System tray** — minimize to tray, tooltip with hottest temp
- **Alerts** — configurable threshold with desktop notifications
- **CSV export** — save all sensor data with timestamps

## Screenshot layout

```
┌──────────────────────────────────────────────────────────┐
│ Host: vicen | CPU: i7-14700K | GPU: RTX 4070 | Up: 2d   │
├─────────────────────────┬────────┬────────┬──────────────┤
│ Sensor                  │ Value  │ Min    │ Max          │
├─────────────────────────┼────────┼────────┼──────────────┤
│ ▼ CPU — Intel i7-14700K │        │        │              │
│   ▼ Temperatures        │        │        │              │
│     Package id 0        │ 45.0°C │ 38.0°C │ 72.0°C      │
│     Core 0              │ 42.0°C │ 36.0°C │ 68.0°C      │
│   ▼ Clocks              │        │        │              │
│     CPU Clock           │ 4200 MHz│ 800 MHz│ 5000 MHz   │
│   ▼ Load                │        │        │              │
│     CPU Total           │ 12.3 % │ 0.0 % │ 98.5 %      │
│   ▼ Power               │        │        │              │
│     CPU Package         │ 28.5 W │ 5.2 W │ 125.0 W     │
│ ▼ GPU — RTX 4070 Ti     │        │        │              │
│   ▼ Temperatures        │        │        │              │
│     GPU Core            │ 41.0°C │ 38.0°C │ 78.0°C      │
│   ▼ Power               │        │        │              │
│     GPU Power           │ 15.8 W │ 12.0 W │ 280.0 W    │
│ ▼ Memory — 32 GB        │        │        │              │
│   ▼ Load                │        │        │              │
│     Memory              │ 31.1 % │ 28.0 % │ 85.0 %     │
│ ▼ Storage               │        │        │              │
│   ▼ Temperatures        │        │        │              │
│     Composite (Drive 1) │ 30.9°C │ 28.0°C │ 42.0°C     │
│   ▼ Usage               │        │        │              │
│     Used Space (/)      │ 44.4 / 456.3 GB │             │
└─────────────────────────┴────────┴────────┴──────────────┘
│ Alert: [85°C]                              [Export CSV]   │
└──────────────────────────────────────────────────────────┘
```

## Requirements

- **Python** 3.10+
- **Linux** (tested on Ubuntu 22.04+)
- **lm-sensors** (CPU temperatures via psutil)
- **NVIDIA driver** (optional, for GPU monitoring via pynvml)

```bash
sudo apt install lm-sensors libxcb-cursor0
sudo sensors-detect
```

## Installation

```bash
git clone https://github.com/Vicen-te/ThermalCore.git
cd ThermalCore
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
source .venv/bin/activate
python src/main.py
```

- Click **▼/►** arrows to expand/collapse hardware sections
- Temperatures are color-coded: green (<50°C), yellow (50-70), orange (70-85), red (>85)
- Close window → minimizes to system tray
- Double-click tray icon → restore window
- **Export CSV** saves all recorded data

## Project structure

```
ThermalCore/
├── src/
│   ├── main.py
│   ├── app.py
│   ├── sensors/
│   │   ├── base_sensor.py     # SensorType enum, format_value()
│   │   ├── cpu_sensor.py      # Temp, clock, load, power
│   │   ├── gpu_sensor.py      # NVIDIA (pynvml) + AMD (sysfs)
│   │   ├── system_sensor.py   # Memory, storage, NVMe
│   │   └── poller.py          # Background QThread
│   ├── ui/
│   │   ├── main_window.py     # 3-level tree view
│   │   └── styles.py          # Dark theme QSS
│   └── utils/
│       └── config.py
├── requirements.txt
├── pyproject.toml
├── .python-version
└── setup.sh
```

## License

MIT License — Copyright (c) 2026 Vicen-te
