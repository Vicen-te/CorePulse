"""
Application constants and configuration.

Centralized configuration values used throughout the application.
All magic numbers and thresholds are defined here.
"""

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

# --- Theme colors ---
COLOR_BACKGROUND: str = "#1a1a2e"
COLOR_PANEL: str = "#16213e"
COLOR_ACCENT: str = "#0f3460"
COLOR_WARNING: str = "#e94560"
COLOR_TEXT_PRIMARY: str = "#eeeeee"
COLOR_TEXT_SECONDARY: str = "#aaaaaa"

# --- Temperature status colors ---
COLOR_TEMP_COOL: str = "#00c853"
COLOR_TEMP_WARM: str = "#ffd600"
COLOR_TEMP_HOT: str = "#ff6d00"
COLOR_TEMP_CRITICAL: str = "#e94560"

