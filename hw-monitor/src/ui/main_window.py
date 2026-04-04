"""
Main window layout for ThermalCore.

Contains the primary application window with a left sidebar showing
sensor card widgets and a right panel for detailed view and charts.
Includes system tray, alerts, CSV export, and system info header.
"""

# Standard library
import csv
import os
import platform
import socket
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
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
    QScrollArea,
    QFrame,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
    QFileDialog,
    QSpinBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QAction, QPixmap, QPainter, QColor

# Local
from utils.config import (
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    WINDOW_TITLE,
    POLL_INTERVAL_MS,
    TEMP_THRESHOLD_LOW,
    TEMP_THRESHOLD_MEDIUM,
    TEMP_THRESHOLD_HIGH,
    CRITICAL_TEMP_THRESHOLD,
    COLOR_TEMP_COOL,
    COLOR_TEMP_WARM,
    COLOR_TEMP_HOT,
    COLOR_TEMP_CRITICAL,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_PANEL,
    COLOR_ACCENT,
    COLOR_BACKGROUND,
    COLOR_WARNING,
)
from sensors.base_sensor import BaseSensor
from sensors.cpu_sensor import discover_cpu_sensors
from sensors.gpu_sensor import discover_gpu_sensors
from ui.sensor_widget import SensorWidget
from ui.chart_widget import ChartWidget


def _get_system_info() -> dict[str, str]:
    """
    Gather system information for the header bar.

    Returns:
        Dictionary with hostname, os, kernel, cpu_model, gpu_model, and uptime.
    """
    info: dict[str, str] = {}

    info["hostname"] = socket.gethostname()
    info["os"] = f"{platform.system()} {platform.release()}"
    info["kernel"] = platform.release()

    # CPU model
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    info["cpu_model"] = line.split(":", 1)[1].strip()
                    break
    except OSError:
        info["cpu_model"] = "Unknown CPU"

    # GPU model via nvidia-smi
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            text=True, timeout=5, stderr=subprocess.DEVNULL,
        ).strip()
        info["gpu_model"] = output.splitlines()[0] if output else "No GPU"
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        info["gpu_model"] = "No GPU detected"

    # Uptime
    try:
        with open("/proc/uptime") as f:
            uptime_seconds = float(f.read().split()[0])
            delta = timedelta(seconds=int(uptime_seconds))
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            info["uptime"] = f"{days}d {hours}h {minutes}m"
    except OSError:
        info["uptime"] = "Unknown"

    return info


