# RESTRUCTURE.md — v2.1 LibreHardwareMonitor-style

---

## Architecture

### 3-Level Tree Hierarchy

```
Hardware Group (bold, with model name)
├── Sensor Type Group (italic, e.g. "Temperatures", "Clocks")
│   ├── Individual Sensor    │ Value   │ Min     │ Max
│   └── Individual Sensor    │ Value   │ Min     │ Max
└── Sensor Type Group
    └── ...
```

### Example Tree

```
CPU — 13th Gen Intel Core i7-13700K
├── Temperatures
│   ├── Package id 0          45.0°C     38.0°C     72.0°C
│   ├── Core 0                42.0°C     36.0°C     68.0°C
│   ├── Core 1                43.0°C     37.0°C     70.0°C
│   └── ...
├── Clocks
│   └── CPU Clock             4200 MHz   800 MHz    5000 MHz
├── Load
│   ├── CPU Total             12.3 %     0.0 %      98.5 %
│   ├── Core #0               8.2 %      0.0 %      100.0 %
│   └── ...
└── Power
    └── CPU Package            28.5 W     5.2 W      125.0 W

GPU — NVIDIA GeForce RTX 4070 Ti SUPER
├── Temperatures
│   └── GPU Core              41.0°C     38.0°C     78.0°C
├── Clocks
│   ├── GPU Core              210 MHz    210 MHz    2745 MHz
│   └── GPU Memory            405 MHz    405 MHz    10501 MHz
├── Load
│   ├── GPU Core              5.0 %      0.0 %      99.0 %
│   └── Memory Controller     8.0 %      0.0 %      95.0 %
├── Data
│   ├── VRAM Used             1.6 GB     0.5 GB     12.0 GB
│   └── VRAM Total            16.0 GB    16.0 GB    16.0 GB
├── Power
│   └── GPU Power             15.8 W     12.0 W     280.0 W
└── Fans
    └── GPU Fan               0 %        0 %        75 %

Memory — 32 GB
├── Load
│   └── Memory                31.1 %     28.0 %     85.0 %
└── Data
    ├── Memory Used           10.2 GB    9.1 GB     27.5 GB
    └── Memory Available      22.8 GB    5.5 GB     23.9 GB

Storage
├── Temperatures
│   ├── Composite             30.9°C     28.0°C     42.0°C
│   ├── Sensor 1              30.9°C     28.0°C     42.0°C
│   └── ...
├── Load
│   └── Usage (/)             9.7 %      9.7 %      9.8 %
└── Data
    ├── Used Space (/)        44.4 GB    44.4 GB    44.5 GB
    └── Free Space (/)        411.9 GB   411.8 GB   411.9 GB
```

---

## Sensor Types Supported

| Type | Format | Unit | Sources |
|------|--------|------|---------|
| Temperature | `{:.1f}` | °C | psutil, pynvml, sysfs |
| Clock | `{:.0f}` | MHz | psutil.cpu_freq(), pynvml |
| Load | `{:.1f}` | % | psutil.cpu_percent(), pynvml |
| Power | `{:.1f}` | W | Intel RAPL (sysfs), pynvml |
| Fan | `{:.0f}` | % | pynvml |
| Data | `{:.1f}` | GB | psutil, pynvml |

---

## Files Changed (vs v1)

| File | Change |
|------|--------|
| `sensors/base_sensor.py` | Added SensorType enum, format_value(), type/group methods |
| `sensors/cpu_sensor.py` | Added CpuClockSensor, CpuTotalLoadSensor, CpuCoreLoadSensor, CpuPowerSensor |
| `sensors/gpu_sensor.py` | Added NVIDIA clock, load, VRAM, power, fan sensors via pynvml |
| `sensors/system_sensor.py` | **NEW** — Memory and storage sensors |
| `sensors/poller.py` | Updated for multi-type sensors with proper key generation |
| `ui/main_window.py` | 3-level tree population, per-type formatting |
| `ui/chart_widget.py` | **DELETED** |
| `ui/sensor_widget.py` | **DELETED** |
| `requirements.txt` | Replaced pyqtgraph with nvidia-ml-py |

---

## Performance

| Metric | v1 | v2.1 |
|--------|-----|------|
| Poll cycle (main thread) | 150-750ms | 0ms (background thread) |
| GPU temp read | 100-500ms (subprocess) | <0.01ms (pynvml) |
| UI update | 30-130ms (chart+sparklines) | <3ms (setText on items) |
| Startup | ~2s | ~0.5s |
