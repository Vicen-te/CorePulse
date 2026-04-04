#!/usr/bin/env bash
# Setup script for ThermalCore.
# Installs system dependencies, Python packages, desktop launcher,
# and persistent permissions. Run once — survives reboots.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== ThermalCore Setup ==="

# Install system dependencies
echo "[*] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y lm-sensors libxcb-cursor0 python3-venv

if ! command -v sensors &> /dev/null; then
    echo "[*] Detecting sensors..."
    sudo sensors-detect --auto
else
    echo "[+] lm-sensors already installed."
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "[*] Creating virtual environment..."
    /usr/bin/python3 -m venv "$SCRIPT_DIR/.venv"
fi

# Install Python dependencies
echo "[*] Installing Python dependencies..."
"$SCRIPT_DIR/.venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

# Persistent CPU power monitoring (Intel RAPL) via udev rule — survives reboots
RAPL_RULE="/etc/udev/rules.d/99-thermalcore-rapl.rules"
if [ -f "/sys/class/powercap/intel-rapl:0/energy_uj" ] && [ ! -f "$RAPL_RULE" ]; then
    echo "[*] Installing udev rule for CPU power monitoring (RAPL)..."
    echo 'SUBSYSTEM=="powercap", ACTION=="add", RUN+="/bin/chmod o+r /sys/class/powercap/intel-rapl:0/energy_uj"' \
        | sudo tee "$RAPL_RULE" > /dev/null
    sudo udevadm control --reload-rules
    sudo udevadm trigger --subsystem-match=powercap
    # Also apply now for current session
    sudo chmod o+r /sys/class/powercap/intel-rapl:0/energy_uj
    echo "[+] RAPL permissions set (persistent across reboots)."
else
    echo "[+] RAPL rule already installed or not applicable."
fi

# Install desktop launcher
echo "[*] Installing desktop launcher..."
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
sed "s|__INSTALL_DIR__|$SCRIPT_DIR|g" "$SCRIPT_DIR/thermalcore.desktop" > "$DESKTOP_DIR/thermalcore.desktop"
chmod +x "$DESKTOP_DIR/thermalcore.desktop"
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo ""
echo "[+] Setup complete!"
echo "    Run from terminal:  source $SCRIPT_DIR/.venv/bin/activate && python $SCRIPT_DIR/src/main.py"
echo "    Run from launcher:  Search 'ThermalCore' in your app menu"
