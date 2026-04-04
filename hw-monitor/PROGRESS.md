# Project Progress

## Status: IN PROGRESS — v2 Restructuring
## Last Commit: chore: add .python-version for pyenv (3.12.12)
## Last Updated: 2026-04-04

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

### v2 Restructuring — HWMonitor-style UI + Performance

#### Completed

_(none)_

#### In Progress

- [ ] R1: Rewrite GPU sensor to avoid subprocess per poll

#### Pending

- [ ] R2: Move sensor polling to a background thread
- [ ] R3: Replace entire UI with QTreeWidget (HWMonitor-style)
- [ ] R4: Remove pyqtgraph, chart_widget, sensor_widget, sparklines
- [ ] R5: Add system tray, alerts, CSV export to new UI
- [ ] R6: Update config, styles, README
- [ ] R7: Final verification and cleanup

### Known Issues

- nvidia-smi subprocess blocks UI thread ~100-500ms every poll cycle
- pyqtgraph + sparklines cause unnecessary rendering overhead
- UI does not resemble CPUID HWMonitor (tree view with expandable sections)
