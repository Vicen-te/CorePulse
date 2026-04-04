# CLAUDE.md — Agent Instructions

> **IMPORTANT**: This file is your single source of truth.
> Read it ENTIRELY before doing anything.
> If you lose track, come back here.
> If the session drops and you return, read this file and then `PROGRESS.md`.

---

## What is this project

A desktop application for Linux/Ubuntu that monitors CPU and GPU temperatures
in real time. Qt window with a dark theme, tree view, alerts, and CSV export.

---

## Rules you MUST always follow

1. **Commit + push after every completed step.** Follow the conventions in `CONVENTIONS.md`.
2. **Update `PROGRESS.md`** after every commit. Mark the step as completed, update the status, and note the date.
3. **All comments, docstrings, and variable names in English.** Follow the commenting rules in `CONVENTIONS.md`.
4. **Type hints on every function.**
5. **Run the code after every step** to verify it works. Never commit broken code.
6. **If something fails 3 times in a row**: commit with `WIP:` in the message, document the error in PROGRESS.md under "Known Issues", and move on to the next step.
7. **Never ask the user anything.** Make decisions yourself and keep going.
8. **If there is no GPU**, display "No GPU detected" gracefully. No crashes.
9. **If you are resuming a session**, the first thing you do is read this file and PROGRESS.md to find out where to pick up.

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
ThermalCore/
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
│   │   ├── base_sensor.py   # Abstract base class + SensorType enum
│   │   ├── cpu_sensor.py    # CPU temp, clock, load, power
│   │   ├── gpu_sensor.py    # NVIDIA (pynvml) + AMD (sysfs)
│   │   ├── system_sensor.py # Memory, storage, NVMe temps
│   │   └── poller.py        # Background QThread polling
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py   # 3-level tree view
│   │   └── styles.py        # QSS dark theme
│   └── utils/
│       ├── __init__.py
│       └── config.py        # Constants and config
└── assets/
    └── icons/
```

---

## Recovery Protocol

If you are reading this at the start of a session and the project already has work done:

1. Read `PROGRESS.md` — it tells you which step you are on.
2. Run `git log --oneline -10` — check the latest commits.
3. Run the current code (`python src/main.py`) to see its state.
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

1. Run `python src/main.py` and verify:
   - Window opens without errors
   - Sensors detected and showing data
   - Tree view updating
   - CSV export functional
   - System tray functional
2. Run `pip check` for dependencies.
3. Mark PROGRESS.md status as `COMPLETED`.
4. Commit: `chore: mark project as completed`
5. Final push.
