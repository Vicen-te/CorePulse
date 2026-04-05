"""
Main window layout for CorePulse.

Tree view with 3-level hierarchy: Hardware -> Sensor Type -> Individual Sensor.
"""

# Standard library
import csv
from collections import OrderedDict, deque
from datetime import datetime

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
    QComboBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QAction, QBrush

# Local
import utils.config as cfg
from utils.config import (
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    WINDOW_TITLE,
    TEMP_THRESHOLD_LOW,
    TEMP_THRESHOLD_MEDIUM,
    TEMP_THRESHOLD_HIGH,
)
from sensors.base_sensor import BaseSensor, SensorType, SENSOR_FORMATS, format_value
from sensors.cpu_sensor import discover_cpu_sensors
from sensors.gpu_sensor import discover_gpu_sensors, shutdown_nvml
from sensors.system_sensor import discover_memory_sensors, discover_storage_sensors
from sensors.poller import SensorPoller, SensorReading
from utils.ipc import AlertBroadcaster
from ui.icons import create_app_icon, create_branch_icons
from ui.system_info import get_system_info
from ui.theme_watcher import ThemeWatcher

# Hardware group display order
_HW_ORDER: list[str] = ["CPU", "GPU", "Memory", "Storage"]

# Type group display order within each hardware group
_TYPE_ORDER: list[str] = [
    "Temperatures", "Clocks", "Load", "Power", "Fans",
    "Voltages", "Data", "Usage", "Throughput",
]

# Maximum temperature log entries
_MAX_LOG_ENTRIES: int = 36000


