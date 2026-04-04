# CLAUDE.md — Agent Instructions

> **IMPORTANT**: This file is your single source of truth.
> Read it ENTIRELY before doing anything.
> If you lose track, come back here.
> If the session drops and you return, read this file and then `hw-monitor/PROGRESS.md`.

---

## What is this project

A desktop application for Linux/Ubuntu that monitors CPU and GPU temperatures
in real time, similar to CPUID HW Monitor on Windows. Qt window with a dark theme,
live charts, alerts, and CSV export.

---

## Rules you MUST always follow

1. **Work inside `hw-monitor/`**.
2. **Commit + push after every completed step.** Follow the conventions in `hw-monitor/CONVENTIONS.md`.
3. **Update `hw-monitor/PROGRESS.md`** after every commit. Mark the step as completed, update the status, and note the date.
4. **All comments, docstrings, and variable names in English.** Follow the commenting rules in `hw-monitor/CONVENTIONS.md`.
5. **Type hints on every function.**
6. **Run the code after every step** to verify it works. Never commit broken code.
7. **If something fails 3 times in a row**: commit with `WIP:` in the message, document the error in PROGRESS.md under "Known Issues", and move on to the next step.
8. **Never ask the user anything.** Make decisions yourself and keep going.
9. **If there is no GPU**, display "No GPU detected" gracefully. No crashes.
10. **If you are resuming a session**, the first thing you do is read this file and PROGRESS.md to find out where to pick up.

---

## Tech Stack

- Python 3.10+
- PySide6 (Qt6) for the GUI
- psutil for CPU data
- pyqtgraph for real-time charts
- lm-sensors / nvidia-smi for hardware readings

---

## Target Structure

```
hw-monitor/
├── PROGRESS.md
├── CONVENTIONS.md
├── README.md
├── requirements.txt
├── setup.sh
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── app.py               # QApplication setup
│   ├── sensors/
│   │   ├── __init__.py
│   │   ├── base_sensor.py   # Abstract base class
│   │   ├── cpu_sensor.py    # CPU temp reader
│   │   └── gpu_sensor.py    # GPU temp reader
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py   # Main window layout
│   │   ├── sensor_widget.py # Sensor card widget
│   │   ├── chart_widget.py  # Real-time chart
│   │   └── styles.py        # QSS dark theme
│   └── utils/
│       ├── __init__.py
│       └── config.py        # Constants and config
└── assets/
    └── icons/
```

---

## Build Steps

### Step 0 — Project Structure

Create the full folder structure and base files.

- `requirements.txt`: PySide6, psutil, pyqtgraph
- `setup.sh`: installs lm-sensors and pip dependencies
- `PROGRESS.md`: initial state with all steps pending

```
Commit: chore: initialize project structure and dependencies
```

### Step 1 — Sensor Readers

`base_sensor.py` — Abstract class `BaseSensor`:
- `get_temperature() -> float`
- `get_name() -> str`
- `is_available() -> bool`

`cpu_sensor.py`:
- Primary: `psutil.sensors_temperatures()`
- Fallback: `/sys/class/thermal/thermal_zone*/temp`
- Per-core support

`gpu_sensor.py`:
- NVIDIA: parse `nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader`
- AMD: read `/sys/class/drm/card*/device/hwmon/hwmon*/temp1_input`
- If no GPU, `is_available()` returns `False`

Verify by printing discovered sensors and their temperatures.

```
Commit: feat: implement CPU and GPU temperature sensor readers
```

### Step 2 — Main Window

Main window with PySide6:

- Dark theme:
  - Background: `#1a1a2e`
  - Panels: `#16213e`
  - Accent: `#0f3460`
  - Warning: `#e94560`
  - Text: `#eeeeee` / `#aaaaaa`
- Layout: left sidebar (sensor list) + right panel (details/charts)
- Minimum size: 800×600, resizable
- Monospace font for temperature values
- QSS stylesheet in `styles.py`

```
Commit: feat: create main window with dark monitoring theme
```

### Step 3 — Sensor Widgets

`sensor_widget.py` — Card widget per sensor:

- Sensor name
- Current temperature in large text ("62°C")
- Min / Max / Avg since launch
- Color indicator: green (<50°C), yellow (50–70), orange (70–85), red (>85)
- Sparkline showing recent trend

Wire sensors to widgets with `QTimer` (poll every 1–2 seconds).

```
Commit: feat: add sensor display widgets with live temperature updates
```

### Step 4 — Real-Time Charts

`chart_widget.py` with pyqtgraph:

- Scrolling line chart with last 60–120 seconds of data
- One line per sensor with legend
- Dark background matching the theme
- Anti-aliased smooth lines
- Y-axis: Temperature (°C), X-axis: Time
- Clicking a sensor in the sidebar highlights its chart line

```
Commit: feat: add real-time temperature chart with scrolling history
```

### Step 5 — Extra Features

- **System tray**: minimize to tray, tooltip with hottest temp, context menu
- **Alerts**: configurable threshold (default 85°C), desktop notification, visual pulse on widget
- **Export**: button to save temperature log as CSV with timestamps
- **Header**: hostname, OS, kernel, CPU model, GPU model, uptime

```
Commit: feat: add system tray, alerts, data export, and system info
```

### Step 6 — Documentation

Complete `README.md`:

- Description and features
- Requirements (Python, Ubuntu, lm-sensors)
- Step-by-step installation
- Usage
- Troubleshooting
- MIT License

```
Commit: docs: add comprehensive README with install and usage guide
```

### Step 7 — Packaging

- `pyproject.toml` for pip install
- `.desktop` file for Linux launcher
- App icon (SVG or PNG)
- Optional: AppImage config

```
Commit: chore: add packaging config and desktop integration
```

---

## Recovery Protocol

If you are reading this at the start of a session and the project already has work done:

1. Read `hw-monitor/PROGRESS.md` — it tells you which step you are on.
2. Run `git log --oneline -10` — check the latest commits.
3. Run the current code (`python hw-monitor/src/main.py`) to see its state.
4. Resume from the step marked as "In Progress" or the first uncompleted one.
5. Keep working. Do not ask.

---

## Emergency Protocol (repeated failures)

If you have failed 3 times on the same error:

1. `git add -A && git commit -m "WIP: [current step] - blocked by [error description]"`
2. `git push`
3. Document in PROGRESS.md under "Known Issues":
   - Which step
   - Exact error message
   - What you tried
4. Move on to the next step.

---

## Final Verification

When ALL steps are done:

1. Run `python hw-monitor/src/main.py` and verify:
   - Window opens without errors
   - Sensors detected and showing data
   - Widgets updating
   - Chart working
   - CSV export functional
   - System tray functional
2. Run `pip check` for dependencies.
3. Mark PROGRESS.md status as `COMPLETED`.
4. Commit: `chore: mark project as completed`
5. Final push.