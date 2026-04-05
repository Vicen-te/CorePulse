#!/usr/bin/env bash
# Build a .deb package for CorePulse.
# Usage: bash packaging/build-deb.sh
# Output: corepulse_<version>_amd64.deb in the project root.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION=$(grep '^version' "$PROJECT_DIR/pyproject.toml" | head -1 | sed 's/.*"\(.*\)".*/\1/')
ARCH="amd64"
PKG_NAME="corepulse"
PKG_DIR="$PROJECT_DIR/build/${PKG_NAME}_${VERSION}_${ARCH}"

echo "Building ${PKG_NAME} ${VERSION} .deb package..."

# Clean previous build
rm -rf "$PKG_DIR"

# Create directory structure
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/opt/corepulse/src/sensors"
mkdir -p "$PKG_DIR/opt/corepulse/src/ui"
mkdir -p "$PKG_DIR/opt/corepulse/src/utils"
mkdir -p "$PKG_DIR/opt/corepulse/assets/icons"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/scalable/apps"

# Copy application files
cp "$PROJECT_DIR"/src/*.py "$PKG_DIR/opt/corepulse/src/"
cp "$PROJECT_DIR"/src/sensors/*.py "$PKG_DIR/opt/corepulse/src/sensors/"
cp "$PROJECT_DIR"/src/ui/*.py "$PKG_DIR/opt/corepulse/src/ui/"
cp "$PROJECT_DIR"/src/utils/*.py "$PKG_DIR/opt/corepulse/src/utils/"
cp "$PROJECT_DIR/assets/icons/corepulse.svg" "$PKG_DIR/opt/corepulse/assets/icons/"
cp "$PROJECT_DIR/requirements.txt" "$PKG_DIR/opt/corepulse/"

# Icon in system location
cp "$PROJECT_DIR/assets/icons/corepulse.svg" \
   "$PKG_DIR/usr/share/icons/hicolor/scalable/apps/corepulse.svg"

# Desktop entry
cat > "$PKG_DIR/usr/share/applications/corepulse.desktop" << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=CorePulse
Comment=Real-time CPU and GPU temperature monitor
Exec=/usr/bin/corepulse
Icon=corepulse
Categories=System;Monitor;
Terminal=false
StartupNotify=true
StartupWMClass=corepulse
Keywords=temperature;monitor;cpu;gpu;hardware;
DESKTOP

# Launcher script
cat > "$PKG_DIR/usr/bin/corepulse" << 'LAUNCHER'
#!/usr/bin/env bash
cd /opt/corepulse
source .venv/bin/activate
exec python src/main.py "$@"
LAUNCHER
chmod 755 "$PKG_DIR/usr/bin/corepulse"

# DEBIAN/control
cat > "$PKG_DIR/DEBIAN/control" << CONTROL
Package: corepulse
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.10), python3-venv, lm-sensors, libxcb-cursor0
Maintainer: Vicen-te <https://github.com/Vicen-te>
Homepage: https://github.com/Vicen-te/CorePulse
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

echo "[CorePulse] Setting up Python environment..."
python3 -m venv /opt/corepulse/.venv
/opt/corepulse/.venv/bin/pip install -q -r /opt/corepulse/requirements.txt

# Intel RAPL permissions (optional, non-fatal)
RAPL_RULE="/etc/udev/rules.d/99-corepulse-rapl.rules"
if [ -f "/sys/class/powercap/intel-rapl:0/energy_uj" ] && [ ! -f "$RAPL_RULE" ]; then
    echo "[CorePulse] Configuring CPU power monitoring (RAPL)..."
    echo 'SUBSYSTEM=="powercap", ACTION=="add", RUN+="/bin/chmod o+r /sys/class/powercap/intel-rapl:0/energy_uj"' \
        > "$RAPL_RULE"
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger --subsystem-match=powercap 2>/dev/null || true
    chmod o+r /sys/class/powercap/intel-rapl:0/energy_uj 2>/dev/null || true
fi

# Update desktop database and icon cache
update-desktop-database /usr/share/applications/ 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

echo "[CorePulse] Installation complete."
POSTINST
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# DEBIAN/prerm — runs before package removal
cat > "$PKG_DIR/DEBIAN/prerm" << 'PRERM'
#!/bin/bash
set -e
rm -rf /opt/corepulse/.venv
rm -f /etc/udev/rules.d/99-corepulse-rapl.rules
udevadm control --reload-rules 2>/dev/null || true
PRERM
chmod 755 "$PKG_DIR/DEBIAN/prerm"

# Build the .deb
dpkg-deb --build "$PKG_DIR" "$PROJECT_DIR/${PKG_NAME}_${VERSION}_${ARCH}.deb"

echo ""
echo "Package built: ${PKG_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "Install:   sudo apt install ./${PKG_NAME}_${VERSION}_${ARCH}.deb"
echo "Uninstall: sudo apt remove corepulse"
