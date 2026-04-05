"""
Entry point for ThermalCore HW Monitor.

Launches the Qt application for real-time temperature monitoring.
"""

# Standard library
import sys

# Local
from app import create_app


def main() -> None:
    """Start the ThermalCore application."""
    sys.argv[0] = "thermalcore"
    app, _window = create_app()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
