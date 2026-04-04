"""
Main window layout for ThermalCore.

Contains the primary application window with a left sidebar for
sensor selection and a right panel for details and charts.
"""

# Standard library
from typing import Optional

# Third-party
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
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
)
from sensors.base_sensor import BaseSensor
from sensors.cpu_sensor import discover_cpu_sensors
from sensors.gpu_sensor import discover_gpu_sensors


class MainWindow(QMainWindow):
    """
    Primary application window for ThermalCore.

    Displays a sidebar with discovered sensors on the left and
    a detail/chart panel on the right. Uses a dark monitoring theme.

    Attributes:
        sensors: List of all discovered temperature sensors.
        sidebar: Sensor list widget in the left panel.
        detail_panel: Right panel for sensor details and charts.
    """

    def __init__(self) -> None:
        """Initialize the main window, discover sensors, and start polling."""
        super().__init__()

        self._sensors: list[BaseSensor] = []
        self._selected_sensor: Optional[BaseSensor] = None

        self._setup_window()
        self._discover_sensors()
        self._setup_ui()
        self._setup_polling()

        # Select first sensor by default
        if self._sensors:
            self._sidebar.setCurrentRow(0)

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
        """Build the main layout: sidebar + detail panel."""
        # --- Central widget ---
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Splitter for resizable sidebar ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # --- Sidebar: sensor list ---
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        sidebar_header = QLabel("  Sensors")
        sidebar_header.setFixedHeight(40)
        sidebar_header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        sidebar_header.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        sidebar_layout.addWidget(sidebar_header)

        self._sidebar = QListWidget()
        self._sidebar.setMinimumWidth(200)
        self._sidebar.setMaximumWidth(300)
        for sensor in self._sensors:
            item = QListWidgetItem(sensor.get_name())
            self._sidebar.addItem(item)
        self._sidebar.currentRowChanged.connect(self._on_sensor_selected)
        sidebar_layout.addWidget(self._sidebar)

        splitter.addWidget(sidebar_widget)

        # --- Right panel: details + chart placeholder ---
        self._detail_panel = QWidget()
        detail_layout = QVBoxLayout(self._detail_panel)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(12)

        # Sensor name label
        self._sensor_name_label = QLabel("Select a sensor")
        self._sensor_name_label.setProperty("class", "sensor-name")
        self._sensor_name_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        detail_layout.addWidget(self._sensor_name_label)

        # Temperature display
        self._temp_label = QLabel("--°C")
        self._temp_label.setProperty("class", "temperature")
        mono_font = QFont("JetBrains Mono", 48, QFont.Weight.Bold)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self._temp_label.setFont(mono_font)
        self._temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail_layout.addWidget(self._temp_label)

        # Stats row (min / max / avg) — placeholder for Step 3
        self._stats_label = QLabel("")
        self._stats_label.setProperty("class", "secondary")
        self._stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stats_label.setFont(QFont("Consolas", 12))
        detail_layout.addWidget(self._stats_label)

        # Chart placeholder area
        self._chart_placeholder = QFrame()
        self._chart_placeholder.setProperty("class", "sensor-card")
        chart_layout = QVBoxLayout(self._chart_placeholder)
        chart_label = QLabel("Chart will appear here (Step 4)")
        chart_label.setProperty("class", "secondary")
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_layout.addWidget(chart_label)
        detail_layout.addWidget(self._chart_placeholder, stretch=1)

        splitter.addWidget(self._detail_panel)

        # Sidebar takes ~25% of width
        splitter.setSizes([250, 750])

        # --- Status bar ---
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self._status_sensor_count = QLabel(f"{len(self._sensors)} sensors detected")
        status_bar.addPermanentWidget(self._status_sensor_count)

        if not self._sensors:
            self._sensor_name_label.setText("No sensors detected")
            self._temp_label.setText("N/A")

    def _setup_polling(self) -> None:
        """Start a timer to refresh temperature readings."""
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._update_readings)
        self._poll_timer.start(POLL_INTERVAL_MS)

    def _on_sensor_selected(self, row: int) -> None:
        """Handle sidebar sensor selection.

        Args:
            row: Index of the selected sensor in the list.
        """
        if 0 <= row < len(self._sensors):
            self._selected_sensor = self._sensors[row]
            self._sensor_name_label.setText(self._selected_sensor.get_name())
            self._update_selected_display()

    def _update_readings(self) -> None:
        """Poll all sensors and refresh the currently displayed one."""
        self._update_selected_display()

    def _update_selected_display(self) -> None:
        """Update the temperature display for the selected sensor."""
        if self._selected_sensor is None:
            return

        temp = self._selected_sensor.get_temperature()
        self._temp_label.setText(f"{temp:.1f}°C")

        # Color the temperature based on thresholds
        from utils.config import (
            TEMP_THRESHOLD_LOW,
            TEMP_THRESHOLD_MEDIUM,
            TEMP_THRESHOLD_HIGH,
            COLOR_TEMP_COOL,
            COLOR_TEMP_WARM,
            COLOR_TEMP_HOT,
            COLOR_TEMP_CRITICAL,
        )

        if temp < TEMP_THRESHOLD_LOW:
            color = COLOR_TEMP_COOL
        elif temp < TEMP_THRESHOLD_MEDIUM:
            color = COLOR_TEMP_WARM
        elif temp < TEMP_THRESHOLD_HIGH:
            color = COLOR_TEMP_HOT
        else:
            color = COLOR_TEMP_CRITICAL

        self._temp_label.setStyleSheet(f"color: {color}; background: transparent;")
