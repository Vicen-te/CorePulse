"""
QSS dark theme stylesheet for ThermalCore.

Defines the dark monitoring theme used throughout the application.
All color values reference the constants in utils.config.
"""

# Local
from utils.config import (
    COLOR_BACKGROUND,
    COLOR_PANEL,
    COLOR_ACCENT,
    COLOR_WARNING,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)

DARK_THEME_QSS: str = f"""
/* --- Global --- */
QWidget {{
    background-color: {COLOR_BACKGROUND};
    color: {COLOR_TEXT_PRIMARY};
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}}

/* --- Main window --- */
QMainWindow {{
    background-color: {COLOR_BACKGROUND};
}}

/* --- Sidebar list --- */
QListWidget {{
    background-color: {COLOR_PANEL};
    border: none;
    border-right: 1px solid {COLOR_ACCENT};
    padding: 4px;
    outline: none;
}}

QListWidget::item {{
    padding: 8px 12px;
    border-radius: 4px;
    margin: 2px 4px;
    color: {COLOR_TEXT_SECONDARY};
}}

QListWidget::item:selected {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_TEXT_PRIMARY};
}}

QListWidget::item:hover:!selected {{
    background-color: rgba(15, 52, 96, 0.5);
}}

/* --- Scroll bars --- */
QScrollBar:vertical {{
    background: {COLOR_PANEL};
    width: 8px;
    margin: 0;
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

QScrollBar:horizontal {{
    background: {COLOR_PANEL};
    height: 8px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: {COLOR_ACCENT};
    min-width: 30px;
    border-radius: 4px;
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* --- Labels --- */
QLabel {{
    background: transparent;
    color: {COLOR_TEXT_PRIMARY};
}}

QLabel[class="secondary"] {{
    color: {COLOR_TEXT_SECONDARY};
}}

QLabel[class="temperature"] {{
    font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
    font-size: 28px;
    font-weight: bold;
}}

QLabel[class="sensor-name"] {{
    font-size: 14px;
    font-weight: bold;
}}

QLabel[class="header-info"] {{
    font-size: 11px;
    color: {COLOR_TEXT_SECONDARY};
}}

/* --- Frames / panels --- */
QFrame[class="sensor-card"] {{
    background-color: {COLOR_PANEL};
    border-radius: 8px;
    padding: 12px;
}}

QFrame[class="header-bar"] {{
    background-color: {COLOR_PANEL};
    border-bottom: 1px solid {COLOR_ACCENT};
    padding: 8px 16px;
}}

/* --- Push buttons --- */
QPushButton {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_TEXT_PRIMARY};
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: #124b8a;
}}

QPushButton:pressed {{
    background-color: #0a2540;
}}

/* --- Splitter --- */
QSplitter::handle {{
    background-color: {COLOR_ACCENT};
    width: 2px;
}}

/* --- Status bar --- */
QStatusBar {{
    background-color: {COLOR_PANEL};
    color: {COLOR_TEXT_SECONDARY};
    font-size: 11px;
    border-top: 1px solid {COLOR_ACCENT};
}}

/* --- Tooltip --- */
QToolTip {{
    background-color: {COLOR_PANEL};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_ACCENT};
    padding: 4px;
    font-size: 12px;
}}
"""
