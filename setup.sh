#!/usr/bin/env bash
# Setup script for ThermalCore HW Monitor.
# Installs system dependencies and Python packages in a virtual environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== ThermalCore HW Monitor Setup ==="

# Install system dependencies
echo "[*] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y lm-sensors libxcb-cursor0

if ! command -v sensors &> /dev/null; then
    echo "[*] Detecting sensors..."
    sudo sensors-detect --auto
else
    echo "[+] lm-sensors already installed."
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/.venv"
fi

# Install Python dependencies
echo "[*] Installing Python dependencies..."
"$SCRIPT_DIR/.venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "[+] Setup complete!"
echo "    Activate:  source $SCRIPT_DIR/.venv/bin/activate"
echo "    Run:       python $SCRIPT_DIR/src/main.py"
