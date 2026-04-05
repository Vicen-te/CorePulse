.PHONY: install uninstall run test benchmark clean

SHELL      := /bin/bash
PREFIX     := $(shell pwd)
VENV       := $(PREFIX)/.venv
PIP        := $(VENV)/bin/pip
PYTHON     := $(VENV)/bin/python
DESKTOP_DIR := $(HOME)/.local/share/applications
ICON_DIR   := $(HOME)/.local/share/icons/hicolor/scalable/apps
RAPL_RULE  := /etc/udev/rules.d/99-thermalcore-rapl.rules

# ── Install ──────────────────────────────────────────────────────────

install: deps venv pip-deps rapl desktop
	@echo ""
	@echo "  ThermalCore installed successfully."
	@echo "  Run:  make run"
	@echo "  Or search 'ThermalCore' in your app launcher."
	@echo ""

deps:
	@echo "[*] Installing system dependencies..."
	@sudo apt-get update -qq
	@sudo apt-get install -y -qq lm-sensors libxcb-cursor0 python3-venv > /dev/null
	@command -v sensors > /dev/null || sudo sensors-detect --auto

venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "[*] Creating virtual environment..."; \
		python3 -m venv $(VENV); \
	fi

pip-deps:
	@echo "[*] Installing Python dependencies..."
	@$(PIP) install -q -r requirements.txt

rapl:
	@if [ -f "/sys/class/powercap/intel-rapl:0/energy_uj" ] && [ ! -f "$(RAPL_RULE)" ]; then \
		echo "[*] Setting up CPU power monitoring (RAPL)..."; \
		echo 'SUBSYSTEM=="powercap", ACTION=="add", RUN+="/bin/chmod o+r /sys/class/powercap/intel-rapl:0/energy_uj"' \
			| sudo tee $(RAPL_RULE) > /dev/null; \
		sudo udevadm control --reload-rules; \
		sudo udevadm trigger --subsystem-match=powercap; \
		sudo chmod o+r /sys/class/powercap/intel-rapl:0/energy_uj; \
	fi

desktop:
	@echo "[*] Installing desktop launcher..."
	@mkdir -p $(DESKTOP_DIR) $(ICON_DIR)
	@cp assets/icons/thermalcore.svg $(ICON_DIR)/thermalcore.svg
	@gtk-update-icon-cache -f -t $(HOME)/.local/share/icons/hicolor 2>/dev/null || true
	@sed "s|__INSTALL_DIR__|$(PREFIX)|g" thermalcore.desktop > $(DESKTOP_DIR)/thermalcore.desktop
	@update-desktop-database $(DESKTOP_DIR) 2>/dev/null || true

# ── Uninstall ────────────────────────────────────────────────────────

uninstall:
	@echo "[*] Removing ThermalCore..."
	@rm -f $(DESKTOP_DIR)/thermalcore.desktop
	@rm -f $(ICON_DIR)/thermalcore.svg
	@update-desktop-database $(DESKTOP_DIR) 2>/dev/null || true
	@gtk-update-icon-cache -f -t $(HOME)/.local/share/icons/hicolor 2>/dev/null || true
	@if [ -f "$(RAPL_RULE)" ]; then \
		sudo rm -f $(RAPL_RULE); \
		sudo udevadm control --reload-rules; \
	fi
	@echo "  Done. Remove the project folder manually if desired."

# ── Run ──────────────────────────────────────────────────────────────

run:
	@$(VENV)/bin/python src/main.py

# ── Tests ────────────────────────────────────────────────────────────

test:
	@$(VENV)/bin/python -m pytest tests/ -v

benchmark:
	@$(VENV)/bin/python -m tests.benchmarks.bench_sensors
	@echo "---"
	@$(VENV)/bin/python -m tests.benchmarks.bench_polling
	@echo "---"
	@$(VENV)/bin/python -m tests.benchmarks.bench_startup

# ── Clean ────────────────────────────────────────────────────────────

clean:
	@rm -rf $(VENV) .pytest_cache src/__pycache__ src/**/__pycache__ tests/__pycache__ tests/**/__pycache__
	@echo "  Cleaned."
