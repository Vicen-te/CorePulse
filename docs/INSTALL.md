# Installation Guide

Step-by-step guide to install ThermalCore on any Linux system (tested on Ubuntu 24.04).

---

## Prerequisites

- **Linux** with a desktop environment (GNOME recommended)
- **Python 3.10** or higher
- **lm-sensors** for CPU temperature readings
- **NVIDIA driver** (optional, only needed for NVIDIA GPU monitoring)

---

## Quick Install

```bash
git clone https://github.com/Vicen-te/ThermalCore.git
cd ThermalCore
bash setup.sh
```

That's it. The setup script handles everything: system dependencies, Python packages, permissions, and desktop integration. After it finishes, search **ThermalCore** in your app launcher.

---

## What `setup.sh` Does

The setup script performs the following steps automatically:

1. **System dependencies** — installs `lm-sensors`, `libxcb-cursor0`, and `python3-venv` via apt
2. **Sensor detection** — runs `sensors-detect` if lm-sensors wasn't previously configured
3. **Python virtual environment** — creates `.venv/` in the project directory
4. **Python packages** — installs PySide6, psutil, and nvidia-ml-py into the venv
5. **CPU power monitoring** — installs a udev rule (`/etc/udev/rules.d/99-thermalcore-rapl.rules`) that grants read access to Intel RAPL energy counters, so CPU power consumption can be monitored without root. This rule persists across reboots
6. **Desktop launcher** — installs `thermalcore.desktop` to `~/.local/share/applications/` and the app icon to `~/.local/share/icons/hicolor/scalable/apps/`, so the app appears in your app launcher and dock with its proper icon

The script is idempotent — running it again skips steps that are already done.

> **Note:** The script requires `sudo` for installing system packages and the udev rule. It will prompt for your password.

---

## Manual Install

If you prefer to install manually or are on a non-Ubuntu distribution:

### 1. Install system dependencies

```bash
# Ubuntu/Debian
sudo apt install lm-sensors libxcb-cursor0 python3-venv
sudo sensors-detect

# Fedora
sudo dnf install lm_sensors python3-devel
sudo sensors-detect

# Arch
sudo pacman -S lm_sensors python
sudo sensors-detect
```

### 2. Clone and set up Python environment

```bash
git clone https://github.com/Vicen-te/ThermalCore.git
cd ThermalCore
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. (Optional) Enable CPU power monitoring

On Intel systems, CPU power is read from RAPL counters which require elevated permissions by default:

```bash
# One-time (current session only)
sudo chmod o+r /sys/class/powercap/intel-rapl:0/energy_uj

# Persistent (survives reboots)
echo 'SUBSYSTEM=="powercap", ACTION=="add", RUN+="/bin/chmod o+r /sys/class/powercap/intel-rapl:0/energy_uj"' \
    | sudo tee /etc/udev/rules.d/99-thermalcore-rapl.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=powercap
```

Without this step, CPU Power will show 0.0 W (the app still works normally otherwise).

### 4. (Optional) Desktop integration

To add ThermalCore to your app launcher:

```bash
# Install icon
mkdir -p ~/.local/share/icons/hicolor/scalable/apps
cp assets/icons/thermalcore.svg ~/.local/share/icons/hicolor/scalable/apps/thermalcore.svg
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor

# Install launcher (replace the path with your actual install location)
sed "s|__INSTALL_DIR__|$(pwd)|g" thermalcore.desktop > ~/.local/share/applications/thermalcore.desktop
update-desktop-database ~/.local/share/applications/
```

---

## Running the App

### From the app launcher (recommended)

Search **ThermalCore** in your desktop's app menu or activities overview. The app will appear in the dock while running.

### From the terminal

```bash
cd ThermalCore
./thermalcore.sh
```

Or manually:

```bash
cd ThermalCore
source .venv/bin/activate
python src/main.py
```

---

## Updating

```bash
cd ThermalCore
git pull
source .venv/bin/activate
pip install -r requirements.txt
```

Run `setup.sh` again only if there are changes to system dependencies or desktop integration.

---

## Uninstalling

```bash
# Remove desktop launcher and icon
rm ~/.local/share/applications/thermalcore.desktop
rm ~/.local/share/icons/hicolor/scalable/apps/thermalcore.svg
update-desktop-database ~/.local/share/applications/
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor

# Remove udev rule (optional)
sudo rm /etc/udev/rules.d/99-thermalcore-rapl.rules
sudo udevadm control --reload-rules

# Remove the project
rm -rf /path/to/ThermalCore
```

---

## Troubleshooting

### No temperatures shown

Make sure lm-sensors is configured:

```bash
sudo sensors-detect
sensors  # should show temperature readings
```

### No GPU detected

This is normal if you don't have an NVIDIA GPU with proprietary drivers. The app shows "No GPU detected" and continues working for CPU, memory, and storage.

For NVIDIA GPUs, verify the driver is loaded:

```bash
nvidia-smi  # should show GPU info
```

### CPU Power shows 0.0 W

The RAPL energy counters need read permissions. Run `setup.sh` or follow the manual RAPL step above, then restart the app.

### App doesn't appear in the dock

The app only appears in the dock when launched from the app launcher (Show Apps). This is standard GNOME behavior — apps launched from a terminal are associated with the terminal window, not their own .desktop entry. Use the app launcher or `gtk-launch thermalcore` from a system terminal (not VS Code).

### PySide6 error about xcb

Install the missing library:

```bash
sudo apt install libxcb-cursor0
```
