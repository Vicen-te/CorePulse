# RESTRUCTURE.md — v2 Plan: HWMonitor-style UI + Performance

> This document defines the restructuring from v1 (custom widgets + charts)
> to v2 (CPUID HWMonitor-style tree view, no charts, optimized polling).

---

## Goal

Make ThermalCore look and behave like **CPUID HWMonitor**:

- A single **QTreeWidget** with expandable/collapsible sections
- Columns: **Sensor | Value | Min | Max**
- Sections grouped by hardware component (CPU, GPU, Disks, etc.)
- Each section is collapsible (click to expand/collapse)
- No charts, no sparklines, no card widgets
- Lightweight, fast, minimal CPU usage

---

## Performance Problems (v1)

| Problem | Impact | Fix |
|---------|--------|-----|
| `nvidia-smi` subprocess every 1s | 100-500ms blocking main thread | Use pynvml (NVML C library) |
| pyqtgraph chart rendering | 20-80ms per frame | Remove entirely |
| Sparkline custom paint × N sensors | 4-48ms per frame | Remove entirely |
| All polling on main thread | UI freezes during sensor read | Background QThread |
| Sensor data goes through widget layer | Unnecessary coupling | Direct data model |

---

## New Architecture

```
src/
├── main.py                  # Entry point (no change)
├── app.py                   # QApplication factory (simplified)
├── sensors/
│   ├── base_sensor.py       # Abstract base class (no change)
│   ├── cpu_sensor.py        # CPU reader (no change)
│   ├── gpu_sensor.py        # GPU reader (rewrite: pynvml instead of subprocess)
│   └── poller.py            # NEW: QThread that polls all sensors
├── ui/
│   ├── main_window.py       # Rewrite: QTreeWidget-based layout
│   ├── styles.py            # Simplified dark theme QSS
│   └── (removed)            # chart_widget.py, sensor_widget.py deleted
└── utils/
    └── config.py            # Updated constants
```

---

## Steps

### R1 — Rewrite GPU sensor (pynvml)

Replace subprocess calls to nvidia-smi with **pynvml** (Python bindings
for NVIDIA Management Library). Direct C library calls, <1ms per read.

- Add `pynvml` to requirements.txt (or `nvidia-ml-py`)
- Rewrite `NvidiaGpuSensor` to use `nvmlDeviceGetTemperature()`
- Initialize NVML once at startup, shutdown on exit
- Keep AMD sysfs reader as-is (already fast)

```
Commit: perf(gpu): replace nvidia-smi subprocess with pynvml
```

### R2 — Background sensor polling thread

Move all sensor reads off the main thread:

- Create `SensorPoller(QThread)` in `sensors/poller.py`
- Polls all sensors every POLL_INTERVAL_MS
- Emits a signal with `dict[str, SensorReading]` (name → value/min/max)
- Main thread only receives data and updates QTreeWidget items
- Zero blocking on the UI thread

```
Commit: perf(sensors): move polling to background QThread
```

### R3 — QTreeWidget-based main window (HWMonitor-style)

Complete rewrite of `main_window.py`:

- **QTreeWidget** with columns: Sensor | Value | Min | Max
- Top-level items = hardware groups (expandable):
  - "CPU — [model name]"
    - "Package" (overall CPU temp)
    - "Core 0", "Core 1", ... (per-core temps)
  - "GPU — [model name]" (or "No GPU detected")
    - "GPU Temperature"
  - "Disks" (NVMe sensors from psutil, if available)
    - "nvme0", "nvme1", ...
- Each leaf item shows: current value, min since launch, max since launch
- Monospace font for value columns
- Color-coded value column (green/yellow/orange/red)
- All sections expanded by default, user can collapse
- Header bar with system info (hostname, OS, CPU, GPU, uptime)
- No sidebar, no detail panel, no charts

Layout:
```
┌──────────────────────────────────────────────────┐
│ Host: ... | CPU: ... | GPU: ... | Uptime: ...    │
├──────────────────────────────────────────────────┤
│ Sensor              │ Value  │ Min    │ Max      │
├──────────────────────────────────────────────────┤
│ ▼ CPU — Intel i7    │        │        │          │
│   Package id 0      │ 45°C   │ 38°C   │ 67°C    │
│   Core 0            │ 42°C   │ 36°C   │ 65°C    │
│   Core 1            │ 44°C   │ 37°C   │ 66°C    │
│   ...               │        │        │          │
│ ▼ GPU — RTX 4070    │        │        │          │
│   GPU Temperature   │ 41°C   │ 38°C   │ 55°C    │
│ ▼ Disks             │        │        │          │
│   nvme0 Composite   │ 35°C   │ 33°C   │ 40°C    │
│   ...               │        │        │          │
└──────────────────────────────────────────────────┘
│ [Export CSV]        22 sensors | Alert: 85°C     │
└──────────────────────────────────────────────────┘
```

```
Commit: feat(ui): rewrite to HWMonitor-style tree view
```

### R4 — Remove dead code

- Delete `chart_widget.py`
- Delete `sensor_widget.py`
- Remove `pyqtgraph` from requirements.txt
- Clean up imports in `__init__.py`

```
Commit: refactor: remove chart and sensor widgets, drop pyqtgraph
```

### R5 — Re-add system tray, alerts, CSV export

Wire the existing features into the new tree-based window:

- System tray (minimize to tray, tooltip, context menu)
- Alerts (threshold spinbox, desktop notification, row highlight)
- CSV export (button in status bar area)

```
Commit: feat(ui): add system tray, alerts, and CSV export to tree view
```

### R6 — Update config, styles, README

- Simplify `styles.py` (QTreeWidget-focused QSS)
- Update `config.py` (remove chart constants, add tree constants)
- Update `README.md` (new screenshots description, remove chart mentions)
- Update `requirements.txt` (add pynvml, remove pyqtgraph)

```
Commit: docs: update config, styles, and README for v2
```

### R7 — Final verification and cleanup

- Run the app, verify:
  - Tree view with expandable sections
  - Values updating in real time
  - Min/Max tracking correctly
  - No UI stuttering
  - System tray works
  - CSV export works
  - Alerts work
- Run `pip check`
- Mark PROGRESS.md as COMPLETED

```
Commit: chore: mark v2 restructuring as completed
```

---

## Dependencies Change

### Remove
- `pyqtgraph>=0.13.3` (charts no longer needed)
- `numpy` (transitive dep of pyqtgraph)

### Add
- `nvidia-ml-py>=12.0` (pynvml — NVML bindings, replaces nvidia-smi subprocess)

### Keep
- `PySide6>=6.5` (Qt6 framework)
- `psutil>=5.9` (CPU temps, system info)

---

## Performance Target

| Metric | v1 | v2 Target |
|--------|-----|-----------|
| Poll cycle (main thread) | 150-750ms | <5ms |
| GPU temp read | 100-500ms (subprocess) | <1ms (pynvml) |
| UI update | 30-130ms (chart+sparklines) | <2ms (setText on tree items) |
| Memory (1h session) | ~50MB+ (growing log) | ~20MB (capped log) |
| CPU usage (idle) | 5-15% | <1% |
