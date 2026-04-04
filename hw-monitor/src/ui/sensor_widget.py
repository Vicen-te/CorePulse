"""
Sensor card widget for displaying individual sensor data.

Shows current temperature in large text, min/max/avg stats since launch,
a color indicator based on temperature thresholds, and a sparkline
showing recent trend.
"""

# Standard library
from collections import deque

# Third-party
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QPen, QColor

# Local
from sensors.base_sensor import BaseSensor
from utils.config import (
    TEMP_THRESHOLD_LOW,
    TEMP_THRESHOLD_MEDIUM,
    TEMP_THRESHOLD_HIGH,
    COLOR_TEMP_COOL,
    COLOR_TEMP_WARM,
    COLOR_TEMP_HOT,
    COLOR_TEMP_CRITICAL,
    COLOR_PANEL,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)

# Number of recent readings to keep for sparkline and stats
SPARKLINE_MAX_POINTS: int = 60


class SparklineWidget(QFrame):
    """
    A small inline chart showing recent temperature trend.

    Draws a simple line graph of the last N temperature readings
    within a compact fixed-size widget.

    Attributes:
        data: Deque of recent temperature values.
    """

    def __init__(self, parent: QFrame | None = None) -> None:
        """Initialize the sparkline widget."""
        super().__init__(parent)
        self._data: deque[float] = deque(maxlen=SPARKLINE_MAX_POINTS)
        self._color = QColor(COLOR_TEMP_COOL)
        self.setFixedHeight(30)
        self.setMinimumWidth(100)

    def set_color(self, color: str) -> None:
        """Update the sparkline color.

        Args:
            color: Hex color string.
        """
        self._color = QColor(color)
        self.update()

    def add_point(self, value: float) -> None:
        """Add a temperature reading to the sparkline.

        Args:
            value: Temperature in Celsius.
        """
        self._data.append(value)
        self.update()

    def paintEvent(self, event: object) -> None:
        """Draw the sparkline graph."""
        if len(self._data) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(self._color, 1.5)
        painter.setPen(pen)

        w = self.width()
        h = self.height()
        margin = 2

        data = list(self._data)
        min_val = min(data) - 1
        max_val = max(data) + 1
        val_range = max_val - min_val if max_val != min_val else 1

        step_x = (w - 2 * margin) / (len(data) - 1)

        for i in range(len(data) - 1):
            x1 = margin + i * step_x
            y1 = h - margin - ((data[i] - min_val) / val_range) * (h - 2 * margin)
            x2 = margin + (i + 1) * step_x
            y2 = h - margin - ((data[i + 1] - min_val) / val_range) * (h - 2 * margin)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        painter.end()


class SensorWidget(QFrame):
    """
    Card widget displaying data for a single temperature sensor.

    Shows the sensor name, current temperature in large text,
    min/max/avg since launch, a color indicator, and a sparkline.

    Attributes:
        sensor: The BaseSensor instance this widget monitors.
        readings: History of temperature readings for stats.
    """

    def __init__(self, sensor: BaseSensor, parent: QFrame | None = None) -> None:
        """Initialize the sensor card widget.

        Args:
            sensor: The temperature sensor to display.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._sensor = sensor
        self._readings: list[float] = []
        self._min_temp: float = float("inf")
        self._max_temp: float = float("-inf")
        self._sum_temp: float = 0.0

        self.setProperty("class", "sensor-card")
        self.setStyleSheet(f"background-color: {COLOR_PANEL}; border-radius: 8px;")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the card layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # --- Top row: name + color indicator ---
        top_row = QHBoxLayout()

        self._name_label = QLabel(self._sensor.get_name())
        self._name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._name_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; background: transparent;")
        top_row.addWidget(self._name_label)

        self._indicator = QLabel("●")
        self._indicator.setFont(QFont("Segoe UI", 14))
        self._indicator.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._indicator.setStyleSheet(f"color: {COLOR_TEMP_COOL}; background: transparent;")
        top_row.addWidget(self._indicator)

        layout.addLayout(top_row)

        # --- Temperature display ---
        self._temp_label = QLabel("--°C")
        mono_font = QFont("JetBrains Mono", 24, QFont.Weight.Bold)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self._temp_label.setFont(mono_font)
        self._temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._temp_label.setStyleSheet(f"color: {COLOR_TEMP_COOL}; background: transparent;")
        layout.addWidget(self._temp_label)

        # --- Stats row: Min / Max / Avg ---
        self._stats_label = QLabel("Min: -- | Max: -- | Avg: --")
        stats_font = QFont("Consolas", 9)
        stats_font.setStyleHint(QFont.StyleHint.Monospace)
        self._stats_label.setFont(stats_font)
        self._stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stats_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self._stats_label)

        # --- Sparkline ---
        self._sparkline = SparklineWidget()
        layout.addWidget(self._sparkline)

    def update_reading(self) -> None:
        """Poll the sensor and update the display."""
        if not self._sensor.is_available():
            self._temp_label.setText("N/A")
            return

        temp = self._sensor.get_temperature()
        if temp <= 0:
            return

        # Update stats
        self._readings.append(temp)
        self._min_temp = min(self._min_temp, temp)
        self._max_temp = max(self._max_temp, temp)
        self._sum_temp += temp
        avg_temp = self._sum_temp / len(self._readings)

        # Update display
        self._temp_label.setText(f"{temp:.1f}°C")
        self._stats_label.setText(
            f"Min: {self._min_temp:.1f} | Max: {self._max_temp:.1f} | Avg: {avg_temp:.1f}"
        )

        # Update color based on temperature
        color = self._get_temp_color(temp)
        self._temp_label.setStyleSheet(f"color: {color}; background: transparent;")
        self._indicator.setStyleSheet(f"color: {color}; background: transparent;")
        self._sparkline.set_color(color)
        self._sparkline.add_point(temp)

    @property
    def sensor(self) -> BaseSensor:
        """Return the sensor associated with this widget."""
        return self._sensor

    @staticmethod
    def _get_temp_color(temp: float) -> str:
        """Return the appropriate color for a temperature value.

        Args:
            temp: Temperature in Celsius.

        Returns:
            Hex color string.
        """
        if temp < TEMP_THRESHOLD_LOW:
            return COLOR_TEMP_COOL
        elif temp < TEMP_THRESHOLD_MEDIUM:
            return COLOR_TEMP_WARM
        elif temp < TEMP_THRESHOLD_HIGH:
            return COLOR_TEMP_HOT
        else:
            return COLOR_TEMP_CRITICAL
