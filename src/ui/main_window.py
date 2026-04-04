"""
Main window layout for ThermalCore.

Tree view with 3-level hierarchy: Hardware → Sensor Type → Individual Sensor.
"""

# Standard library
import csv
import platform
import socket
from collections import OrderedDict
from datetime import datetime, timedelta

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
    QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QAction, QBrush

# Local
from utils.config import (
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    WINDOW_TITLE,
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
    COLOR_BACKGROUND,
    COLOR_WARNING,
)
from sensors.base_sensor import BaseSensor, SensorType, SENSOR_FORMATS, format_value
from sensors.cpu_sensor import discover_cpu_sensors
from sensors.gpu_sensor import discover_gpu_sensors, shutdown_nvml
from sensors.system_sensor import discover_memory_sensors, discover_storage_sensors
from sensors.poller import SensorPoller, SensorReading

# Hardware group display order
_HW_ORDER: list[str] = ["CPU", "GPU", "Memory", "Storage"]

# Type group display order within each hardware group
_TYPE_ORDER: list[str] = [
    "Temperatures", "Clocks", "Load", "Power", "Fans", "Voltages", "Data", "Usage", "Throughput",
]

# Maximum temperature log entries
_MAX_LOG_ENTRIES: int = 36000


def _get_system_info() -> dict[str, str]:
    """Gather system information for the header bar."""
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
        info["cpu_model"] = "Unknown"

    try:
        from sensors.gpu_sensor import _ensure_nvml
        import pynvml
        _ensure_nvml()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info["gpu_model"] = pynvml.nvmlDeviceGetName(handle)
    except Exception:
        info["gpu_model"] = "No GPU"

    try:
        with open("/proc/uptime") as f:
            secs = float(f.read().split()[0])
            delta = timedelta(seconds=int(secs))
            d, h, m = delta.days, delta.seconds // 3600, (delta.seconds % 3600) // 60
            info["uptime"] = f"{d}d {h}h {m}m"
    except OSError:
        info["uptime"] = "?"

    return info


