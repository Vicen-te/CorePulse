#!/usr/bin/env bash
# Launcher script for CorePulse.
cd "$(dirname "$0")"
source .venv/bin/activate
exec python src/main.py "$@"
