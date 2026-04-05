# Coding Standards

Rules for writing code in this project. Aimed at AI agents and contributors.

## Language

All code, comments, docstrings, and variable names in **English**.

## Naming

| Element | Convention | Example |
|---|---|---|
| Files | `snake_case.py` | `cpu_sensor.py` |
| Classes | `PascalCase` | `CpuSensor`, `MainWindow` |
| Functions/methods | `snake_case` | `get_temperature()`, `is_available()` |
| Variables | `snake_case` | `cpu_temp`, `sensor_list` |
| Constants | `UPPER_SNAKE_CASE` | `POLL_INTERVAL_MS`, `COLOR_PANEL` |
| Private members | `_prefix` | `self._timer`, `self._running` |
| Booleans | `is_`/`has_`/`can_` prefix | `is_available()`, `has_gpu()` |

## Type Hints

Every function signature must have type hints:

```python
def get_temperature(self) -> float: ...
def discover_sensors(self) -> list[BaseSensor]: ...
def update_sensor(self, sensor_id: str, value: float) -> None: ...
```

## Imports

PEP 8 order, separated by blank lines:

```python
# Standard library
import os
import sys

# Third-party
from PySide6.QtWidgets import QMainWindow
import psutil

# Local
from sensors.base_sensor import BaseSensor
from utils.config import POLL_INTERVAL_MS
```

## Docstrings

Google style. Every file, class, and function gets one.

```python
"""
CPU temperature sensor reader.

Reads CPU core temperatures using psutil, with a fallback
to sysfs thermal zones.
"""
```

Simple methods use a single-line docstring:

```python
def get_name(self) -> str:
    """Return the human-readable sensor name."""
    return self._name
```

## Comments

Explain **why**, not **what**:

```python
# BAD
temperature = value / 1000  # divide by 1000

# GOOD
temperature = value / 1000  # sysfs reports millidegrees, convert to Celsius
```

Use `# --- Section ---` to separate logical blocks in long functions.
Use `# TODO:`, `# FIXME:`, `# HACK:` for issues needing attention.

## Error Handling

Catch specific exceptions. Document why:

```python
try:
    output = subprocess.check_output(["nvidia-smi", ...])
except FileNotFoundError:
    # nvidia-smi not installed — GPU monitoring unavailable
    self._available = False
```

## Constants

No magic numbers. Use named constants from `config.py`:

```python
# BAD
if temp > 85:

# GOOD
if temp > CRITICAL_TEMP_THRESHOLD:
```

## File Template

```python
"""
Brief description of what this module does.

More detail if needed.
"""

# Standard library
import os

# Third-party
from PySide6.QtWidgets import QWidget

# Local
from utils.config import SOME_CONSTANT


class MyClass:
    """One-line summary."""

    def __init__(self, name: str) -> None:
        """Initialize MyClass with the given name."""
        self._name = name

    def my_method(self) -> str:
        """Return something useful."""
        return self._name
```
