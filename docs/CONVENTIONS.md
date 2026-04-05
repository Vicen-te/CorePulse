# CONVENTIONS.md — Code & Commit Standards

> This document defines how to write comments, name things, and make commits.
> Follow these rules in every file, every function, and every commit.

---

## 1. Commit Convention — Conventional Commits

Every commit message follows this format:

```
<type>(<scope>): <short description>
```

### Types

| Type       | When to use                                         | Example                                                    |
|------------|-----------------------------------------------------|------------------------------------------------------------|
| `feat`     | New feature or functionality                        | `feat(sensors): implement CPU temperature reader`          |
| `fix`      | Bug fix                                             | `fix(gpu): handle missing nvidia-smi gracefully`           |
| `chore`    | Maintenance, config, dependencies, no logic change  | `chore: add pyqtgraph to requirements.txt`                 |
| `docs`     | Documentation only                                  | `docs: add installation instructions to README`            |
| `style`    | Code formatting, whitespace, no logic change        | `style(ui): fix indentation in main_window.py`             |
| `refactor` | Code restructuring without changing behavior        | `refactor(sensors): extract common logic to base class`    |
| `test`     | Adding or updating tests                            | `test(cpu): add unit tests for fallback sensor reading`    |
| `perf`     | Performance improvement                             | `perf(chart): reduce redraw frequency to lower CPU usage`  |
| `WIP`      | Work in progress (blocked by error, moving on)      | `WIP(chart): scrolling chart — blocked by pyqtgraph issue` |

### Scope

The scope is optional but recommended. Use the module or area being changed:

- `sensors`, `cpu`, `gpu` — sensor layer
- `ui`, `window`, `widget`, `chart` — UI layer
- `config`, `utils` — utilities
- `docs` — documentation
- `deps` — dependencies

### Rules

- **Subject line**: lowercase, imperative mood, no period at the end, max 72 characters.
- **Body** (optional): explain *why*, not *what*. Separate from subject with a blank line.
- **Breaking changes**: add `BREAKING CHANGE:` in the body if applicable.

### Examples

```
feat(sensors): implement CPU temperature reader

Use psutil as the primary source. Falls back to reading
/sys/class/thermal/thermal_zone*/temp when psutil returns empty.
Supports per-core temperature readings.
```

```
fix(gpu): return None instead of crashing when nvidia-smi is not installed
```

```
WIP(chart): real-time chart rendering — blocked by pyqtgraph import error

Attempted:
1. pip install pyqtgraph — version conflict with PySide6
2. pip install pyqtgraph==0.13.3 — same error
3. Tried matplotlib as fallback — rendering too slow

Documented in PROGRESS.md. Moving to Step 5.
```

---

## 2. Code Comments — Rules

### Language

All comments in **English**. No exceptions.

### Comment Types

#### 2.1 Module Docstring (top of every file)

Every `.py` file starts with a module docstring explaining its purpose:

```python
"""
CPU temperature sensor reader.

Reads CPU core temperatures using psutil as the primary source,
with a fallback to sysfs thermal zones. Supports per-core readings
on multi-core systems.
"""
```

#### 2.2 Class Docstring

Every class gets a docstring right after the class definition:

```python
class CpuSensor(BaseSensor):
    """
    Reads CPU temperature data from the system.

    Uses psutil.sensors_temperatures() as the primary method.
    Falls back to reading /sys/class/thermal/thermal_zone*/temp
    if psutil returns no data.

    Attributes:
        cores: List of detected CPU cores with temperature data.
        poll_interval: Time in seconds between readings.
    """
```

#### 2.3 Function/Method Docstring

Every function and method gets a docstring. Use Google style:

```python
def get_temperature(self) -> float:
    """
    Return the current CPU temperature in Celsius.

    Reads from all available cores and returns the highest
    temperature found. Returns 0.0 if no sensors are available.

    Returns:
        The highest core temperature in degrees Celsius.

    Raises:
        SensorReadError: If the sensor file exists but cannot be read.
    """
```

For simple one-liner functions, a single-line docstring is fine:

```python
def get_name(self) -> str:
    """Return the human-readable sensor name."""
    return self._name
```

#### 2.4 Inline Comments

Use inline comments to explain **why**, not **what**:

```python
# BAD — describes what the code does (obvious from reading it)
temperature = value / 1000  # divide by 1000

# GOOD — explains why
temperature = value / 1000  # sysfs reports millidegrees, convert to Celsius
```

```python
# BAD
if temp > 85:  # check if temp is greater than 85

# GOOD
if temp > 85:  # thermal throttling threshold for most CPUs
```

#### 2.5 Section Comments

Use section comments to separate logical blocks inside long functions:

