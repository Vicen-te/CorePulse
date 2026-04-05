#!/usr/bin/env bash
# Setup script for CorePulse.
# Installs system dependencies, Python packages, desktop launcher,
# and persistent permissions. Run once — survives reboots.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== CorePulse Setup ==="

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
RAPL_RULE="/etc/udev/rules.d/99-corepulse-rapl.rules"
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
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$DESKTOP_DIR" "$ICON_DIR"
cp "$SCRIPT_DIR/assets/icons/corepulse.svg" "$ICON_DIR/corepulse.svg"
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
sed "s|__INSTALL_DIR__|$SCRIPT_DIR|g" "$SCRIPT_DIR/corepulse.desktop" > "$DESKTOP_DIR/corepulse.desktop"
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo ""
echo "[+] Setup complete!"
echo "    Run from terminal:  source $SCRIPT_DIR/.venv/bin/activate && python $SCRIPT_DIR/src/main.py"
echo "    Run from launcher:  Search 'CorePulse' in your app menu"
