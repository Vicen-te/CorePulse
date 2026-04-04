#!/usr/bin/env bash
# Setup script for ThermalCore.
# Installs system dependencies, Python packages, and desktop launcher.

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

# Enable CPU power monitoring (Intel RAPL) for non-root users
RAPL_PATH="/sys/class/powercap/intel-rapl:0/energy_uj"
if [ -f "$RAPL_PATH" ]; then
    echo "[*] Enabling CPU power monitoring (RAPL)..."
    sudo chmod o+r "$RAPL_PATH"
fi

# Install desktop launcher
echo "[*] Installing desktop launcher..."
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
sed "s|__INSTALL_DIR__|$SCRIPT_DIR|g" "$SCRIPT_DIR/thermalcore.desktop" > "$DESKTOP_DIR/thermalcore.desktop"
chmod +x "$DESKTOP_DIR/thermalcore.desktop"

echo ""
echo "[+] Setup complete!"
echo "    Run from terminal:  source $SCRIPT_DIR/.venv/bin/activate && python $SCRIPT_DIR/src/main.py"
echo "    Run from launcher:  Search 'ThermalCore' in your app menu"
