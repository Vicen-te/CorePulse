# ThermalCore — HW Monitor

A lightweight hardware monitoring application for Linux. Features a tree view with expandable sections showing temperatures, clocks, load, power, and more.

## Features

- **Tree view** with 3-level hierarchy:
  - **Hardware** → **Sensor Type** → **Individual Sensor**
- **Columns**: Sensor | Value | Min | Max | Alert
- **Per-metric alerts** — double-click the Alert column to set a threshold per sensor
- **CPU monitoring**: per-core temperatures, clock speed, per-core load, package power (Intel RAPL)
- **NVIDIA GPU**: temperature, core/memory clocks, GPU/memory load, VRAM usage, power draw, fan speed
- **AMD GPU**: temperature via sysfs hwmon
- **Memory**: usage percentage, used/available GB
- **Storage**: NVMe temperatures, free disk space per partition (free / total GB)
- **Background polling** — zero UI blocking via QThread
- **NVIDIA via pynvml** — direct NVML library calls (<0.01ms per read)
- **Auto dark/light theme** — follows system preference, color-coded temperatures
- **System tray** — tooltip with hottest temp
- **CSV export** — save all sensor data with timestamps
- **Desktop integration** — appears in app launcher alongside other apps

## Screenshot layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ Host: vicen   CPU: i7-14700K   GPU: RTX 4070 Ti SUPER   Up: 2d 3h │
├───────────────────────┬──────────┬──────────┬──────────┬───────────┤
│ Sensor                │ Value    │ Min      │ Max      │ Alert     │
├───────────────────────┼──────────┼──────────┼──────────┼───────────┤
│ ▼ CPU — Intel i7-14700K                                            │
│   ▼ Temperatures      │          │          │          │           │
│     Package id 0      │  45.0°C  │  38.0°C  │  72.0°C  │  85.0°C  │
│     Core 0            │  42.0°C  │  36.0°C  │  68.0°C  │           │
│   ▼ Clocks            │          │          │          │           │
│     CPU Clock         │ 4200 MHz │  800 MHz │ 5000 MHz │           │
│   ▼ Load              │          │          │          │           │
│     CPU Total         │  12.3 %  │   0.0 %  │  98.5 %  │  90.0 %  │
│ ▼ GPU — RTX 4070 Ti SUPER                                         │
│   ▼ Temperatures      │          │          │          │           │
│     GPU Core          │  41.0°C  │  38.0°C  │  78.0°C  │  85.0°C  │
│   ▼ Power             │          │          │          │           │
│     GPU Power         │  15.8 W  │  12.0 W  │ 280.0 W  │           │
│   ▼ Fans              │          │          │          │           │
│     GPU Fan           │     0 %  │     0 %  │    75 %  │           │
│ ▼ Memory — 32 GB      │          │          │          │           │
│   ▼ Load              │          │          │          │           │
│     Memory            │  31.1 %  │  28.0 %  │  85.0 %  │           │
│ ▼ Storage             │          │          │          │           │
│   ▼ Temperatures      │          │          │          │           │
│     Composite (Drv 1) │  30.9°C  │  28.0°C  │  42.0°C  │           │
│   ▼ Usage             │          │          │          │           │
│     Free Space (/)    │  388.9 / 456.3 GB   │          │           │
├───────────────────────┴──────────┴──────────┴──────────┴───────────┤
│ Double-click Alert column to set threshold           [Export CSV]  │
└─────────────────────────────────────────────────────────────────────┘
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
bash setup.sh
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
source .venv/bin/activate
python src/main.py
```

Or search **ThermalCore** in your app launcher (after running `setup.sh`).

- Click **▼/►** arrows to expand/collapse hardware sections
- **Double-click** the Alert column to set a threshold per sensor
- Temperatures are color-coded: green (<50°C), yellow (50-70), orange (70-85), red (>85)
- **Export CSV** saves all recorded data
- CPU Power (RAPL): `setup.sh` configures persistent permissions (survives reboots)

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
│   │   ├── main_window.py     # 3-level tree view + per-metric alerts
│   │   └── styles.py          # Dark theme QSS
│   └── utils/
│       └── config.py
├── requirements.txt
├── pyproject.toml
├── setup.sh
└── thermalcore.desktop
```

## License

MIT License — Copyright (c) 2026 Vicen-te
