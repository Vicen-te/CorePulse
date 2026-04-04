# ThermalCore — HW Monitor

A lightweight desktop application for Linux that monitors CPU, GPU, and disk temperatures in real time. Inspired by CPUID HWMonitor, featuring a tree view with expandable sections, dark theme, alerts, and CSV export.

## Features

- **HWMonitor-style tree view** with expandable/collapsible hardware sections
- **Columns**: Sensor | Value | Min | Max
- **Per-core CPU support** using psutil with sysfs fallback
- **NVIDIA GPU** support via pynvml (direct NVML library, no subprocess)
- **AMD GPU** support via sysfs hwmon
- **NVMe disk** temperature monitoring
- **Background polling** — sensor reads happen on a separate thread, zero UI blocking
- **Dark monitoring theme** with color-coded temperatures
- **System tray** — minimize to tray, tooltip with hottest temp
- **Temperature alerts** — configurable threshold with desktop notifications
- **CSV export** — save temperature log with timestamps
- **System info header** — hostname, CPU model, GPU model, uptime

## Requirements

- **Python** 3.10+
- **Linux** (tested on Ubuntu 22.04+)
- **lm-sensors** (for CPU temperature readings via psutil)
- **NVIDIA driver** (optional, for GPU monitoring via pynvml)

### System dependencies

```bash
sudo apt install lm-sensors libxcb-cursor0
sudo sensors-detect
```

## Installation

```bash
git clone https://github.com/Vicen-te/ThermalCore.git
cd ThermalCore/hw-monitor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Or use the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

## Usage

```bash
source .venv/bin/activate
python src/main.py
```

### Interface

```
┌──────────────────────────────────────────────────┐
│ Host: ... | CPU: ... | GPU: ... | Uptime: ...    │
├──────────────────────────────────────────────────┤
│ Sensor              │ Value  │ Min    │ Max      │
├──────────────────────────────────────────────────┤
│ ▼ CPU — Intel i7    │        │        │          │
│   Package id 0      │ 45°C   │ 38°C   │ 67°C    │
│   Core 0            │ 42°C   │ 36°C   │ 65°C    │
│   ...               │        │        │          │
│ ▼ GPU — RTX 4070    │        │        │          │
│   GPU Temperature   │ 41°C   │ 38°C   │ 55°C    │
│ ▼ Disks             │        │        │          │
│   NVMe Composite    │ 35°C   │ 33°C   │ 40°C    │
└──────────────────────────────────────────────────┘
│ Alert: [85°C]                      [Export CSV]  │
└──────────────────────────────────────────────────┘
```

- Click section headers to expand/collapse
- Temperatures are color-coded: green (<50°C), yellow (50-70), orange (70-85), red (>85)
- Closing the window minimizes to system tray
- Double-click tray icon to restore

## Troubleshooting

### No sensors detected

```bash
sudo apt install lm-sensors && sudo sensors-detect
python3 -c "import psutil; print(psutil.sensors_temperatures())"
```

### No GPU detected

The app shows "No GPU detected" gracefully. For NVIDIA, ensure the driver is installed (`nvidia-smi`).

### Qt platform plugin error

```bash
sudo apt install libxcb-cursor0
```

## Project structure

```
hw-monitor/
├── README.md
├── requirements.txt
├── pyproject.toml
├── .python-version
├── setup.sh
├── src/
│   ├── main.py
│   ├── app.py
│   ├── sensors/
│   │   ├── base_sensor.py
│   │   ├── cpu_sensor.py
│   │   ├── gpu_sensor.py
│   │   └── poller.py
│   ├── ui/
│   │   ├── main_window.py
│   │   └── styles.py
│   └── utils/
│       └── config.py
└── assets/
    └── icons/
```

## License

MIT License — Copyright (c) 2026 Vicen-te
