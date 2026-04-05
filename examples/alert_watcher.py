#!/usr/bin/env python3
"""
Demo: external app that reacts to CorePulse alerts.

Connects to CorePulse's Unix socket and listens for alert events.
When an alert fires, it prints the event and (optionally) kills a
target process — showing how any app could auto-shutdown when
temperatures get too high.

Usage:
    # Terminal 1: run CorePulse
    ./corepulse.sh

    # Terminal 2: run this watcher (just prints alerts)
    python examples/alert_watcher.py

    # Or: kill a specific process when any alert fires
    python examples/alert_watcher.py --kill firefox

    # Or: kill by PID
    python examples/alert_watcher.py --kill-pid 12345

    # Then set an alert in CorePulse (double-click Alert column)
    # and wait for it to trigger.
"""

import argparse
import json
import os
import signal
import socket
import subprocess
import sys

SOCKET_PATH = "/tmp/corepulse.sock"


def connect() -> socket.socket:
    """Connect to CorePulse's IPC socket."""
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(SOCKET_PATH)
    return sock


def find_pid_by_name(name: str) -> int | None:
    """Find PID of a process by name using pgrep."""
    try:
        out = subprocess.check_output(["pgrep", "-f", name], text=True)
        pids = [int(p) for p in out.strip().split("\n") if p]
        # Exclude our own PID
        pids = [p for p in pids if p != os.getpid()]
        return pids[0] if pids else None
    except (subprocess.CalledProcessError, ValueError):
        return None


def main() -> None:
    """Listen for CorePulse alerts and react."""
    parser = argparse.ArgumentParser(description="React to CorePulse alerts")
    parser.add_argument("--kill", metavar="NAME",
                        help="Process name to kill when an alert fires")
    parser.add_argument("--kill-pid", metavar="PID", type=int,
                        help="PID to kill when an alert fires")
    args = parser.parse_args()

    print(f"Connecting to CorePulse at {SOCKET_PATH}...")
    try:
        sock = connect()
    except (FileNotFoundError, ConnectionRefusedError):
        print("ERROR: CorePulse is not running or IPC is not available.")
        print("Start CorePulse first, then run this script.")
        sys.exit(1)

    print("Connected. Waiting for alerts...\n")

    buffer = ""
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                print("CorePulse disconnected.")
                break

            buffer += data.decode()
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                event = json.loads(line)

                sensor = event["sensor"]
                value = event["value"]
                threshold = event["threshold"]
                unit = event["unit"]

                print(f"ALERT: {sensor} = {value} {unit} (threshold: {threshold} {unit})")

                if args.kill:
                    pid = find_pid_by_name(args.kill)
                    if pid:
                        print(f"  -> Killing '{args.kill}' (PID {pid})")
                        os.kill(pid, signal.SIGTERM)
                    else:
                        print(f"  -> Process '{args.kill}' not found")

                elif args.kill_pid:
                    print(f"  -> Killing PID {args.kill_pid}")
                    try:
                        os.kill(args.kill_pid, signal.SIGTERM)
                    except ProcessLookupError:
                        print(f"  -> PID {args.kill_pid} not found")

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
