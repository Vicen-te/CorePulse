"""
IPC server for ThermalCore.

Broadcasts alert events over a Unix domain socket so external
apps can react to temperature/load alerts in real time.

Protocol: one JSON line per event, newline-delimited.
"""

import json
import os
import socket
import threading

SOCKET_PATH = "/tmp/thermalcore.sock"


class AlertBroadcaster:
    """Broadcasts alert events to connected Unix socket clients."""

    def __init__(self) -> None:
        """Initialize the broadcaster."""
        self._clients: list[socket.socket] = []
        self._server: socket.socket | None = None
        self._running = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start listening for client connections in a background thread."""
        # Clean up stale socket
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)

        self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server.bind(SOCKET_PATH)
        self._server.listen(5)
        self._server.settimeout(1.0)
        self._running = True

        thread = threading.Thread(target=self._accept_loop, daemon=True)
        thread.start()

    def _accept_loop(self) -> None:
        """Accept incoming connections."""
        while self._running:
            try:
                client, _ = self._server.accept()
                with self._lock:
                    self._clients.append(client)
            except socket.timeout:
                continue
            except OSError:
                break

    def send_alert(self, sensor: str, value: float, threshold: float, unit: str) -> None:
        """Broadcast an alert event to all connected clients."""
        msg = json.dumps({
            "event": "alert",
            "sensor": sensor,
            "value": value,
            "threshold": threshold,
            "unit": unit,
        }) + "\n"
        data = msg.encode()

        with self._lock:
            dead: list[socket.socket] = []
            for client in self._clients:
                try:
                    client.sendall(data)
                except OSError:
                    dead.append(client)
            for client in dead:
                self._clients.remove(client)
                client.close()

    def stop(self) -> None:
        """Shut down the server and close all clients."""
        self._running = False
        with self._lock:
            for client in self._clients:
                client.close()
            self._clients.clear()
        if self._server:
            self._server.close()
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)
