"""
QSS theme stylesheet for ThermalCore.

Colors adapt automatically to the system dark/light preference.
"""

# Local
from utils.config import (
    COLOR_BACKGROUND,
    COLOR_PANEL,
    COLOR_ACCENT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)

THEME_QSS: str = f"""
QWidget {{
    background-color: {COLOR_BACKGROUND};
    color: {COLOR_TEXT_PRIMARY};
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {COLOR_BACKGROUND};
}}

QScrollBar:vertical {{
    background: {COLOR_PANEL};
    width: 8px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: {COLOR_ACCENT};
    min-height: 30px;
    border-radius: 4px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QStatusBar {{
    background-color: {COLOR_PANEL};
    color: {COLOR_TEXT_SECONDARY};
    font-size: 11px;
    border-top: 1px solid {COLOR_ACCENT};
}}

QToolTip {{
    background-color: {COLOR_PANEL};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_ACCENT};
    padding: 4px;
}}
"""
