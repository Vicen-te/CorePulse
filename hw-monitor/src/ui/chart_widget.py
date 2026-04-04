"""
Real-time temperature chart widget.

Renders a scrolling line chart using pyqtgraph showing the last
60-120 seconds of temperature data for all sensors. Supports
highlighting a selected sensor's line.
"""

# Standard library
import time
from collections import deque

# Third-party
import pyqtgraph as pg
from PySide6.QtWidgets import QVBoxLayout, QFrame
from PySide6.QtGui import QColor

# Local
from sensors.base_sensor import BaseSensor
from utils.config import (
    CHART_HISTORY_SECONDS,
    CHART_LINE_WIDTH,
    COLOR_BACKGROUND,
    COLOR_PANEL,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_ACCENT,
)

# Color palette for chart lines
LINE_COLORS: list[str] = [
    "#00c853", "#ffd600", "#2196f3", "#e94560", "#ab47bc",
    "#00bcd4", "#ff6d00", "#8bc34a", "#ff5252", "#7c4dff",
    "#26a69a", "#ec407a", "#5c6bc0", "#ffca28", "#66bb6a",
]

HIGHLIGHT_WIDTH: int = 3
DIM_ALPHA: int = 60


class ChartWidget(QFrame):
    """
    Scrolling line chart for real-time temperature monitoring.

    Displays one line per sensor with a legend. The chart scrolls
    to show the last CHART_HISTORY_SECONDS of data. A selected
    sensor's line is highlighted while others are dimmed.

    Attributes:
        sensors: List of sensors being plotted.
        plot_widget: The pyqtgraph PlotWidget.
    """

    def __init__(self, parent: QFrame | None = None) -> None:
        """Initialize the chart widget."""
        super().__init__(parent)
        self._sensors: list[BaseSensor] = []
        self._lines: dict[str, pg.PlotDataItem] = {}
        self._data: dict[str, deque[float]] = {}
        self._times: dict[str, deque[float]] = {}
        self._start_time: float = time.monotonic()
        self._selected_sensor_name: str | None = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the chart layout with pyqtgraph."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Configure pyqtgraph for dark theme
        pg.setConfigOptions(antialias=True, background=COLOR_PANEL, foreground=COLOR_TEXT_PRIMARY)

        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setLabel("left", "Temperature", units="°C")
        self._plot_widget.setLabel("bottom", "Time", units="s")
        self._plot_widget.showGrid(x=True, y=True, alpha=0.15)
        self._plot_widget.setMouseEnabled(x=False, y=False)

        # Style the axes
        axis_pen = pg.mkPen(color=COLOR_TEXT_SECONDARY, width=1)
        for axis_name in ("left", "bottom"):
            axis = self._plot_widget.getAxis(axis_name)
            axis.setPen(axis_pen)
            axis.setTextPen(pg.mkPen(color=COLOR_TEXT_SECONDARY))

        # Add legend
        self._legend = self._plot_widget.addLegend(
            offset=(10, 10),
            brush=pg.mkBrush(QColor(COLOR_PANEL)),
            pen=pg.mkPen(color=COLOR_ACCENT),
        )

        layout.addWidget(self._plot_widget)

    def set_sensors(self, sensors: list[BaseSensor]) -> None:
        """Configure the chart with sensors to plot.

        Args:
            sensors: List of sensors to create lines for.
        """
        self._sensors = sensors
        self._start_time = time.monotonic()

        # Clear existing lines
        self._plot_widget.clear()
        self._lines.clear()
        self._data.clear()
        self._times.clear()

        # Re-add legend after clear
        if self._legend is not None:
            self._legend.clear()

        for i, sensor in enumerate(sensors):
            name = sensor.get_name()
            color = LINE_COLORS[i % len(LINE_COLORS)]
            pen = pg.mkPen(color=color, width=CHART_LINE_WIDTH)
            line = self._plot_widget.plot([], [], pen=pen, name=name)
            self._lines[name] = line
            self._data[name] = deque(maxlen=CHART_HISTORY_SECONDS)
            self._times[name] = deque(maxlen=CHART_HISTORY_SECONDS)

    def update_data(self) -> None:
        """Add a new data point from each sensor and refresh the chart."""
        now = time.monotonic() - self._start_time

        for sensor in self._sensors:
            name = sensor.get_name()
            if name not in self._lines:
                continue

            temp = sensor.get_temperature()
            if temp <= 0:
                continue

            self._times[name].append(now)
            self._data[name].append(temp)

            self._lines[name].setData(
                list(self._times[name]),
                list(self._data[name]),
            )

        # Auto-scroll: keep the x-axis showing the last CHART_HISTORY_SECONDS
        if now > CHART_HISTORY_SECONDS:
            self._plot_widget.setXRange(now - CHART_HISTORY_SECONDS, now)
        else:
            self._plot_widget.setXRange(0, max(CHART_HISTORY_SECONDS, now))

    def highlight_sensor(self, sensor_name: str | None) -> None:
        """Highlight a specific sensor's line and dim others.

        Args:
            sensor_name: Name of the sensor to highlight, or None to reset.
        """
        self._selected_sensor_name = sensor_name

        for i, sensor in enumerate(self._sensors):
            name = sensor.get_name()
            line = self._lines.get(name)
            if line is None:
                continue

            base_color = QColor(LINE_COLORS[i % len(LINE_COLORS)])

            if sensor_name is None:
                # No selection — show all lines normally
                pen = pg.mkPen(color=base_color, width=CHART_LINE_WIDTH)
            elif name == sensor_name:
                # Selected — bold line
                pen = pg.mkPen(color=base_color, width=HIGHLIGHT_WIDTH)
            else:
                # Dimmed — reduce alpha
                dimmed = QColor(base_color)
                dimmed.setAlpha(DIM_ALPHA)
                pen = pg.mkPen(color=dimmed, width=1)

            line.setPen(pen)
