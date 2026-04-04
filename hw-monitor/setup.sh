#!/usr/bin/env bash
# Setup script for ThermalCore HW Monitor.
# Installs system dependencies (lm-sensors) and Python packages.

set -euo pipefail

echo "=== ThermalCore HW Monitor Setup ==="

# Install lm-sensors if not already present
if ! command -v sensors &> /dev/null; then
    echo "[*] Installing lm-sensors..."
    sudo apt-get update && sudo apt-get install -y lm-sensors
    echo "[*] Detecting sensors..."
    sudo sensors-detect --auto
else
    echo "[+] lm-sensors already installed."
fi

# Install Python dependencies
echo "[*] Installing Python dependencies..."
pip install -r "$(dirname "$0")/requirements.txt"

echo "[+] Setup complete. Run: python hw-monitor/src/main.py"
