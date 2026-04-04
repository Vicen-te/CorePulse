"""
Main window layout for ThermalCore v2.

HWMonitor-style tree view with expandable sections for each hardware
component. Columns: Sensor | Value | Min | Max. Lightweight and fast.
"""

# Standard library
import csv
import platform
import socket
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Third-party
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QStatusBar,
    QFrame,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
    QFileDialog,
    QSpinBox,
    QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QAction

# Local
from utils.config import (
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    WINDOW_TITLE,
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
from sensors.gpu_sensor import discover_gpu_sensors, shutdown_nvml
from sensors.poller import SensorPoller, SensorReading


def _get_system_info() -> dict[str, str]:
    """
    Gather system information for the header bar.

    Returns:
        Dictionary with hostname, os, kernel, cpu_model, gpu_model, and uptime.
    """
    info: dict[str, str] = {}
    info["hostname"] = socket.gethostname()
    info["os"] = f"{platform.system()} {platform.release()}"

    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    info["cpu_model"] = line.split(":", 1)[1].strip()
                    break
    except OSError:
        info["cpu_model"] = "Unknown CPU"

    # GPU model via pynvml (already initialized by sensor discovery)
    try:
        import pynvml
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info["gpu_model"] = pynvml.nvmlDeviceGetName(handle)
    except Exception:
        info["gpu_model"] = "No GPU detected"

    try:
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
            delta = timedelta(seconds=int(seconds))
            d, h, m = delta.days, delta.seconds // 3600, (delta.seconds % 3600) // 60
            info["uptime"] = f"{d}d {h}h {m}m"
    except OSError:
        info["uptime"] = "Unknown"

    return info


def _create_app_icon() -> QIcon:
    """Create a simple app icon."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(COLOR_WARNING))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, 56, 56)
    painter.setBrush(QColor(COLOR_BACKGROUND))
    painter.drawEllipse(14, 14, 36, 36)
    painter.setBrush(QColor(COLOR_TEMP_COOL))
    painter.drawEllipse(22, 22, 20, 20)
    painter.end()
    return QIcon(pixmap)


# Maximum temperature log entries to keep in memory
_MAX_LOG_ENTRIES: int = 36000


class MainWindow(QMainWindow):
    """
    HWMonitor-style main window with a QTreeWidget.

    Displays temperature sensors in an expandable tree grouped by
    hardware component. Columns: Sensor | Value | Min | Max.
    Background thread polls sensors; UI only updates text items.

    Attributes:
        sensors: All discovered temperature sensors.
        poller: Background polling thread.
    """

    def __init__(self) -> None:
        """Initialize the main window, discover sensors, and start polling."""
        super().__init__()

        self._cpu_sensors: list[BaseSensor] = []
        self._gpu_sensors: list[BaseSensor] = []
        self._all_sensors: list[BaseSensor] = []
        self._tree_items: dict[str, QTreeWidgetItem] = {}
        self._temperature_log: list[dict[str, object]] = []
        self._alert_threshold: int = CRITICAL_TEMP_THRESHOLD
        self._alert_active: bool = False

        self._app_icon = _create_app_icon()
        self.setWindowIcon(self._app_icon)
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.resize(900, 600)

        self._discover_sensors()
        self._setup_ui()
        self._setup_system_tray()
        self._start_polling()

    def _discover_sensors(self) -> None:
        """Find all available CPU and GPU sensors."""
        self._cpu_sensors = discover_cpu_sensors()
        self._gpu_sensors = discover_gpu_sensors()
        self._all_sensors = self._cpu_sensors + self._gpu_sensors

    def _setup_ui(self) -> None:
        """Build the main layout: header + tree + status bar."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Header bar ---
        self._setup_header(layout)

        # --- Tree widget ---
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Sensor", "Value", "Min", "Max"])
        self._tree.setColumnCount(4)
        self._tree.setRootIsDecorated(True)
        self._tree.setAnimated(False)
        self._tree.setIndentation(20)
        self._tree.setAlternatingRowColors(False)
        self._tree.setUniformRowHeights(True)

        mono_font = QFont("JetBrains Mono", 11)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self._tree.setFont(mono_font)

        # Column sizing
        header = self._tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._tree.setColumnWidth(1, 100)
        self._tree.setColumnWidth(2, 100)
        self._tree.setColumnWidth(3, 100)

        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {COLOR_BACKGROUND};
                color: {COLOR_TEXT_PRIMARY};
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border-bottom: 1px solid {COLOR_PANEL};
            }}
            QTreeWidget::item:selected {{
                background-color: {COLOR_ACCENT};
            }}
            QTreeWidget::branch {{
                background-color: {COLOR_BACKGROUND};
            }}
            QHeaderView::section {{
                background-color: {COLOR_PANEL};
                color: {COLOR_TEXT_PRIMARY};
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid {COLOR_ACCENT};
                border-right: 1px solid {COLOR_ACCENT};
                font-weight: bold;
            }}
        """)

        self._populate_tree()
        layout.addWidget(self._tree, stretch=1)

        # --- Bottom bar: controls ---
        self._setup_bottom_bar(layout)

        # --- Status bar ---
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self._status_label = QLabel(f"{len(self._all_sensors)} sensors detected")
        status_bar.addPermanentWidget(self._status_label)

    def _setup_header(self, parent_layout: QVBoxLayout) -> None:
        """Create the system info header bar."""
        header_frame = QFrame()
        header_frame.setStyleSheet(
            f"background-color: {COLOR_PANEL}; border-bottom: 1px solid {COLOR_ACCENT};"
        )
        header_frame.setFixedHeight(36)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 2, 12, 2)
        header_layout.setSpacing(20)

        info = _get_system_info()
        header_font = QFont("Consolas", 9)
        header_font.setStyleHint(QFont.StyleHint.Monospace)

        for key, value in [
            ("Host", info.get("hostname", "?")),
            ("CPU", info.get("cpu_model", "?")),
            ("GPU", info.get("gpu_model", "?")),
            ("Uptime", info.get("uptime", "?")),
        ]:
            label = QLabel(f"<b>{key}:</b> {value}")
            label.setFont(header_font)
            label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; background: transparent;")
            header_layout.addWidget(label)

        header_layout.addStretch()
        parent_layout.addWidget(header_frame)

    def _setup_bottom_bar(self, parent_layout: QVBoxLayout) -> None:
        """Create the bottom bar with alert threshold and export button."""
        bar = QFrame()
        bar.setStyleSheet(
            f"background-color: {COLOR_PANEL}; border-top: 1px solid {COLOR_ACCENT};"
        )
        bar.setFixedHeight(40)

        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(12, 4, 12, 4)
        bar_layout.setSpacing(8)

        alert_label = QLabel("Alert:")
        alert_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; background: transparent;")
        bar_layout.addWidget(alert_label)

        self._threshold_spin = QSpinBox()
        self._threshold_spin.setRange(30, 120)
        self._threshold_spin.setValue(self._alert_threshold)
        self._threshold_spin.setSuffix("°C")
        self._threshold_spin.setFixedWidth(80)
        self._threshold_spin.setStyleSheet(
            f"background-color: {COLOR_BACKGROUND}; color: {COLOR_TEXT_PRIMARY}; "
            f"border: 1px solid {COLOR_ACCENT}; border-radius: 3px; padding: 2px 6px;"
        )
        self._threshold_spin.valueChanged.connect(self._on_threshold_changed)
        bar_layout.addWidget(self._threshold_spin)

        bar_layout.addStretch()

        export_btn = QPushButton("Export CSV")
        export_btn.setFixedWidth(100)
        export_btn.setStyleSheet(
            f"background-color: {COLOR_ACCENT}; color: {COLOR_TEXT_PRIMARY}; "
            f"border: none; border-radius: 3px; padding: 4px 12px; font-weight: bold;"
        )
        export_btn.clicked.connect(self._export_csv)
        bar_layout.addWidget(export_btn)

        parent_layout.addWidget(bar)

    def _populate_tree(self) -> None:
        """Create the tree structure with hardware groups and sensor items."""
        self._tree.clear()
        self._tree_items.clear()

        # Detect NVMe/disk sensors from psutil
        import psutil
        all_temps = psutil.sensors_temperatures()
        nvme_entries = all_temps.get("nvme", [])

        # --- CPU group ---
        if self._cpu_sensors:
            cpu_info = _get_system_info().get("cpu_model", "CPU")
            cpu_group = QTreeWidgetItem(self._tree, [f"CPU — {cpu_info}"])
            cpu_group.setFlags(cpu_group.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            bold_font = QFont("JetBrains Mono", 11, QFont.Weight.Bold)
            cpu_group.setFont(0, bold_font)
            cpu_group.setExpanded(True)

            for sensor in self._cpu_sensors:
                name = sensor.get_name()
                item = QTreeWidgetItem(cpu_group, [name, "--", "--", "--"])
                item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
                item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
                item.setTextAlignment(3, Qt.AlignmentFlag.AlignCenter)
                self._tree_items[name] = item

        # --- GPU group ---
        gpu_label = "No GPU detected"
        if self._gpu_sensors:
            gpu_label = self._gpu_sensors[0].get_name().replace("GPU ", "")

        gpu_group = QTreeWidgetItem(self._tree, [f"GPU — {gpu_label}"])
        gpu_group.setFlags(gpu_group.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        bold_font = QFont("JetBrains Mono", 11, QFont.Weight.Bold)
        gpu_group.setFont(0, bold_font)
        gpu_group.setExpanded(True)

        if self._gpu_sensors:
            for sensor in self._gpu_sensors:
                name = sensor.get_name()
                item = QTreeWidgetItem(gpu_group, ["GPU Temperature", "--", "--", "--"])
                item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
                item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
                item.setTextAlignment(3, Qt.AlignmentFlag.AlignCenter)
                self._tree_items[name] = item
        else:
            no_gpu = QTreeWidgetItem(gpu_group, ["No GPU detected", "", "", ""])
            no_gpu.setForeground(0, QColor(COLOR_TEXT_SECONDARY))

        # --- Disks group (NVMe from psutil) ---
        if nvme_entries:
            disk_group = QTreeWidgetItem(self._tree, ["Disks"])
            disk_group.setFlags(disk_group.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            bold_font = QFont("JetBrains Mono", 11, QFont.Weight.Bold)
            disk_group.setFont(0, bold_font)
            disk_group.setExpanded(True)

            for entry in nvme_entries:
                label = entry.label if entry.label else "NVMe"
                display_name = f"NVMe {label}"
                item = QTreeWidgetItem(disk_group, [display_name, "--", "--", "--"])
                item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
                item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
                item.setTextAlignment(3, Qt.AlignmentFlag.AlignCenter)
                # Store NVMe readings with a unique key
                self._tree_items[f"nvme_{label}"] = item

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

    def _start_polling(self) -> None:
        """Start the background sensor polling thread."""
        self._poller = SensorPoller(self._all_sensors)
        self._poller.readings_updated.connect(self._on_readings_updated)
        self._poller.start()

    def _on_readings_updated(self, readings: dict[str, SensorReading]) -> None:
        """Handle new readings from the background thread.

        Args:
            readings: Dict mapping sensor name to its SensorReading.
        """
        hottest_temp = 0.0
        hottest_name = ""
        log_entry: dict[str, object] = {"timestamp": datetime.now().isoformat()}

        for name, reading in readings.items():
            log_entry[name] = reading.current

            if reading.current > hottest_temp:
                hottest_temp = reading.current
                hottest_name = name

            item = self._tree_items.get(name)
            if item is None:
                continue

            if reading.current <= 0:
                continue

            # Update text
            item.setText(1, f"{reading.current:.1f}°C")
            item.setText(2, f"{reading.min_temp:.1f}°C")
            item.setText(3, f"{reading.max_temp:.1f}°C")

            # Color the value column
            color = QColor(self._get_temp_color(reading.current))
            item.setForeground(1, color)

        # Also update NVMe sensors directly from psutil
        self._update_nvme_readings(log_entry)

        # Cap temperature log
        if len(self._temperature_log) < _MAX_LOG_ENTRIES:
            self._temperature_log.append(log_entry)

        # Update tray tooltip
        self._tray_icon.setToolTip(f"ThermalCore — {hottest_name}: {hottest_temp:.0f}°C")

        # Check alerts
        self._check_alerts(hottest_temp, hottest_name)

    def _update_nvme_readings(self, log_entry: dict[str, object]) -> None:
        """Update NVMe disk temperature readings from psutil.

        Args:
            log_entry: Log entry dict to append NVMe readings to.
        """
        import psutil
        all_temps = psutil.sensors_temperatures()
        nvme_entries = all_temps.get("nvme", [])

        for entry in nvme_entries:
            label = entry.label if entry.label else "NVMe"
            key = f"nvme_{label}"
            item = self._tree_items.get(key)
            if item is None:
                continue

            temp = entry.current
            log_entry[key] = temp

            if temp <= 0:
                continue

            # Track min/max via item data
            stored_min = item.data(2, Qt.ItemDataRole.UserRole)
            stored_max = item.data(3, Qt.ItemDataRole.UserRole)
            min_val = min(stored_min, temp) if stored_min is not None else temp
            max_val = max(stored_max, temp) if stored_max is not None else temp
            item.setData(2, Qt.ItemDataRole.UserRole, min_val)
            item.setData(3, Qt.ItemDataRole.UserRole, max_val)

            item.setText(1, f"{temp:.1f}°C")
            item.setText(2, f"{min_val:.1f}°C")
            item.setText(3, f"{max_val:.1f}°C")

            color = QColor(self._get_temp_color(temp))
            item.setForeground(1, color)

    def _check_alerts(self, hottest_temp: float, hottest_name: str) -> None:
        """Check if any sensor exceeds the alert threshold."""
        if hottest_temp >= self._alert_threshold:
            if not self._alert_active:
                self._alert_active = True
                self._tray_icon.showMessage(
                    "Temperature Alert!",
                    f"{hottest_name} reached {hottest_temp:.1f}°C "
                    f"(threshold: {self._alert_threshold}°C)",
                    QSystemTrayIcon.MessageIcon.Critical,
                    5000,
                )
        else:
            self._alert_active = False

    def _on_threshold_changed(self, value: int) -> None:
        """Update the alert threshold."""
        self._alert_threshold = value

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

        self.statusBar().showMessage(
            f"Exported {len(self._temperature_log)} records to {file_path}", 5000
        )

    # --- System tray ---

    def closeEvent(self, event: object) -> None:
        """Minimize to tray on window close."""
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
        """Handle tray icon double-click to restore window."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _quit_app(self) -> None:
        """Fully quit the application."""
        self._poller.stop()
        shutdown_nvml()
        self._tray_icon.hide()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    @staticmethod
    def _get_temp_color(temp: float) -> str:
        """Return the appropriate color for a temperature value."""
        if temp < TEMP_THRESHOLD_LOW:
            return COLOR_TEMP_COOL
        elif temp < TEMP_THRESHOLD_MEDIUM:
            return COLOR_TEMP_WARM
        elif temp < TEMP_THRESHOLD_HIGH:
            return COLOR_TEMP_HOT
        else:
            return COLOR_TEMP_CRITICAL