def _create_app_icon() -> QIcon:
    """
    Create a simple colored icon for the app and system tray.

    Returns:
        A QIcon with a thermal indicator.
    """
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Draw a circle with thermal gradient colors
    painter.setBrush(QColor(COLOR_WARNING))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, 56, 56)
    painter.setBrush(QColor(COLOR_BACKGROUND))
    painter.drawEllipse(14, 14, 36, 36)
    painter.setBrush(QColor(COLOR_TEMP_COOL))
    painter.drawEllipse(22, 22, 20, 20)
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    """
    Primary application window for ThermalCore.

    Displays sensor card widgets in a scrollable sidebar on the left.
    The right panel shows system info header, selected sensor details,
    and a real-time chart. Supports system tray, temperature alerts,
    and CSV export.

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
        self._temperature_log: list[dict[str, object]] = []
        self._alert_threshold: int = CRITICAL_TEMP_THRESHOLD
        self._alert_active: bool = False
        self._start_time: float = time.time()

        self._setup_window()
        self._discover_sensors()
        self._setup_ui()
        self._setup_system_tray()
        self._setup_polling()

        # Select first sensor by default
        if self._sensor_widgets:
            self._select_widget(self._sensor_widgets[0])

    def _setup_window(self) -> None:
        """Configure window title, size, and basic properties."""
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.resize(1000, 700)
        self._app_icon = _create_app_icon()
        self.setWindowIcon(self._app_icon)

    def _discover_sensors(self) -> None:
        """Find all available CPU and GPU sensors."""
        self._sensors.extend(discover_cpu_sensors())
        self._sensors.extend(discover_gpu_sensors())

    def _setup_ui(self) -> None:
        """Build the main layout: header + sidebar + detail panel."""
        # --- Central widget ---
        central = QWidget()
        self.setCentralWidget(central)
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # --- System info header ---
        self._setup_header(outer_layout)

        # --- Content area: sidebar + detail ---
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        content_layout.addWidget(splitter)

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

        # --- Right panel: details + chart ---
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

        # --- Controls row: alert threshold + export button ---
        controls_row = QHBoxLayout()
        controls_row.setSpacing(12)

        alert_label = QLabel("Alert threshold:")
        alert_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; background: transparent;")
        controls_row.addWidget(alert_label)

        self._threshold_spin = QSpinBox()
        self._threshold_spin.setRange(30, 120)
        self._threshold_spin.setValue(self._alert_threshold)
        self._threshold_spin.setSuffix("°C")
        self._threshold_spin.setStyleSheet(
            f"background-color: {COLOR_PANEL}; color: {COLOR_TEXT_PRIMARY}; "
            f"border: 1px solid {COLOR_ACCENT}; border-radius: 4px; padding: 2px 8px;"
        )
        self._threshold_spin.valueChanged.connect(self._on_threshold_changed)
        controls_row.addWidget(self._threshold_spin)

        controls_row.addStretch()

        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self._export_csv)
        controls_row.addWidget(export_btn)

        detail_layout.addLayout(controls_row)

        # --- Real-time chart ---
        self._chart = ChartWidget()
        self._chart.set_sensors(self._sensors)
        detail_layout.addWidget(self._chart, stretch=1)

        splitter.addWidget(self._detail_panel)
        splitter.setSizes([280, 720])

        outer_layout.addLayout(content_layout, stretch=1)

        # --- Status bar ---
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self._status_sensor_count = QLabel(f"{len(self._sensors)} sensors detected")
        status_bar.addPermanentWidget(self._status_sensor_count)

        if not self._sensors:
            self._detail_name_label.setText("No sensors detected")
            self._detail_temp_label.setText("N/A")

    def _setup_header(self, parent_layout: QVBoxLayout) -> None:
        """Create the system info header bar.

        Args:
            parent_layout: Layout to add the header to.
        """
        header_frame = QFrame()
        header_frame.setStyleSheet(
            f"background-color: {COLOR_PANEL}; border-bottom: 1px solid {COLOR_ACCENT};"
        )
        header_frame.setFixedHeight(50)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 4, 16, 4)
        header_layout.setSpacing(24)

        info = _get_system_info()
        header_font = QFont("Consolas", 10)
        header_font.setStyleHint(QFont.StyleHint.Monospace)

        items = [
            ("Host", info.get("hostname", "?")),
            ("OS", info.get("os", "?")),
            ("CPU", info.get("cpu_model", "?")),
            ("GPU", info.get("gpu_model", "?")),
            ("Uptime", info.get("uptime", "?")),
        ]

        for label_text, value_text in items:
            label = QLabel(f"<b>{label_text}:</b> {value_text}")
            label.setFont(header_font)
            label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; background: transparent;")
            header_layout.addWidget(label)

        header_layout.addStretch()
        parent_layout.addWidget(header_frame)

    def _setup_system_tray(self) -> None:
        """Create the system tray icon with context menu."""
        self._tray_icon = QSystemTrayIcon(self._app_icon, self)

        tray_menu = QMenu()

        show_action = QAction("Show", self)
        show_action.triggered.connect(self._show_from_tray)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)

        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.setToolTip("ThermalCore — Loading...")
        self._tray_icon.show()

    def _setup_polling(self) -> None:
        """Start a timer to refresh temperature readings."""
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._update_readings)
        self._poll_timer.start(POLL_INTERVAL_MS)
        self._update_readings()

    # --- Alert pulse animation ---
    def _setup_alert_pulse(self) -> None:
        """Start a visual pulse on the temperature label during alerts."""
        if hasattr(self, "_pulse_timer") and self._pulse_timer.isActive():
            return
        self._pulse_state = True
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._toggle_pulse)
        self._pulse_timer.start(500)

    def _stop_alert_pulse(self) -> None:
        """Stop the alert pulse animation."""
        if hasattr(self, "_pulse_timer"):
            self._pulse_timer.stop()

    def _toggle_pulse(self) -> None:
        """Toggle the pulse visual state."""
        self._pulse_state = not self._pulse_state
        if self._pulse_state:
            self._detail_temp_label.setStyleSheet(
                f"color: {COLOR_TEMP_CRITICAL}; background: transparent;"
            )
        else:
            self._detail_temp_label.setStyleSheet(
                f"color: {COLOR_WARNING}; background: transparent;"
            )

    # --- Event handlers ---

    def closeEvent(self, event: object) -> None:
        """Minimize to tray on window close instead of quitting."""
        event.ignore()
        self.hide()
        self._tray_icon.showMessage(
            "ThermalCore",
            "Running in system tray. Right-click to quit.",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def _show_from_tray(self) -> None:
        """Restore the window from system tray."""
        self.showNormal()
        self.activateWindow()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon double-click to restore window.

        Args:
            reason: The activation reason.
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _quit_app(self) -> None:
        """Fully quit the application."""
        self._tray_icon.hide()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    def _on_threshold_changed(self, value: int) -> None:
        """Update the alert threshold.

        Args:
            value: New threshold in Celsius.
        """
        self._alert_threshold = value

    def _select_widget(self, widget: SensorWidget) -> None:
        """Handle sensor card selection in the sidebar.

        Args:
            widget: The SensorWidget that was clicked.
        """
        if self._selected_widget is not None:
            self._selected_widget.setStyleSheet(
                f"background-color: {COLOR_PANEL}; border-radius: 8px;"
            )

        self._selected_widget = widget
        widget.setStyleSheet(
            f"background-color: {COLOR_ACCENT}; border-radius: 8px;"
        )
        self._detail_name_label.setText(widget.sensor.get_name())
        self._chart.highlight_sensor(widget.sensor.get_name())
        self._update_detail_display()

    def _update_readings(self) -> None:
        """Poll all sensors, update widgets, refresh chart, check alerts."""
        now = datetime.now()
        log_entry: dict[str, object] = {"timestamp": now.isoformat()}
        hottest_temp = 0.0
        hottest_name = ""

        for widget in self._sensor_widgets:
            widget.update_reading()
            sensor = widget.sensor
            temp = sensor.get_temperature()
            log_entry[sensor.get_name()] = temp
            if temp > hottest_temp:
                hottest_temp = temp
                hottest_name = sensor.get_name()

        self._temperature_log.append(log_entry)
        self._chart.update_data()
        self._update_detail_display()

        # Update tray tooltip with hottest sensor
        self._tray_icon.setToolTip(
            f"ThermalCore — {hottest_name}: {hottest_temp:.0f}°C"
        )

        # Check alert threshold
        self._check_alerts(hottest_temp, hottest_name)

    def _check_alerts(self, hottest_temp: float, hottest_name: str) -> None:
        """Check if any sensor exceeds the alert threshold.

        Args:
            hottest_temp: Highest temperature across all sensors.
            hottest_name: Name of the hottest sensor.
        """
        if hottest_temp >= self._alert_threshold:
            if not self._alert_active:
                self._alert_active = True
                self._setup_alert_pulse()
                # Desktop notification via tray
                self._tray_icon.showMessage(
                    "Temperature Alert!",
                    f"{hottest_name} reached {hottest_temp:.1f}°C "
                    f"(threshold: {self._alert_threshold}°C)",
                    QSystemTrayIcon.MessageIcon.Critical,
                    5000,
                )
        else:
            if self._alert_active:
                self._alert_active = False
                self._stop_alert_pulse()

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

        # Only set color if alert pulse is not active
        if not self._alert_active:
            color = self._get_temp_color(temp)
            self._detail_temp_label.setStyleSheet(
                f"color: {color}; background: transparent;"
            )

        readings = self._selected_widget._readings
        if readings:
            min_t = self._selected_widget._min_temp
            max_t = self._selected_widget._max_temp
            avg_t = self._selected_widget._sum_temp / len(readings)
            self._detail_stats_label.setText(
                f"Min: {min_t:.1f}°C  |  Max: {max_t:.1f}°C  |  Avg: {avg_t:.1f}°C"
            )

    def _export_csv(self) -> None:
        """Export temperature log to a CSV file."""
        if not self._temperature_log:
            return

        default_name = f"thermalcore_{datetime.now():%Y%m%d_%H%M%S}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Temperature Log", default_name, "CSV Files (*.csv)"
        )

        if not file_path:
            return

        headers = list(self._temperature_log[0].keys())
        with open(file_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(self._temperature_log)

        self.statusBar().showMessage(f"Exported {len(self._temperature_log)} records to {file_path}", 5000)

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