def _create_branch_icons() -> tuple[str, str]:
    """Create triangle arrow icons for tree branches and return temp file paths."""
    import tempfile, os
    arrow_size = 12
    color = QColor(COLOR_TEXT_SECONDARY)

    # Right-pointing triangle (collapsed)
    closed_pix = QPixmap(arrow_size, arrow_size)
    closed_pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(closed_pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(color)
    p.setPen(Qt.PenStyle.NoPen)
    from PySide6.QtGui import QPolygonF
    from PySide6.QtCore import QPointF
    p.drawPolygon(QPolygonF([
        QPointF(3, 1), QPointF(10, 6), QPointF(3, 11),
    ]))
    p.end()

    # Down-pointing triangle (expanded)
    open_pix = QPixmap(arrow_size, arrow_size)
    open_pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(open_pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(color)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygonF([
        QPointF(1, 3), QPointF(11, 3), QPointF(6, 10),
    ]))
    p.end()

    tmp_dir = tempfile.mkdtemp(prefix="thermalcore_")
    closed_path = os.path.join(tmp_dir, "arrow_closed.png")
    open_path = os.path.join(tmp_dir, "arrow_open.png")
    closed_pix.save(closed_path)
    open_pix.save(open_path)
    return closed_path, open_path


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


class MainWindow(QMainWindow):
    """
    Main window with hardware monitoring tree view.

    3-level QTreeWidget: Hardware → Sensor Type → Sensor.
    Background thread polls; UI only updates text.
    """

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()

        self._all_sensors: list[BaseSensor] = []
        self._sensor_items: dict[str, QTreeWidgetItem] = {}
        self._sensor_map: dict[str, BaseSensor] = {}
        self._active_sensors: set[str] = set()
        self._poll_count: int = 0
        self._temperature_log: list[dict[str, object]] = []
        self._alert_thresholds: dict[str, float] = {}
        self._triggered_alerts: set[str] = set()
        self._sys_info = _get_system_info()

        self._app_icon = _create_app_icon()
        self.setWindowIcon(self._app_icon)
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.resize(750, 650)

        self._discover_sensors()
        self._setup_ui()
        self._setup_system_tray()
        self._start_polling()

    def _discover_sensors(self) -> None:
        """Find all available sensors."""
        self._all_sensors.extend(discover_cpu_sensors())
        self._all_sensors.extend(discover_gpu_sensors())
        self._all_sensors.extend(discover_memory_sensors())
        self._all_sensors.extend(discover_storage_sensors())

    # --- UI setup ---

    def _setup_ui(self) -> None:
        """Build the main layout."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._setup_header(layout)
        self._setup_tree(layout)
        self._setup_bottom_bar(layout)

        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self._status_label = QLabel(f"{len(self._all_sensors)} sensors")
        status_bar.addPermanentWidget(self._status_label)

    def _setup_header(self, parent: QVBoxLayout) -> None:
        """Create the system info header bar."""
        header = QFrame()
        header.setStyleSheet(
            f"background-color: {COLOR_PANEL}; border-bottom: 1px solid {COLOR_ACCENT};"
        )
        header.setFixedHeight(32)

        hl = QHBoxLayout(header)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(16)

        hfont = QFont("Consolas", 9)
        hfont.setStyleHint(QFont.StyleHint.Monospace)

        for key, val in [
            ("Host", self._sys_info.get("hostname", "?")),
            ("CPU", self._sys_info.get("cpu_model", "?")),
            ("GPU", self._sys_info.get("gpu_model", "?")),
            ("Uptime", self._sys_info.get("uptime", "?")),
        ]:
            lbl = QLabel(f"<b>{key}:</b> {val}")
            lbl.setFont(hfont)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; background: transparent;")
            hl.addWidget(lbl)
        hl.addStretch()
        parent.addWidget(header)

    def _setup_tree(self, parent: QVBoxLayout) -> None:
        """Create and populate the QTreeWidget."""
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Sensor", "Value", "Min", "Max", "Alert"])
        self._tree.setColumnCount(5)
        self._tree.setRootIsDecorated(True)
        self._tree.setAnimated(False)
        self._tree.setIndentation(20)
        self._tree.setUniformRowHeights(True)

        mono = QFont("JetBrains Mono", 10)
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self._tree.setFont(mono)

        hdr = self._tree.header()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3, 4):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self._tree.setColumnWidth(col, 110)

        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        closed_icon, open_icon = _create_branch_icons()

        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {COLOR_BACKGROUND};
                color: {COLOR_TEXT_PRIMARY};
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 3px 6px;
            }}
            QTreeWidget::item:selected {{
                background-color: {COLOR_ACCENT};
            }}
            QTreeWidget::branch {{
                background-color: {COLOR_BACKGROUND};
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                image: url({closed_icon});
            }}
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                image: url({open_icon});
            }}
            QHeaderView::section {{
                background-color: {COLOR_PANEL};
                color: {COLOR_TEXT_PRIMARY};
                padding: 5px 8px;
                border: none;
                border-bottom: 2px solid {COLOR_ACCENT};
                border-right: 1px solid {COLOR_ACCENT};
                font-weight: bold;
                font-size: 11px;
            }}
        """)

        self._populate_tree()
        parent.addWidget(self._tree, stretch=1)

    def _populate_tree(self) -> None:
        """Build the 3-level tree: Hardware → Type → Sensor."""
        self._tree.clear()
        self._sensor_items.clear()
        self._sensor_map.clear()

        # Group sensors: hardware_group → type_group → [sensors]
        grouped: dict[str, dict[str, list[BaseSensor]]] = OrderedDict()
        for hw in _HW_ORDER:
            grouped[hw] = OrderedDict()

        for sensor in self._all_sensors:
            hw = sensor.get_hardware_group()
            tg = sensor.get_type_group()
            if hw not in grouped:
                grouped[hw] = OrderedDict()
            if tg not in grouped[hw]:
                grouped[hw][tg] = []
            grouped[hw][tg].append(sensor)

        # Sort type groups within each hardware group
        for hw in grouped:
            sorted_types = OrderedDict()
            for t in _TYPE_ORDER:
                if t in grouped[hw]:
                    sorted_types[t] = grouped[hw][t]
            for t in grouped[hw]:
                if t not in sorted_types:
                    sorted_types[t] = grouped[hw][t]
            grouped[hw] = sorted_types

        bold = QFont("JetBrains Mono", 10, QFont.Weight.Bold)
        type_font = QFont("JetBrains Mono", 10)
        type_font.setItalic(False)
        secondary_brush = QBrush(QColor(COLOR_TEXT_SECONDARY))

        for hw_name, type_groups in grouped.items():
            if not type_groups:
                continue

            # Hardware display name with model info
            hw_display = self._hw_display_name(hw_name)
            hw_item = QTreeWidgetItem(self._tree, [hw_display, "", "", "", ""])
            hw_item.setFont(0, bold)
            hw_item.setFlags(hw_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            hw_item.setExpanded(True)

            for type_name, sensors in type_groups.items():
                if not sensors:
                    continue

                type_item = QTreeWidgetItem(hw_item, [type_name, "", "", "", ""])
                type_item.setFont(0, type_font)
                type_item.setForeground(0, secondary_brush)
                type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                type_item.setExpanded(True)

                for sensor in sensors:
                    key = f"{hw_name}|{type_name}|{sensor.get_name()}"
                    item = QTreeWidgetItem(type_item, [sensor.get_name(), "--", "--", "--", ""])
                    for col in (1, 2, 3, 4):
                        item.setTextAlignment(col, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self._sensor_items[key] = item
                    self._sensor_map[key] = sensor

    def _hw_display_name(self, hw_name: str) -> str:
        """Build the display name for a hardware group node."""
        if hw_name == "CPU":
            model = self._sys_info.get("cpu_model", "")
            return f"CPU — {model}" if model else "CPU"
        elif hw_name == "GPU":
            model = self._sys_info.get("gpu_model", "")
            return f"GPU — {model}" if model else "GPU"
        elif hw_name == "Memory":
            import psutil
            total = psutil.virtual_memory().total / (1024 ** 3)
            return f"Memory — {total:.0f} GB"
        elif hw_name == "Storage":
            return "Storage"
        return hw_name

    def _setup_bottom_bar(self, parent: QVBoxLayout) -> None:
        """Create the bottom bar with export button."""
        bar = QFrame()
        bar.setStyleSheet(
            f"background-color: {COLOR_PANEL}; border-top: 1px solid {COLOR_ACCENT};"
        )
        bar.setFixedHeight(36)

        bl = QHBoxLayout(bar)
        bl.setContentsMargins(10, 2, 10, 2)
        bl.setSpacing(6)

        hint_lbl = QLabel("Double-click Alert column to set threshold")
        hint_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; background: transparent;")
        bl.addWidget(hint_lbl)

        bl.addStretch()

        export_btn = QPushButton("Export CSV")
        export_btn.setFixedWidth(90)
        export_btn.setStyleSheet(
            f"background-color: {COLOR_ACCENT}; color: {COLOR_TEXT_PRIMARY}; "
            f"border: none; border-radius: 3px; padding: 3px 10px; font-weight: bold;"
        )
        export_btn.clicked.connect(self._export_csv)
        bl.addWidget(export_btn)

        parent.addWidget(bar)

    # --- Polling ---

    def _start_polling(self) -> None:
        """Start the background sensor polling thread."""
        self._poller = SensorPoller(self._all_sensors)
        self._poller.readings_updated.connect(self._on_readings_updated)
        self._poller.start()

    def _on_readings_updated(self, readings: dict[str, SensorReading]) -> None:
        """Handle new readings from the background thread."""
        self._poll_count += 1
        hottest_temp = 0.0
        hottest_name = ""
        log_entry: dict[str, object] = {"timestamp": datetime.now().isoformat()}

        for key, reading in readings.items():
            log_entry[reading.name] = reading.current

            # Track hottest temperature sensor for alerts
            if reading.sensor_type == SensorType.TEMPERATURE and reading.current > hottest_temp:
                hottest_temp = reading.current
                hottest_name = reading.name.split("|")[-1] if "|" in reading.name else reading.name

            item = self._sensor_items.get(key)
            if item is None:
                continue

            has_data = reading.current > 0 or reading.sensor_type in (
                SensorType.LOAD, SensorType.FAN, SensorType.POWER,
            )
            if has_data:
                self._active_sensors.add(key)

            if not has_data:
                continue

            # Format values with proper units (use sensor's custom format if available)
            sensor_obj = self._sensor_map.get(key)
            if sensor_obj is not None:
                val_str = sensor_obj.format_reading(reading.current)
                min_str = sensor_obj.format_reading(reading.min_val) if reading.min_val != float("inf") else "--"
                max_str = sensor_obj.format_reading(reading.max_val) if reading.max_val != float("-inf") else "--"
            else:
                val_str = format_value(reading.current, reading.sensor_type)
                min_str = format_value(reading.min_val, reading.sensor_type) if reading.min_val != float("inf") else "--"
                max_str = format_value(reading.max_val, reading.sensor_type) if reading.max_val != float("-inf") else "--"

            item.setText(1, val_str)
            item.setText(2, min_str)
            item.setText(3, max_str)

            # Color the value column for temperatures
            if reading.sensor_type == SensorType.TEMPERATURE:
                color = QColor(self._get_temp_color(reading.current))
                item.setForeground(1, color)

        # After 3 polls, hide sensors that never reported data
        if self._poll_count == 3:
            self._hide_inactive_sensors()

        if self._poll_count == 3:
            count = sum(1 for k in self._sensor_items if k in self._active_sensors)
            self._status_label.setText(f"{count} sensors")

        if len(self._temperature_log) < _MAX_LOG_ENTRIES:
            self._temperature_log.append(log_entry)

        self._tray_icon.setToolTip(f"ThermalCore — {hottest_name}: {hottest_temp:.0f}°C")
        self._check_alerts(readings)

    def _hide_inactive_sensors(self) -> None:
        """Hide sensors that never reported data and empty type groups."""
        for key, item in self._sensor_items.items():
            if key not in self._active_sensors:
                item.setHidden(True)

        # Hide type group nodes with all children hidden
        root = self._tree.invisibleRootItem()
        for hw_idx in range(root.childCount()):
            hw_item = root.child(hw_idx)
            hw_has_visible = False
            for tg_idx in range(hw_item.childCount()):
                tg_item = hw_item.child(tg_idx)
                visible_children = sum(
                    1 for i in range(tg_item.childCount())
                    if not tg_item.child(i).isHidden()
                )
                if visible_children == 0:
                    tg_item.setHidden(True)
                else:
                    hw_has_visible = True
            if not hw_has_visible:
                hw_item.setHidden(True)

    # --- Per-metric alerts ---

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on Alert column to set/clear threshold."""
        if column != 4:
            return

        # Find the sensor key for this item
        key = None
        for k, v in self._sensor_items.items():
            if v is item:
                key = k
                break
        if key is None:
            return

        from PySide6.QtWidgets import QInputDialog
        sensor_obj = self._sensor_map.get(key)
        if sensor_obj is None:
            return

        st = sensor_obj.get_sensor_type()
        _, unit = SENSOR_FORMATS.get(st, ("{:.1f}", ""))
        current = self._alert_thresholds.get(key)
        label = f"Alert threshold for {sensor_obj.get_name()} ({unit.strip()}):"

        if current is not None:
            label += f"\nCurrent: {current}{unit}\n(Enter 0 to clear)"

        value, ok = QInputDialog.getDouble(
            self, "Set Alert", label,
            current if current is not None else 0.0,
            0, 100000, 1,
        )
        if not ok:
            return

        if value == 0 and current is not None:
            del self._alert_thresholds[key]
            self._triggered_alerts.discard(key)
            item.setText(4, "")
            item.setForeground(4, QBrush(QColor(COLOR_TEXT_PRIMARY)))
        elif value > 0:
            self._alert_thresholds[key] = value
            fmt, unit = SENSOR_FORMATS.get(st, ("{:.1f}", ""))
            item.setText(4, fmt.format(value) + unit)
            item.setForeground(4, QBrush(QColor(COLOR_TEXT_SECONDARY)))

    def _check_alerts(self, readings: dict[str, "SensorReading"]) -> None:
        """Check per-sensor alert thresholds."""
        for key, threshold in self._alert_thresholds.items():
            reading = readings.get(key)
            if reading is None:
                continue

            if reading.current >= threshold:
                if key not in self._triggered_alerts:
                    self._triggered_alerts.add(key)
                    sensor_name = reading.name.split("|")[-1] if "|" in reading.name else reading.name
                    st = reading.sensor_type
                    fmt, unit = SENSOR_FORMATS.get(st, ("{:.1f}", ""))
                    val_str = fmt.format(reading.current) + unit
                    thr_str = fmt.format(threshold) + unit
                    self._tray_icon.showMessage(
                        "Alert!",
                        f"{sensor_name}: {val_str} (threshold: {thr_str})",
                        QSystemTrayIcon.MessageIcon.Critical, 5000,
                    )
                # Color the alert cell red when exceeded
                item = self._sensor_items.get(key)
                if item:
                    item.setForeground(4, QBrush(QColor(COLOR_WARNING)))
            else:
                self._triggered_alerts.discard(key)
                item = self._sensor_items.get(key)
                if item and key in self._alert_thresholds:
                    item.setForeground(4, QBrush(QColor(COLOR_TEXT_SECONDARY)))

    # --- CSV export ---

    def _export_csv(self) -> None:
        """Export temperature log to CSV."""
        if not self._temperature_log:
            return

        default_name = f"thermalcore_{datetime.now():%Y%m%d_%H%M%S}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export", default_name, "CSV (*.csv)")
        if not path:
            return

        headers = list(self._temperature_log[0].keys())
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            w.writerows(self._temperature_log)

        self.statusBar().showMessage(f"Exported {len(self._temperature_log)} records", 5000)

    # --- System tray ---

    def _setup_system_tray(self) -> None:
        """Create system tray icon."""
        self._tray_icon = QSystemTrayIcon(self._app_icon, self)
        menu = QMenu()

        show = QAction("Show", self)
        show.triggered.connect(self._show_from_tray)
        menu.addAction(show)
        menu.addSeparator()
        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(self._quit_app)
        menu.addAction(quit_act)

        self._tray_icon.setContextMenu(menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.setToolTip("ThermalCore — Loading...")
        self._tray_icon.show()

    def closeEvent(self, event: object) -> None:
        """Close the application normally."""
        self._quit_app()
        event.accept()

    def _show_from_tray(self) -> None:
        """Restore window."""
        self.showNormal()
        self.activateWindow()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray double-click."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _quit_app(self) -> None:
        """Quit the application."""
        self._poller.stop()
        shutdown_nvml()
        self._tray_icon.hide()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    @staticmethod
    def _get_temp_color(temp: float) -> str:
        """Return color for a temperature value."""
        if temp < TEMP_THRESHOLD_LOW:
            return COLOR_TEMP_COOL
        elif temp < TEMP_THRESHOLD_MEDIUM:
            return COLOR_TEMP_WARM
        elif temp < TEMP_THRESHOLD_HIGH:
            return COLOR_TEMP_HOT
        else:
            return COLOR_TEMP_CRITICAL
