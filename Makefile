PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
VENV ?= .venv
ACTIVATE = . $(VENV)/bin/activate

ENV_FILE ?= .env
APP_CONFIG ?= configs/app.yaml

.PHONY: help install install-dev run-headless run-interactive run-scenario lint test format clean clean-venv env-example

help:
	@echo "Targets:"
	@echo "  install         Create venv and install runtime deps"
	@echo "  install-dev     Install runtime + dev/test extras"
	@echo "  run-headless    Run simulator in headless mode"
	@echo "  run-interactive Run simulator with UI"
	@echo "  run-scenario    Run headless with explicit scenario file SCENARIO=<path>"
	@echo "  lint            Placeholder for linting (extend with ruff/flake8)"
	@echo "  test            Run pytest suite"
	@echo "  clean           Remove __pycache__ and build artifacts"
	@echo "  clean-venv      Remove virtual environment"

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && $(PIP) install --upgrade pip

install: $(VENV)/bin/activate
	$(ACTIVATE) && $(PIP) install -e .[runtime,observability]

install-dev: $(VENV)/bin/activate
	$(ACTIVATE) && $(PIP) install -e .[runtime,observability,test]

run-headless: export WRTC_SIM_MODE=headless
run-headless: install
	@if [ -f $(ENV_FILE) ]; then set -a; . $(ENV_FILE); set +a; fi; \
	$(ACTIVATE) && PYTHONPATH=src $(PYTHON) -m webrtc_sim.main --config $(APP_CONFIG) --mode headless

run-interactive: export WRTC_SIM_MODE=interactive
run-interactive: install
	@if [ -f $(ENV_FILE) ]; then set -a; . $(ENV_FILE); set +a; fi; \
	$(ACTIVATE) && PYTHONPATH=src $(PYTHON) -m webrtc_sim.main --config $(APP_CONFIG) --mode interactive

run-scenario: export WRTC_SIM_MODE=headless
run-scenario: install
	@if [ -z "$$SCENARIO" ]; then echo "SCENARIO=<path> required"; exit 1; fi; \
	if [ -f $(ENV_FILE) ]; then set -a; . $(ENV_FILE); set +a; fi; \
	$(ACTIVATE) && PYTHONPATH=src WRTC_SCENARIO_FILE=$$SCENARIO $(PYTHON) -m webrtc_sim.main --config $(APP_CONFIG) --mode headless

lint: install-dev
	@echo "No linters configured; add ruff/flake8 here."

test: install-dev
	$(ACTIVATE) && PYTHONPATH=src pytest -q

format:
	@echo "Add formatter commands (e.g., ruff format/black) here."

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -delete

clean-venv:
	rm -rf $(VENV)

env-example:
	@cp -n .env.example .env || true
