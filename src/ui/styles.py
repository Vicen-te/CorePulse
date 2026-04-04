"""
QSS theme stylesheet for ThermalCore.

Colors adapt automatically to the system dark/light preference
and switch live when the system theme changes.
"""


def build_qss(palette: dict[str, str]) -> str:
    """Build a QSS stylesheet from a color palette dict."""
    bg = palette["background"]
    panel = palette["panel"]
    accent = palette["accent"]
    text1 = palette["text_primary"]
    text2 = palette["text_secondary"]

    return f"""
QWidget {{
    background-color: {bg};
    color: {text1};
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {bg};
}}

QScrollBar:vertical {{
    background: {panel};
    width: 8px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: {accent};
    min-height: 30px;
    border-radius: 4px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QStatusBar {{
    background-color: {panel};
    color: {text2};
    font-size: 11px;
    border-top: 1px solid {accent};
}}

QToolTip {{
    background-color: {panel};
    color: {text1};
    border: 1px solid {accent};
    padding: 4px;
}}
"""


# Build initial QSS at import time
from utils.config import get_palette
THEME_QSS: str = build_qss(get_palette())
