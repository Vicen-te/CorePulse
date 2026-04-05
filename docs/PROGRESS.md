# Project Progress

## Status: COMPLETED
## Last Commit: refactor: extract UI modules, add tests and benchmarks
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

### v2 — Tree view with background polling (completed 2026-04-04)

- [x] R1: Replace nvidia-smi subprocess with pynvml (<0.01ms reads)
- [x] R2: Background QThread for sensor polling (zero UI blocking)
- [x] R3: QTreeWidget with expandable sections, Sensor/Value/Min/Max columns
- [x] R4: Remove pyqtgraph, charts, sparklines, sensor card widgets
- [x] R5: System tray, alerts, CSV export in new UI
- [x] R6: Update config, styles, README, requirements

---

### v2.1 — 3-level tree with multi-sensor support (completed 2026-04-04)

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
- [x] Storage redesign: removed Load/Data, added Usage section (free/total GB)
- [x] Filtered snap/squashfs/tmpfs mounts from storage sensors

### v2.3 — Structure & Cleanup (completed 2026-04-05)

- [x] Flatten hw-monitor/ into project root (no nested project)
- [x] Clean all third-party product name references from code and docs

### v2.4 — UX & Sensor Fixes (completed 2026-04-05)

- [x] Fix GPU detection: use system Python (pyenv ctypes broken, pynvml failed)
- [x] Fix window behavior: close button now quits normally (no forced tray-only mode)
- [x] Auto-hide sensors with no data after 3 poll cycles (and empty type groups)
- [x] Show free space instead of used space in Storage > Usage
- [x] Add visible expand/collapse arrow icons to tree nodes
- [x] GPU Power now working (30+ W on RTX 4070 Ti SUPER)

### v2.5 — Per-Metric Alerts & Desktop Integration (completed 2026-04-05)

- [x] Per-metric alerts: new Alert column, double-click to set threshold per sensor
- [x] Desktop notification when any sensor exceeds its configured threshold
- [x] Removed global alert spinbox (replaced by per-sensor config)
- [x] GPU Fan sensor type changed from LOAD to FAN (0% displayed correctly for idle fans)
- [x] Min/Max tracking now works for LOAD/FAN sensors at 0 values
- [x] Desktop integration: .desktop file installs to ~/.local/share/applications/
- [x] setup.sh installs desktop launcher automatically
- [x] Fixed README screenshot layout alignment with Alert column

### v2.6 — Physical Core Mapping & CPU Power (completed 2026-04-05)

- [x] Load cores now match temperature core labels (Core 0, Core 4, Core 8...)
- [x] P-cores with HT average both thread loads into one reading
- [x] Physical core → logical CPU mapping read from /proc/cpuinfo
- [x] CPU Power section always visible (shows 0.0 W without root)

### v2.7 — Auto Dark/Light Theme (completed 2026-04-05)

- [x] Auto-detect system theme (GNOME gsettings: color-scheme and gtk-theme)
- [x] Light theme colors for light system preference
- [x] Defaults to dark if detection fails
- [x] Live theme switching via DBus signal watcher (no polling)

### v2.8 — Persistent Setup (completed 2026-04-05)

- [x] RAPL permissions persist across reboots via udev rule (99-thermalcore-rapl.rules)
- [x] setup.sh is run-once: detects if already configured

### v2.9 — Ubuntu Theme & Desktop Integration Fix (completed 2026-04-05)

- [x] Dark/light palettes updated to Ubuntu colors (orange #e95420, grey tones)
- [x] App icon redesigned: thermometer on rounded square (Ubuntu style), replaces old red ring/green circle
- [x] Icon loads from SVG asset instead of programmatic drawing
- [x] Desktop file fixed: invalid Exec with unescaped chars replaced by launcher script (thermalcore.sh)
- [x] Desktop file validated (desktop-file-validate passes)
- [x] StartupWMClass=thermalcore added for GNOME dock matching
- [x] setDesktopFileName("thermalcore") added for Wayland/X11 integration
- [x] Icon installed to ~/.local/share/icons/hicolor/scalable/apps/ for proper GNOME discovery
- [x] setup.sh updated to install icon to standard XDG location

### v3.0 — Refactoring, Tests & Benchmarks (completed 2026-04-05)

- [x] Extract ThemeWatcher from main_window.py into ui/theme_watcher.py
- [x] Extract icon creation into ui/icons.py
- [x] Extract system info gathering into ui/system_info.py
- [x] main_window.py reduced from 760 to 580 lines (pure UI logic)
- [x] Move documentation to docs/ folder (INSTALL, DEVELOPMENT, CONVENTIONS, PROGRESS)
- [x] 41 unit tests: sensor interface, format values, CPU/GPU/memory/storage, config/palettes
- [x] 3 performance benchmarks: per-sensor reads, poll cycle overhead, startup time
- [x] All 41 tests passing, app startup in 0.4s, ~50MB memory

### Known Issues

- CPU Fan RPM: not available on this board (no nct6775/it87 sensor chip loaded). Only ACPI on/off state exposed.
- RAM Temperature: not available (no DIMM/SPD temp sensors on this motherboard).
- GPU Fan shows 0% when GPU is idle — correct behavior (0-RPM fan mode). Fans spin up under load.
