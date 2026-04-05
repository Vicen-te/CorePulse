"""
Application constants and configuration.

Centralized configuration values used throughout the application.
Theme colors adapt automatically to the system dark/light preference.
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

# --- Theme palettes ---
DARK_PALETTE: dict[str, str] = {
    "background": "#2b2b2b",
    "panel": "#333333",
    "accent": "#444444",
    "warning": "#e95420",
    "text_primary": "#f0f0f0",
    "text_secondary": "#999999",
    "temp_cool": "#73d216",
    "temp_warm": "#f5c211",
    "temp_hot": "#e95420",
    "temp_critical": "#cc0000",
}

LIGHT_PALETTE: dict[str, str] = {
    "background": "#fafafa",
    "panel": "#ebebeb",
    "accent": "#d6d6d6",
    "warning": "#e95420",
    "text_primary": "#1c1c1c",
    "text_secondary": "#666666",
    "temp_cool": "#3a7d34",
    "temp_warm": "#e6a003",
    "temp_hot": "#c7400a",
    "temp_critical": "#a40e0e",
}


def detect_dark_mode() -> bool:
    """Detect whether the system is using a dark theme."""
    # Check GNOME color-scheme
    try:
        r = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True, text=True, timeout=2,
        )
        if r.returncode == 0 and r.stdout.strip():
            return "dark" in r.stdout.lower()
    except (OSError, subprocess.TimeoutExpired):
        pass

    # Check GTK theme name
    try:
        r = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            capture_output=True, text=True, timeout=2,
        )
        if r.returncode == 0 and r.stdout.strip():
            return "dark" in r.stdout.lower()
    except (OSError, subprocess.TimeoutExpired):
        pass

    return True


def get_palette() -> dict[str, str]:
    """Return the active color palette based on system theme."""
    return DARK_PALETTE if detect_dark_mode() else LIGHT_PALETTE


# Current palette — set once at import, updated live by ThemeWatcher
_palette: dict[str, str] = get_palette()

COLOR_BACKGROUND: str = _palette["background"]
COLOR_PANEL: str = _palette["panel"]
COLOR_ACCENT: str = _palette["accent"]
COLOR_WARNING: str = _palette["warning"]
COLOR_TEXT_PRIMARY: str = _palette["text_primary"]
COLOR_TEXT_SECONDARY: str = _palette["text_secondary"]
COLOR_TEMP_COOL: str = _palette["temp_cool"]
COLOR_TEMP_WARM: str = _palette["temp_warm"]
COLOR_TEMP_HOT: str = _palette["temp_hot"]
COLOR_TEMP_CRITICAL: str = _palette["temp_critical"]


def apply_palette(palette: dict[str, str]) -> None:
    """Update module-level color variables from a palette dict."""
    import utils.config as _self
    _self.COLOR_BACKGROUND = palette["background"]
    _self.COLOR_PANEL = palette["panel"]
    _self.COLOR_ACCENT = palette["accent"]
    _self.COLOR_WARNING = palette["warning"]
    _self.COLOR_TEXT_PRIMARY = palette["text_primary"]
    _self.COLOR_TEXT_SECONDARY = palette["text_secondary"]
    _self.COLOR_TEMP_COOL = palette["temp_cool"]
    _self.COLOR_TEMP_WARM = palette["temp_warm"]
    _self.COLOR_TEMP_HOT = palette["temp_hot"]
    _self.COLOR_TEMP_CRITICAL = palette["temp_critical"]
    _self._palette = palette