class MainWindow(QMainWindow):
    """
    Main window with hardware monitoring tree view.

    3-level QTreeWidget: Hardware -> Sensor Type -> Sensor.
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
        self._log_keys: list[str] = []
        self._log_data: deque[tuple] = deque(maxlen=_MAX_LOG_ENTRIES)
        self._alert_thresholds: dict[str, float] = {}
        self._triggered_alerts: set[str] = set()
        self._sys_info = get_system_info()

        self._app_icon = create_app_icon()
        self.setWindowIcon(self._app_icon)
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.resize(750, 650)

        self._is_dark: bool = cfg.detect_dark_mode()
        self._broadcaster = AlertBroadcaster()
        self._broadcaster.start()
        self._discover_sensors()
        self._setup_ui()
        self._setup_system_tray()
        self._start_polling()
        self._start_theme_watcher()

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
        self._header = header = QFrame()
        header.setStyleSheet(
            f"background-color: {cfg.COLOR_PANEL}; border-bottom: 1px solid {cfg.COLOR_ACCENT};"
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
            lbl.setStyleSheet(f"color: {cfg.COLOR_TEXT_SECONDARY}; background: transparent;")
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

        closed_icon, open_icon = create_branch_icons()
        self._tree.setStyleSheet(self._build_tree_qss(closed_icon, open_icon))

        self._populate_tree()
        parent.addWidget(self._tree, stretch=1)

    @staticmethod
    def _build_tree_qss(closed_icon: str, open_icon: str) -> str:
        """Build QSS for the tree widget using current theme colors."""
        return f"""
            QTreeWidget {{
                background-color: {cfg.COLOR_BACKGROUND};
                color: {cfg.COLOR_TEXT_PRIMARY};
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 3px 6px;
            }}
            QTreeWidget::item:selected {{
                background-color: {cfg.COLOR_ACCENT};
            }}
            QTreeWidget::branch {{
                background-color: {cfg.COLOR_BACKGROUND};
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
                background-color: {cfg.COLOR_PANEL};
                color: {cfg.COLOR_TEXT_PRIMARY};
                padding: 5px 8px;
                border: none;
                border-bottom: 2px solid {cfg.COLOR_ACCENT};
                border-right: 1px solid {cfg.COLOR_ACCENT};
                font-weight: bold;
                font-size: 11px;
            }}
        """

    def _populate_tree(self) -> None:
        """Build the 3-level tree: Hardware -> Type -> Sensor."""
        self._tree.clear()
        self._sensor_items.clear()
        self._sensor_map.clear()

        # Group sensors: hardware_group -> type_group -> [sensors]
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
        secondary_brush = QBrush(QColor(cfg.COLOR_TEXT_SECONDARY))

        for hw_name, type_groups in grouped.items():
            if not type_groups:
                continue

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
        """Create the bottom bar with action buttons."""
        self._bottom_bar = bar = QFrame()
        bar.setStyleSheet(
            f"background-color: {cfg.COLOR_PANEL}; border-top: 1px solid {cfg.COLOR_ACCENT};"
        )
        bar.setFixedHeight(36)

        bl = QHBoxLayout(bar)
        bl.setContentsMargins(10, 2, 10, 2)
        bl.setSpacing(6)

        hint_lbl = QLabel("Double-click Alert column to set threshold")
        hint_lbl.setStyleSheet(f"color: {cfg.COLOR_TEXT_SECONDARY}; background: transparent;")
        bl.addWidget(hint_lbl)

        bl.addStretch()

        combo_style = (
            f"background-color: {cfg.COLOR_PANEL}; color: {cfg.COLOR_TEXT_PRIMARY}; "
            f"border: 1px solid {cfg.COLOR_ACCENT}; border-radius: 3px; padding: 2px 6px;"
        )
        btn_style_secondary = (
            f"background-color: transparent; color: {cfg.COLOR_TEXT_SECONDARY}; "
            f"border: 1px solid {cfg.COLOR_ACCENT}; border-radius: 3px; padding: 3px 10px;"
        )
        btn_style_primary = (
            f"background-color: {cfg.COLOR_ACCENT}; color: {cfg.COLOR_TEXT_PRIMARY}; "
            f"border: none; border-radius: 3px; padding: 3px 10px; font-weight: bold;"
        )

        self._rate_combo = QComboBox()
        self._rate_combo.addItem("0.5s", 500)
        self._rate_combo.addItem("1s", 1000)
        self._rate_combo.addItem("2s", 2000)
        self._rate_combo.addItem("4s", 4000)
        self._rate_combo.setCurrentIndex(1)
        self._rate_combo.setMinimumWidth(70)
        self._rate_combo.setStyleSheet(combo_style)
        self._rate_combo.setToolTip("Update rate")
        self._rate_combo.currentIndexChanged.connect(self._on_rate_changed)
        bl.addWidget(self._rate_combo)

        self._reset_minmax_btn = QPushButton("Reset Min/Max")
        self._reset_minmax_btn.setStyleSheet(btn_style_secondary)
        self._reset_minmax_btn.clicked.connect(self._reset_min_max)
        bl.addWidget(self._reset_minmax_btn)

        self._clear_alerts_btn = QPushButton("Clear Alerts")
        self._clear_alerts_btn.setStyleSheet(btn_style_secondary)
        self._clear_alerts_btn.clicked.connect(self._clear_alerts)
        bl.addWidget(self._clear_alerts_btn)

        self._export_btn = QPushButton("Export CSV")
        self._export_btn.setStyleSheet(btn_style_primary)
        bl.addWidget(self._export_btn)
        self._export_btn.clicked.connect(self._export_csv)

        parent.addWidget(bar)

    def _on_rate_changed(self, index: int) -> None:
        """Handle update rate combobox change."""
        ms = self._rate_combo.currentData()
        self._poller.set_interval(ms)
        self.statusBar().showMessage(f"Update rate: {self._rate_combo.currentText()}", 3000)

    # --- Polling ---

    def _start_polling(self) -> None:
        """Start the background sensor polling thread."""
        self._poller = SensorPoller(self._all_sensors)
        self._poller.readings_updated.connect(self._on_readings_updated)
        self._poller.start()

    def _start_theme_watcher(self) -> None:
        """Listen for system theme changes via DBus freedesktop portal."""
        self._theme_watcher = ThemeWatcher(self)
        self._theme_watcher.theme_changed.connect(self._on_theme_changed)
        self._theme_watcher.start()

    def _on_theme_changed(self, is_dark: bool) -> None:
        """Handle system theme change."""
        if is_dark == self._is_dark:
            return
        self._is_dark = is_dark
        palette = cfg.DARK_PALETTE if is_dark else cfg.LIGHT_PALETTE
        cfg.apply_palette(palette)

        from ui.styles import build_qss
        from PySide6.QtWidgets import QApplication
        QApplication.instance().setStyleSheet(build_qss(palette))
        self._apply_theme()

    def _apply_theme(self) -> None:
        """Re-apply inline styles after a theme switch."""
        self._header.setStyleSheet(
            f"background-color: {cfg.COLOR_PANEL}; border-bottom: 1px solid {cfg.COLOR_ACCENT};"
        )
        for lbl in self._header.findChildren(QLabel):
            lbl.setStyleSheet(f"color: {cfg.COLOR_TEXT_SECONDARY}; background: transparent;")

        closed_icon, open_icon = create_branch_icons()
        self._tree.setStyleSheet(self._build_tree_qss(closed_icon, open_icon))

        self._bottom_bar.setStyleSheet(
            f"background-color: {cfg.COLOR_PANEL}; border-top: 1px solid {cfg.COLOR_ACCENT};"
        )
        btn_style_secondary = (
            f"background-color: transparent; color: {cfg.COLOR_TEXT_SECONDARY}; "
            f"border: 1px solid {cfg.COLOR_ACCENT}; border-radius: 3px; padding: 3px 10px;"
        )
        self._rate_combo.setStyleSheet(
            f"background-color: {cfg.COLOR_PANEL}; color: {cfg.COLOR_TEXT_PRIMARY}; "
            f"border: 1px solid {cfg.COLOR_ACCENT}; border-radius: 3px; padding: 2px 6px;"
        )
        self._reset_minmax_btn.setStyleSheet(btn_style_secondary)
        self._clear_alerts_btn.setStyleSheet(btn_style_secondary)
        self._export_btn.setStyleSheet(
            f"background-color: {cfg.COLOR_ACCENT}; color: {cfg.COLOR_TEXT_PRIMARY}; "
            f"border: none; border-radius: 3px; padding: 3px 10px; font-weight: bold;"
        )

        secondary_brush = QBrush(QColor(cfg.COLOR_TEXT_SECONDARY))
        root = self._tree.invisibleRootItem()
        for hw_i in range(root.childCount()):
            hw_item = root.child(hw_i)
            for tg_i in range(hw_item.childCount()):
                tg_item = hw_item.child(tg_i)
                tg_item.setForeground(0, secondary_brush)

    def _on_readings_updated(self, readings: dict[str, SensorReading]) -> None:
        """Handle new readings from the background thread."""
        self._poll_count += 1
        hottest_temp = 0.0
        hottest_name = ""

        # Build log key order on first cycle
        if not self._log_keys:
            self._log_keys = list(readings.keys())

        # Local refs for tight loop
        sensor_items = self._sensor_items
        sensor_map = self._sensor_map
        active = self._active_sensors
        is_first_pass = self._poll_count <= 3
        _TEMP = SensorType.TEMPERATURE
        _TRACK = (SensorType.LOAD, SensorType.FAN, SensorType.POWER)
        _INF = float("inf")
        _NINF = float("-inf")
        values = []
        vappend = values.append

        for key, reading in readings.items():
            cur = reading.current
            vappend(cur)

            if reading.sensor_type is _TEMP and cur > hottest_temp:
                hottest_temp = cur
                hottest_name = key.rsplit("|", 1)[-1]

            item = sensor_items.get(key)
            if item is None:
                continue

            if is_first_pass:
                has_data = cur > 0 or reading.sensor_type in _TRACK
                if has_data:
                    active.add(key)
                elif cur == 0 and reading.sensor_type not in _TRACK:
                    continue

            if not reading.changed:
                continue

            sensor_obj = sensor_map.get(key)
            if sensor_obj is not None:
                item.setText(1, sensor_obj.format_reading(cur))
                item.setText(2, sensor_obj.format_reading(reading.min_val) if reading.min_val != _INF else "--")
                item.setText(3, sensor_obj.format_reading(reading.max_val) if reading.max_val != _NINF else "--")
            else:
                st = reading.sensor_type
                item.setText(1, format_value(cur, st))
                item.setText(2, format_value(reading.min_val, st) if reading.min_val != _INF else "--")
                item.setText(3, format_value(reading.max_val, st) if reading.max_val != _NINF else "--")

            if reading.sensor_type is _TEMP:
                item.setForeground(1, QColor(self._get_temp_color(cur)))

        if self._poll_count == 3:
            self._hide_inactive_sensors()
            count = sum(1 for k in sensor_items if k in active)
            self._status_label.setText(f"{count} sensors")

        self._log_data.append((datetime.now().isoformat(), *values))

        self._tray_icon.setToolTip(f"CorePulse — {hottest_name}: {hottest_temp:.0f}°C")
        self._check_alerts(readings)

    def _hide_inactive_sensors(self) -> None:
        """Hide sensors that never reported data and empty type groups."""
        for key, item in self._sensor_items.items():
            if key not in self._active_sensors:
                item.setHidden(True)

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

    # --- Reset actions ---

    def _reset_min_max(self) -> None:
        """Reset min/max tracking for all sensors."""
        self._poller.reset_min_max()
        for item in self._sensor_items.values():
            item.setText(2, "--")
            item.setText(3, "--")
        self.statusBar().showMessage("Min/Max values reset", 3000)

    def _clear_alerts(self) -> None:
        """Remove all configured alert thresholds."""
        self._alert_thresholds.clear()
        self._triggered_alerts.clear()
        for item in self._sensor_items.values():
            item.setText(4, "")
            item.setForeground(4, QBrush(QColor(cfg.COLOR_TEXT_PRIMARY)))
        self.statusBar().showMessage("All alerts cleared", 3000)

    # --- Per-metric alerts ---

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on Alert column to set/clear threshold."""
        if column != 4:
            return

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
            item.setForeground(4, QBrush(QColor(cfg.COLOR_TEXT_PRIMARY)))
        elif value > 0:
            self._alert_thresholds[key] = value
            fmt, unit = SENSOR_FORMATS.get(st, ("{:.1f}", ""))
            item.setText(4, fmt.format(value) + unit)
            item.setForeground(4, QBrush(QColor(cfg.COLOR_TEXT_SECONDARY)))

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
                    self._broadcaster.send_alert(
                        sensor_name, reading.current, threshold, unit.strip(),
                    )
                item = self._sensor_items.get(key)
                if item:
                    item.setForeground(4, QBrush(QColor(cfg.COLOR_WARNING)))
            else:
                self._triggered_alerts.discard(key)
                item = self._sensor_items.get(key)
                if item and key in self._alert_thresholds:
                    item.setForeground(4, QBrush(QColor(cfg.COLOR_TEXT_SECONDARY)))

    # --- CSV export ---

    def _export_csv(self) -> None:
        """Export sensor log to CSV."""
        if not self._log_data:
            return

        default_name = f"corepulse_{datetime.now():%Y%m%d_%H%M%S}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export", default_name, "CSV (*.csv)")
        if not path:
            return

        headers = ["timestamp"] + self._log_keys
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(self._log_data)

        self.statusBar().showMessage(f"Exported {len(self._log_data)} records", 5000)

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
        self._tray_icon.setToolTip("CorePulse — Loading...")
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
        self._theme_watcher.stop()
        self._broadcaster.stop()
        shutdown_nvml()
        self._tray_icon.hide()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    @staticmethod
    def _get_temp_color(temp: float) -> str:
        """Return color for a temperature value."""
        if temp < TEMP_THRESHOLD_LOW:
            return cfg.COLOR_TEMP_COOL
        elif temp < TEMP_THRESHOLD_MEDIUM:
            return cfg.COLOR_TEMP_WARM
        elif temp < TEMP_THRESHOLD_HIGH:
            return cfg.COLOR_TEMP_HOT
        else:
            return cfg.COLOR_TEMP_CRITICAL