```python
def setup_ui(self) -> None:
    """Initialize the main window layout and widgets."""

    # --- Sidebar: sensor list ---
    self.sidebar = QListWidget()
    self.sidebar.setMaximumWidth(250)

    # --- Main panel: charts and details ---
    self.main_panel = QWidget()
    self.chart = ChartWidget()

    # --- Status bar ---
    self.status = QStatusBar()
    self.status.showMessage("Monitoring...")
```

#### 2.6 TODO / FIXME / HACK

Use these markers for issues that need attention later:

```python
# TODO: Add support for AMD GPU sensors via ROCm-SMI
# FIXME: This polling interval causes high CPU usage on single-core systems
# HACK: nvidia-smi sometimes returns empty string on first call, retry once
```

---

## 3. Naming Conventions

### Files and Modules

- `snake_case.py` — all lowercase, underscores
- Name describes the content: `cpu_sensor.py`, `main_window.py`, `chart_widget.py`

### Classes

- `PascalCase` — capitalize each word, no underscores
- `CpuSensor`, `MainWindow`, `ChartWidget`, `BaseSensor`

### Functions and Methods

- `snake_case` — all lowercase, underscores
- Verb first: `get_temperature()`, `update_chart()`, `is_available()`
- Boolean methods start with `is_`, `has_`, `can_`: `is_available()`, `has_gpu()`

### Variables

- `snake_case` — all lowercase, underscores
- Descriptive: `cpu_temperature`, `max_temp`, `sensor_list`
- Avoid single letters except in loops: `for i in range(cores)`

### Constants

- `UPPER_SNAKE_CASE` — all uppercase, underscores
- `MAX_TEMPERATURE_THRESHOLD = 85`
- `POLL_INTERVAL_MS = 1000`
- `DEFAULT_WINDOW_WIDTH = 800`

### Private Members

- Prefix with single underscore: `self._temperature`, `self._poll_timer`
- Double underscore only for name mangling when truly needed (rare)

---

## 4. Code Structure Rules

### Imports Order

Follow PEP 8 import ordering, separated by blank lines:

```python
# 1. Standard library
import os
import sys
from pathlib import Path
from abc import ABC, abstractmethod

# 2. Third-party packages
from PySide6.QtWidgets import QMainWindow, QWidget
from PySide6.QtCore import QTimer
import psutil

# 3. Local project imports
from sensors.base_sensor import BaseSensor
from utils.config import POLL_INTERVAL_MS
```

### Type Hints

Every function signature must have type hints:

```python
def get_temperature(self) -> float: ...
def is_available(self) -> bool: ...
def update_sensor(self, sensor_id: str, value: float) -> None: ...
def discover_sensors(self) -> list[BaseSensor]: ...
```

### Error Handling

Always catch specific exceptions. Log or document why:

```python
try:
    output = subprocess.check_output(["nvidia-smi", ...])
except FileNotFoundError:
    # nvidia-smi not installed — GPU monitoring unavailable
    self._available = False
except subprocess.CalledProcessError as e:
    # nvidia-smi crashed — driver issue, disable GPU sensor
    logger.warning("nvidia-smi failed: %s", e)
    self._available = False
```

### Magic Numbers

No magic numbers in code. Use named constants from `config.py`:

```python
# BAD
if temp > 85:
    self.set_color("red")
time.sleep(2)

# GOOD
if temp > CRITICAL_TEMP_THRESHOLD:
    self.set_color(COLOR_CRITICAL)
time.sleep(POLL_INTERVAL_SEC)
```

---

## 5. File Template

Every new Python file should follow this template:

```python
"""
Brief description of what this module does.

More detailed explanation if needed, covering the main purpose,
dependencies, and any important design decisions.
"""

# Standard library
import os

# Third-party
from PySide6.QtWidgets import QWidget

# Local
from utils.config import SOME_CONSTANT


class MyClass:
    """
    One-line summary of the class.

    Detailed description covering purpose, usage, and any
    important attributes or behavior.

    Attributes:
        name: Description of the attribute.
    """

    def __init__(self, name: str) -> None:
        """Initialize MyClass with the given name."""
        self._name = name

    def my_method(self) -> str:
        """Return something useful."""
        return self._name
```

---

## Quick Reference

| Element             | Convention          | Example                                   |
|---------------------|---------------------|--------------------------------------------|
| File names          | `snake_case.py`     | `cpu_sensor.py`                            |
| Classes             | `PascalCase`        | `CpuSensor`                               |
| Functions/methods   | `snake_case`        | `get_temperature()`                        |
| Variables           | `snake_case`        | `cpu_temp`                                 |
| Constants           | `UPPER_SNAKE_CASE`  | `MAX_TEMP_THRESHOLD`                       |
| Private members     | `_prefix`           | `self._timer`                              |
| Commits             | `type(scope): msg`  | `feat(sensors): add CPU reader`            |
| Comments            | English, explain *why* | `# sysfs reports millidegrees`          |
| Docstrings          | Google style        | `"""Return the current temperature."""`    |