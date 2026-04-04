# Project Progress

## Status: COMPLETED
## Last Commit: fix: CPU load cache, GPU detection, NVMe keys, storage redesign
## Last Updated: 2026-04-05

---

### v1 (completed 2026-04-04)

- [x] Step 0: Project structure and dependencies
- [x] Step 1: CPU and GPU sensor readers
- [x] Step 2: Main window with dark theme
- [x] Step 3: Sensor display widgets with live updates
- [x] Step 4: Real-time temperature charts
- [x] Step 5: System tray, alerts, CSV export, system info
- [x] Step 6: README and documentation
- [x] Step 7: Packaging and desktop integration

---

### v2 Restructuring — HWMonitor-style (completed 2026-04-04)

- [x] R1: Replace nvidia-smi subprocess with pynvml (<0.01ms reads)
- [x] R2: Background QThread for sensor polling (zero UI blocking)
- [x] R3: QTreeWidget with expandable sections, Sensor/Value/Min/Max columns
- [x] R4: Remove pyqtgraph, charts, sparklines, sensor card widgets
- [x] R5: System tray, alerts, CSV export in new UI
- [x] R6: Update config, styles, README, requirements

---

### v2.1 — LibreHardwareMonitor-style (completed 2026-04-04)

- [x] 3-level tree hierarchy: Hardware → Sensor Type → Individual Sensor
- [x] Multi-sensor types: Temperature, Clock, Load, Power, Fan, Data
- [x] NVIDIA GPU: temp, clocks, load, VRAM, power, fan via pynvml
- [x] CPU: per-core temps, clock speed, per-core load, RAPL power
- [x] Memory: used/available/load
- [x] Storage: NVMe temps, disk usage per partition
- [x] Proper value formatting per sensor type (°C, MHz, %, W, GB, RPM)
- [x] Hardware group headers with model names (CPU — Intel..., GPU — RTX...)
- [x] Type groups (Temperatures, Clocks, Load, Power, etc.) as sub-nodes

### v2.2 — Bugfixes & Storage Redesign (completed 2026-04-05)

- [x] Fix CPU load: cores 1+ now show correct values (shared poll cache)
- [x] Fix GPU header: NVML initialized before querying GPU name
- [x] Fix NVMe temps: duplicate sensor names resolved with drive numbers
- [x] Storage redesign: removed Load/Data, added Usage section (used/total, available/total GB)
- [x] Filtered snap/squashfs/tmpfs mounts from storage sensors

### Known Issues

_(none)_
