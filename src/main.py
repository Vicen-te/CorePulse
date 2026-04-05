"""
Entry point for CorePulse HW Monitor.

Launches the Qt application for real-time temperature monitoring.
"""

# Standard library
import sys

# Local
from app import create_app
from utils.logger import get_logger

log = get_logger("corepulse")


def main() -> None:
    """Start the CorePulse application."""
    sys.argv[0] = "corepulse"
    log.info("Starting CorePulse")
    app, _window = create_app()
    code = app.exec()
    log.info("CorePulse exited with code %d", code)
    sys.exit(code)


if __name__ == "__main__":
    main()
