"""
Application constants and configuration.

Centralized configuration values used throughout the application.
All magic numbers and thresholds are defined here.
Theme colors are selected automatically based on the system preference.
"""

# Standard library
import subprocess

# --- Window defaults ---
DEFAULT_WINDOW_WIDTH: int = 800
DEFAULT_WINDOW_HEIGHT: int = 600
WINDOW_TITLE: str = "ThermalCore — HW Monitor"

# --- Polling ---
POLL_INTERVAL_MS: int = 1000

# --- Temperature thresholds (Celsius) ---
TEMP_THRESHOLD_LOW: int = 50
TEMP_THRESHOLD_MEDIUM: int = 70
TEMP_THRESHOLD_HIGH: int = 85
CRITICAL_TEMP_THRESHOLD: int = 85


def _detect_dark_mode() -> bool:
    """Detect whether the system is using a dark theme."""
    try:
        r = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True, text=True, timeout=2,
        )
        if "dark" in r.stdout.lower():
            return True
    except (OSError, subprocess.TimeoutExpired):
        pass

    try:
        r = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            capture_output=True, text=True, timeout=2,
        )
        if "dark" in r.stdout.lower():
            return True
    except (OSError, subprocess.TimeoutExpired):
        pass

    # Default to dark if detection fails
    return True


IS_DARK_THEME: bool = _detect_dark_mode()

# --- Dark theme colors ---
_DARK = {
    "background": "#1a1a2e",
    "panel": "#16213e",
    "accent": "#0f3460",
    "warning": "#e94560",
    "text_primary": "#eeeeee",
    "text_secondary": "#aaaaaa",
    "temp_cool": "#00c853",
    "temp_warm": "#ffd600",
    "temp_hot": "#ff6d00",
    "temp_critical": "#e94560",
}

# --- Light theme colors ---
_LIGHT = {
    "background": "#f5f5f5",
    "panel": "#e8e8e8",
    "accent": "#c0c0c0",
    "warning": "#d32f2f",
    "text_primary": "#1a1a1a",
    "text_secondary": "#666666",
    "temp_cool": "#2e7d32",
    "temp_warm": "#f57f17",
    "temp_hot": "#e65100",
    "temp_critical": "#c62828",
}

_THEME = _DARK if IS_DARK_THEME else _LIGHT

COLOR_BACKGROUND: str = _THEME["background"]
COLOR_PANEL: str = _THEME["panel"]
COLOR_ACCENT: str = _THEME["accent"]
COLOR_WARNING: str = _THEME["warning"]
COLOR_TEXT_PRIMARY: str = _THEME["text_primary"]
COLOR_TEXT_SECONDARY: str = _THEME["text_secondary"]
COLOR_TEMP_COOL: str = _THEME["temp_cool"]
COLOR_TEMP_WARM: str = _THEME["temp_warm"]
COLOR_TEMP_HOT: str = _THEME["temp_hot"]
COLOR_TEMP_CRITICAL: str = _THEME["temp_critical"]
