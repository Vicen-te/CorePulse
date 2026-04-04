"""
QApplication factory for ThermalCore.

Creates and configures the PySide6 application instance
with the appropriate settings for the monitoring tool.
"""

import sys

from PySide6.QtWidgets import QApplication


def create_app() -> QApplication:
    """
    Create and configure the QApplication instance.

    Returns:
        A configured QApplication ready to run.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("ThermalCore")
    app.setOrganizationName("ThermalCore")
    return app
