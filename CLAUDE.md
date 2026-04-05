# CLAUDE.md — Agent Instructions

> **IMPORTANT**: This file is your single source of truth.
> Read it ENTIRELY before doing anything.
> If you lose track, come back here.

---

## What is this project

A desktop application for Linux/Ubuntu that monitors CPU and GPU temperatures
in real time. Qt window with a dark theme, tree view, alerts, and CSV export.

---

## Rules you MUST always follow

1. **Commit + push after every completed step.** Follow `docs/COMMIT_STANDARDS.md`.
2. **All comments, docstrings, and variable names in English.** Follow `docs/CODING_STANDARDS.md`.
3. **Type hints on every function.**
4. **Run the code after every step** to verify it works. Never commit broken code.
5. **If something fails 3 times in a row**: commit with `WIP:` in the message, document the error in Known Issues (README.md), and move on.
6. **Never ask the user anything.** Make decisions yourself and keep going.
7. **If there is no GPU**, display "No GPU detected" gracefully. No crashes.
8. **If you are resuming a session**, read this file first, then `git log --oneline -10` to see where you are.

---

## Tech Stack

- Python 3.10+
- PySide6 (Qt6) for the GUI
- psutil for CPU data
- pynvml (nvidia-ml-py) for NVIDIA GPU data
- lm-sensors for hardware readings

---

## Project Structure

```
CorePulse/
├── README.md                    # Everything: install, usage, architecture, contributing
├── CLAUDE.md                    # This file (AI agent instructions)
├── requirements.txt
├── setup.sh                     # One-command installer
├── corepulse.sh               # Launcher script
├── corepulse.desktop          # Desktop integration
├── pyproject.toml
├── docs/
│   ├── CODING_STANDARDS.md      # How to write code
│   └── COMMIT_STANDARDS.md      # How to make commits
├── src/
│   ├── main.py                  # Entry point
│   ├── app.py                   # QApplication setup
│   ├── sensors/
│   │   ├── base_sensor.py       # Abstract base + SensorType enum
│   │   ├── cpu_sensor.py        # CPU temp, clock, load, power + shared cache
│   │   ├── gpu_sensor.py        # NVIDIA (pynvml) + AMD (sysfs)
│   │   ├── system_sensor.py     # Memory, storage, NVMe temps
│   │   └── poller.py            # Background QThread polling
│   ├── ui/
│   │   ├── main_window.py       # 3-level tree view + alerts
│   │   ├── icons.py             # App icon + tree branch arrows
│   │   ├── system_info.py       # Header bar system info
│   │   ├── theme_watcher.py     # DBus theme change listener
│   │   └── styles.py            # Auto dark/light theme (QSS)
│   └── utils/
│       ├── config.py            # Constants, palettes, theme detection
│       └── ipc.py               # Unix socket alert broadcaster
├── tests/
│   ├── test_sensors.py          # Sensor unit tests
│   ├── test_config.py           # Config/theme tests
│   └── benchmarks/              # Performance benchmarks
├── examples/
│   ├── alert_watcher.py         # CLI alert reactor
│   └── demo_app.py              # GUI auto-close on alert
└── assets/icons/
    └── corepulse.svg          # App icon
```

---

## Recovery Protocol

1. Run `git log --oneline -10` — check recent commits.
2. Run `python src/main.py` to see the current state.
3. Resume from whatever the user asks or the last unfinished work.
4. Keep working. Do not ask.
