# ThermalCore — HW Monitor

A desktop application for Linux that monitors CPU and GPU temperatures in real time. Built with PySide6 (Qt6) and pyqtgraph, featuring a dark theme, live charts, configurable alerts, system tray integration, and CSV data export.

## Features

- **Real-time temperature monitoring** for CPU cores and GPU
- **Per-core CPU support** using psutil with sysfs fallback
- **NVIDIA and AMD GPU** support (nvidia-smi / sysfs hwmon)
- **Dark monitoring theme** with color-coded temperature indicators
- **Scrolling line chart** with 120-second history
- **Sensor card widgets** with sparklines and min/max/avg stats
- **System tray** — minimize to tray, tooltip with hottest temp, context menu
- **Temperature alerts** — configurable threshold, desktop notifications, visual pulse
- **CSV export** — save temperature log with timestamps
- **System info header** — hostname, OS, kernel, CPU/GPU model, uptime

## Requirements

- **Python** 3.10+
- **Linux** (tested on Ubuntu 22.04+)
- **lm-sensors** (for CPU temperature readings via psutil)
- **nvidia-smi** (optional, for NVIDIA GPU monitoring)

### System dependencies

```bash
sudo apt install lm-sensors libxcb-cursor0
sudo sensors-detect   # follow prompts to detect sensors
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Vicen-te/ThermalCore.git
cd ThermalCore/hw-monitor
```

### 2. Create a virtual environment and install dependencies

Using the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the application

```bash
source .venv/bin/activate
python src/main.py
```

## Usage

### Main interface

- **Left sidebar** — scrollable list of sensor cards showing current temperature, min/max/avg, and sparkline
- **Right panel** — detailed view of the selected sensor with large temperature display and real-time chart
- **Header bar** — system information (hostname, OS, CPU, GPU, uptime)

### Sensor selection

Click any sensor card in the sidebar to:
- View its detailed temperature in the right panel
- Highlight its line in the chart (other lines dim)

### Temperature alerts

- Adjust the alert threshold using the spinbox (default: 85°C)
- When any sensor exceeds the threshold:
  - Desktop notification appears
  - Temperature display pulses red
  - Notification clears when temperature drops below threshold

### CSV export

Click **Export CSV** to save all recorded temperature data with timestamps to a CSV file.

### System tray

- Closing the window minimizes to the system tray
- Tray tooltip shows the hottest sensor and its temperature
- Double-click the tray icon to restore the window
- Right-click for context menu (Show / Quit)

## Troubleshooting

### No sensors detected

1. Ensure lm-sensors is installed and configured:
   ```bash
   sudo apt install lm-sensors
   sudo sensors-detect
   sensors  # verify output
   ```

2. Check that psutil can read sensors:
   ```bash
   python3 -c "import psutil; print(psutil.sensors_temperatures())"
   ```

### No GPU detected

- **NVIDIA**: Ensure nvidia-smi is installed and the NVIDIA driver is loaded
  ```bash
  nvidia-smi
  ```
- **AMD**: Check sysfs hwmon paths exist:
  ```bash
  ls /sys/class/drm/card*/device/hwmon/hwmon*/temp1_input
  ```
- If no GPU is present, the app shows "No GPU detected" gracefully

### Qt platform plugin error

If you see `Could not load the Qt platform plugin "xcb"`:

```bash
sudo apt install libxcb-cursor0
```

### High CPU usage

The default polling interval is 1 second. If this causes issues on low-power systems, you can adjust `POLL_INTERVAL_MS` in `src/utils/config.py`.

## Project structure

```
hw-monitor/
├── README.md
├── CONVENTIONS.md
├── PROGRESS.md
├── requirements.txt
├── setup.sh
├── pyproject.toml
├── src/
│   ├── main.py              # Entry point
│   ├── app.py               # QApplication setup
│   ├── sensors/
│   │   ├── base_sensor.py   # Abstract base class
│   │   ├── cpu_sensor.py    # CPU temp reader
│   │   └── gpu_sensor.py    # GPU temp reader
│   ├── ui/
│   │   ├── main_window.py   # Main window layout
│   │   ├── sensor_widget.py # Sensor card widget
│   │   ├── chart_widget.py  # Real-time chart
│   │   └── styles.py        # QSS dark theme
│   └── utils/
│       └── config.py        # Constants and config
└── assets/
    └── icons/
```

## License

MIT License

Copyright (c) 2026 Vicen-te

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
