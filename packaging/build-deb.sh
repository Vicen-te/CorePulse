#!/usr/bin/env bash
# Build a .deb package for ThermalCore.
# Usage: bash packaging/build-deb.sh
# Output: thermalcore_<version>_amd64.deb in the project root.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION=$(grep '^version' "$PROJECT_DIR/pyproject.toml" | head -1 | sed 's/.*"\(.*\)".*/\1/')
ARCH="amd64"
PKG_NAME="thermalcore"
PKG_DIR="$PROJECT_DIR/build/${PKG_NAME}_${VERSION}_${ARCH}"

echo "Building ${PKG_NAME} ${VERSION} .deb package..."

# Clean previous build
rm -rf "$PKG_DIR"

# Create directory structure
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/opt/thermalcore/src/sensors"
mkdir -p "$PKG_DIR/opt/thermalcore/src/ui"
mkdir -p "$PKG_DIR/opt/thermalcore/src/utils"
mkdir -p "$PKG_DIR/opt/thermalcore/assets/icons"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/scalable/apps"

# Copy application files
cp "$PROJECT_DIR"/src/*.py "$PKG_DIR/opt/thermalcore/src/"
cp "$PROJECT_DIR"/src/sensors/*.py "$PKG_DIR/opt/thermalcore/src/sensors/"
cp "$PROJECT_DIR"/src/ui/*.py "$PKG_DIR/opt/thermalcore/src/ui/"
cp "$PROJECT_DIR"/src/utils/*.py "$PKG_DIR/opt/thermalcore/src/utils/"
cp "$PROJECT_DIR/assets/icons/thermalcore.svg" "$PKG_DIR/opt/thermalcore/assets/icons/"
cp "$PROJECT_DIR/requirements.txt" "$PKG_DIR/opt/thermalcore/"

# Icon in system location
cp "$PROJECT_DIR/assets/icons/thermalcore.svg" \
   "$PKG_DIR/usr/share/icons/hicolor/scalable/apps/thermalcore.svg"

# Desktop entry
cat > "$PKG_DIR/usr/share/applications/thermalcore.desktop" << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=ThermalCore
Comment=Real-time CPU and GPU temperature monitor
Exec=/usr/bin/thermalcore
Icon=thermalcore
Categories=System;Monitor;
Terminal=false
StartupNotify=true
StartupWMClass=thermalcore
Keywords=temperature;monitor;cpu;gpu;hardware;
DESKTOP

# Launcher script
cat > "$PKG_DIR/usr/bin/thermalcore" << 'LAUNCHER'
#!/usr/bin/env bash
cd /opt/thermalcore
source .venv/bin/activate
exec python src/main.py "$@"
LAUNCHER
chmod 755 "$PKG_DIR/usr/bin/thermalcore"

# DEBIAN/control
cat > "$PKG_DIR/DEBIAN/control" << CONTROL
Package: thermalcore
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.10), python3-venv, lm-sensors, libxcb-cursor0
Recommends: nvidia-driver-560 | nvidia-driver-550 | nvidia-driver-545 | nvidia-driver-535
Maintainer: Vicen-te <https://github.com/Vicen-te>
Homepage: https://github.com/Vicen-te/ThermalCore
Description: Real-time hardware monitor for Linux
 Lightweight desktop application that monitors CPU and GPU temperatures,
 clocks, load, power consumption, and storage health in a tree view with
 live updates, per-sensor alerts, and CSV export.
 .
 Features: per-core CPU temps, NVIDIA GPU via pynvml, AMD GPU via sysfs,
 auto dark/light theme, system tray, IPC socket for external apps.
CONTROL

# DEBIAN/postinst — runs after package install
cat > "$PKG_DIR/DEBIAN/postinst" << 'POSTINST'
#!/bin/bash
set -e

echo "[ThermalCore] Setting up Python environment..."
python3 -m venv /opt/thermalcore/.venv
/opt/thermalcore/.venv/bin/pip install -q -r /opt/thermalcore/requirements.txt

# Intel RAPL permissions (optional, non-fatal)
RAPL_RULE="/etc/udev/rules.d/99-thermalcore-rapl.rules"
if [ -f "/sys/class/powercap/intel-rapl:0/energy_uj" ] && [ ! -f "$RAPL_RULE" ]; then
    echo "[ThermalCore] Configuring CPU power monitoring (RAPL)..."
    echo 'SUBSYSTEM=="powercap", ACTION=="add", RUN+="/bin/chmod o+r /sys/class/powercap/intel-rapl:0/energy_uj"' \
        > "$RAPL_RULE"
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger --subsystem-match=powercap 2>/dev/null || true
    chmod o+r /sys/class/powercap/intel-rapl:0/energy_uj 2>/dev/null || true
fi

# Update desktop database and icon cache
update-desktop-database /usr/share/applications/ 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

echo "[ThermalCore] Installation complete."
POSTINST
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# DEBIAN/prerm — runs before package removal
cat > "$PKG_DIR/DEBIAN/prerm" << 'PRERM'
#!/bin/bash
set -e
rm -rf /opt/thermalcore/.venv
rm -f /etc/udev/rules.d/99-thermalcore-rapl.rules
udevadm control --reload-rules 2>/dev/null || true
PRERM
chmod 755 "$PKG_DIR/DEBIAN/prerm"

# Build the .deb
dpkg-deb --build "$PKG_DIR" "$PROJECT_DIR/${PKG_NAME}_${VERSION}_${ARCH}.deb"

echo ""
echo "Package built: ${PKG_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "Install:   sudo apt install ./${PKG_NAME}_${VERSION}_${ARCH}.deb"
echo "Uninstall: sudo apt remove thermalcore"
