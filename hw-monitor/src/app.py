"""
QApplication factory for ThermalCore.

Creates and configures the PySide6 application instance
with the dark theme and main window.
"""

# Standard library
import sys

# Third-party
from PySide6.QtWidgets import QApplication

# Local
from ui.styles import DARK_THEME_QSS
from ui.main_window import MainWindow


def create_app() -> tuple[QApplication, MainWindow]:
    """
    Create and configure the QApplication and main window.

    Returns:
        A tuple of the configured QApplication and MainWindow.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("ThermalCore")
    app.setOrganizationName("ThermalCore")
    app.setStyleSheet(DARK_THEME_QSS)

    window = MainWindow()
    window.show()

    return app, window
