#!/usr/bin/env bash
# Launcher script for ThermalCore.
cd "$(dirname "$0")"
source .venv/bin/activate
exec python src/main.py "$@"
