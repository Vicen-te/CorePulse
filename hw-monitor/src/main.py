"""
Entry point for ThermalCore HW Monitor.

Launches the Qt application for real-time temperature monitoring.
"""

import sys

from app import create_app


def main() -> None:
    """Start the ThermalCore application."""
    app = create_app()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
