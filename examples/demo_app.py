#!/usr/bin/env python3
"""
Demo: simple app that auto-closes when CorePulse sends an alert.

Opens a small window with a status label. When CorePulse fires
an alert (any sensor exceeds its threshold), this app receives the
event and closes itself — simulating a workload that should stop
when the system overheats.

Usage:
    # Terminal 1: run CorePulse
    ./corepulse.sh

    # Terminal 2: run this demo
    python examples/demo_app.py

    # Set a low alert threshold in CorePulse (e.g. 40°C on any sensor)
    # and watch this app close automatically when the alert fires.
"""

import json
import socket
import sys
import threading

from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, Signal, QObject

SOCKET_PATH = "/tmp/corepulse.sock"


class AlertListener(QObject):
    """Listens for CorePulse alerts in a background thread."""

    alert_received = Signal(str)
    connection_lost = Signal()

    def start(self) -> None:
        """Connect and start listening."""
        thread = threading.Thread(target=self._listen, daemon=True)
        thread.start()

    def _listen(self) -> None:
        """Connect to CorePulse and listen for events."""
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(SOCKET_PATH)
        except (FileNotFoundError, ConnectionRefusedError):
            self.connection_lost.emit()
            return

        buffer = ""
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    self.connection_lost.emit()
                    break
                buffer += data.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    event = json.loads(line)
                    msg = f"{event['sensor']}: {event['value']} {event['unit']}"
                    self.alert_received.emit(msg)
        except OSError:
            self.connection_lost.emit()
        finally:
            sock.close()


class DemoWindow(QWidget):
    """Simple window that closes on CorePulse alert."""

    def __init__(self) -> None:
        """Initialize the demo window."""
        super().__init__()
        self.setWindowTitle("Demo App — CorePulse Watcher")
        self.setFixedSize(400, 150)

        layout = QVBoxLayout(self)
        self._status = QLabel("Connecting to CorePulse...")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setStyleSheet("font-size: 16px; padding: 20px;")
        layout.addWidget(self._status)

        self._listener = AlertListener()
        self._listener.alert_received.connect(self._on_alert)
        self._listener.connection_lost.connect(self._on_disconnected)
        self._listener.start()

    def _on_alert(self, msg: str) -> None:
        """Handle alert — show message and close."""
        self._status.setText(f"ALERT: {msg}\nClosing in 2 seconds...")
        self._status.setStyleSheet("font-size: 16px; padding: 20px; color: red;")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, QApplication.quit)

    def _on_disconnected(self) -> None:
        """Handle CorePulse not running."""
        self._status.setText("CorePulse not running.\nStart it and restart this demo.")
        self._status.setStyleSheet("font-size: 14px; padding: 20px; color: orange;")


def main() -> None:
    """Run the demo app."""
    app = QApplication(sys.argv)
    window = DemoWindow()
    window.show()

    # Update status once connected
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(SOCKET_PATH)
        sock.close()
        window._status.setText("Connected to CorePulse.\nWaiting for alert...")
        window._status.setStyleSheet("font-size: 16px; padding: 20px; color: green;")
    except (FileNotFoundError, ConnectionRefusedError):
        pass

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
