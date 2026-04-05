"""
System theme change watcher.

Monitors DBus for GNOME theme setting changes and emits a signal
when the system switches between dark and light mode.
"""

# Third-party
from PySide6.QtCore import QObject, Signal

# Local
import utils.config as cfg


class ThemeWatcher(QObject):
    """Watches for system theme changes via DBus (gdbus monitor) and emits a signal."""

    theme_changed = Signal(bool)

    def start(self) -> None:
        """Start monitoring DBus for theme setting changes."""
        from PySide6.QtCore import QProcess
        self._proc = QProcess(self)
        self._proc.setProgram("gdbus")
        self._proc.setArguments([
            "monitor", "--session",
            "--dest", "org.freedesktop.portal.Desktop",
            "--object-path", "/org/freedesktop/portal/desktop",
        ])
        self._proc.readyReadStandardOutput.connect(self._on_output)
        self._proc.start()

    def _on_output(self) -> None:
        """Parse gdbus monitor output for theme changes."""
        data = self._proc.readAllStandardOutput().data().decode(errors="replace")
        for line in data.splitlines():
            if "SettingChanged" not in line:
                continue
            if "gtk-theme" in line or "color-scheme" in line:
                self.theme_changed.emit(cfg.detect_dark_mode())
                return

    def stop(self) -> None:
        """Stop the monitor process."""
        if hasattr(self, "_proc") and self._proc.state() != 0:
            self._proc.kill()
            self._proc.waitForFinished(1000)
