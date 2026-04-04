"""
Main window layout for ThermalCore.

Contains the primary application window with a left sidebar showing
sensor card widgets and a right panel for detailed view and charts.
"""

# Standard library
from typing import Optional

# Third-party
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSplitter,
    QStatusBar,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

# Local
from utils.config import (
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    WINDOW_TITLE,
    POLL_INTERVAL_MS,
    TEMP_THRESHOLD_LOW,
    TEMP_THRESHOLD_MEDIUM,
    TEMP_THRESHOLD_HIGH,
    COLOR_TEMP_COOL,
    COLOR_TEMP_WARM,
    COLOR_TEMP_HOT,
    COLOR_TEMP_CRITICAL,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_PANEL,
    COLOR_ACCENT,
)
from sensors.base_sensor import BaseSensor
from sensors.cpu_sensor import discover_cpu_sensors
from sensors.gpu_sensor import discover_gpu_sensors
from ui.sensor_widget import SensorWidget


class MainWindow(QMainWindow):
    """
    Primary application window for ThermalCore.

    Displays sensor card widgets in a scrollable sidebar on the left.
    The right panel shows a detailed view of the selected sensor
    with large temperature display and chart area.

    Attributes:
        sensors: List of all discovered temperature sensors.
        sensor_widgets: List of SensorWidget cards in the sidebar.
    """

    def __init__(self) -> None:
        """Initialize the main window, discover sensors, and start polling."""
        super().__init__()

        self._sensors: list[BaseSensor] = []
        self._sensor_widgets: list[SensorWidget] = []
        self._selected_widget: Optional[SensorWidget] = None

        self._setup_window()
        self._discover_sensors()
        self._setup_ui()
        self._setup_polling()

        # Select first sensor by default
        if self._sensor_widgets:
            self._select_widget(self._sensor_widgets[0])

    def _setup_window(self) -> None:
        """Configure window title, size, and basic properties."""
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.resize(1000, 700)

    def _discover_sensors(self) -> None:
        """Find all available CPU and GPU sensors."""
        self._sensors.extend(discover_cpu_sensors())
        self._sensors.extend(discover_gpu_sensors())

    def _setup_ui(self) -> None:
        """Build the main layout: sidebar with sensor cards + detail panel."""
        # --- Central widget ---
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Splitter for resizable sidebar ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # --- Sidebar: scrollable sensor cards ---
        sidebar_container = QWidget()
        sidebar_container.setStyleSheet(
            f"background-color: {COLOR_PANEL}; border-right: 1px solid {COLOR_ACCENT};"
        )
        sidebar_outer_layout = QVBoxLayout(sidebar_container)
        sidebar_outer_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_outer_layout.setSpacing(0)

        sidebar_header = QLabel("  Sensors")
        sidebar_header.setFixedHeight(40)
        sidebar_header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        sidebar_header.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        sidebar_header.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; background: transparent;")
        sidebar_outer_layout.addWidget(sidebar_header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("border: none; background: transparent;")

        scroll_content = QWidget()
        self._sidebar_layout = QVBoxLayout(scroll_content)
        self._sidebar_layout.setContentsMargins(8, 4, 8, 4)
        self._sidebar_layout.setSpacing(6)

        for sensor in self._sensors:
            widget = SensorWidget(sensor)
            widget.setCursor(Qt.CursorShape.PointingHandCursor)
            widget.mousePressEvent = lambda _, w=widget: self._select_widget(w)
            self._sensor_widgets.append(widget)
            self._sidebar_layout.addWidget(widget)

        self._sidebar_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        sidebar_outer_layout.addWidget(scroll_area)

        sidebar_container.setMinimumWidth(220)
        sidebar_container.setMaximumWidth(350)
        splitter.addWidget(sidebar_container)

        # --- Right panel: details + chart placeholder ---
        self._detail_panel = QWidget()
        detail_layout = QVBoxLayout(self._detail_panel)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(12)

        # Sensor name label
        self._detail_name_label = QLabel("Select a sensor")
        self._detail_name_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._detail_name_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; background: transparent;"
        )
        detail_layout.addWidget(self._detail_name_label)

        # Large temperature display
        self._detail_temp_label = QLabel("--°C")
        mono_font = QFont("JetBrains Mono", 48, QFont.Weight.Bold)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self._detail_temp_label.setFont(mono_font)
        self._detail_temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._detail_temp_label.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; background: transparent;"
        )
        detail_layout.addWidget(self._detail_temp_label)

        # Stats row
        self._detail_stats_label = QLabel("")
        self._detail_stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_font = QFont("Consolas", 12)
        stats_font.setStyleHint(QFont.StyleHint.Monospace)
        self._detail_stats_label.setFont(stats_font)
        self._detail_stats_label.setStyleSheet(
            f"color: {COLOR_TEXT_SECONDARY}; background: transparent;"
        )
        detail_layout.addWidget(self._detail_stats_label)

        # Chart placeholder area — will be replaced in Step 4
        self._chart_container = QFrame()
        self._chart_container.setProperty("class", "sensor-card")
        self._chart_container.setStyleSheet(
            f"background-color: {COLOR_PANEL}; border-radius: 8px;"
        )
        chart_layout = QVBoxLayout(self._chart_container)
        self._chart_placeholder_label = QLabel("Chart will appear here (Step 4)")
        self._chart_placeholder_label.setStyleSheet(
            f"color: {COLOR_TEXT_SECONDARY}; background: transparent;"
        )
        self._chart_placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_layout.addWidget(self._chart_placeholder_label)
        detail_layout.addWidget(self._chart_container, stretch=1)

        splitter.addWidget(self._detail_panel)
        splitter.setSizes([280, 720])

        # --- Status bar ---
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self._status_sensor_count = QLabel(f"{len(self._sensors)} sensors detected")
        status_bar.addPermanentWidget(self._status_sensor_count)

        if not self._sensors:
            self._detail_name_label.setText("No sensors detected")
            self._detail_temp_label.setText("N/A")

    def _setup_polling(self) -> None:
        """Start a timer to refresh temperature readings."""
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._update_readings)
        self._poll_timer.start(POLL_INTERVAL_MS)
        # Trigger immediate first reading
        self._update_readings()

    def _select_widget(self, widget: SensorWidget) -> None:
        """Handle sensor card selection in the sidebar.

        Args:
            widget: The SensorWidget that was clicked.
        """
        # Reset previous selection highlight
        if self._selected_widget is not None:
            self._selected_widget.setStyleSheet(
                f"background-color: {COLOR_PANEL}; border-radius: 8px;"
            )

        self._selected_widget = widget
        widget.setStyleSheet(
            f"background-color: {COLOR_ACCENT}; border-radius: 8px;"
        )
        self._detail_name_label.setText(widget.sensor.get_name())
        self._update_detail_display()

    def _update_readings(self) -> None:
        """Poll all sensors and update widgets."""
        for widget in self._sensor_widgets:
            widget.update_reading()
        self._update_detail_display()

    def _update_detail_display(self) -> None:
        """Update the right panel for the selected sensor."""
        if self._selected_widget is None:
            return

        sensor = self._selected_widget.sensor
        temp = sensor.get_temperature()

        if temp <= 0:
            self._detail_temp_label.setText("N/A")
            return

        self._detail_temp_label.setText(f"{temp:.1f}°C")

        color = self._get_temp_color(temp)
        self._detail_temp_label.setStyleSheet(
            f"color: {color}; background: transparent;"
        )

        # Update stats from the widget's readings
        readings = self._selected_widget._readings
        if readings:
            min_t = self._selected_widget._min_temp
            max_t = self._selected_widget._max_temp
            avg_t = self._selected_widget._sum_temp / len(readings)
            self._detail_stats_label.setText(
                f"Min: {min_t:.1f}°C  |  Max: {max_t:.1f}°C  |  Avg: {avg_t:.1f}°C"
            )

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
