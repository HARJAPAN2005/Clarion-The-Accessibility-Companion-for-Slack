# =============================================================================
# Clarion — Makefile
# =============================================================================
# Usage:
#   make install      Install all dependencies (including dev extras)
#   make dev          Start Clarion in Socket Mode
#   make test         Run the test suite
#   make lint         Run ruff linter
#   make format       Auto-format with ruff
#   make typecheck    Run mypy type checking
#   make audit        Run pip-audit security scan
#   make clean        Remove all build/cache artifacts
#   make docker-build Build the Docker image
#   make docker-run   Run Clarion in Docker (requires .env)

.PHONY: install dev test lint format typecheck audit clean docker-build docker-run

PYTHON   := python
PIP      := $(PYTHON) -m pip
PYTEST   := $(PYTHON) -m pytest
RUFF     := $(PYTHON) -m ruff
MYPY     := $(PYTHON) -m mypy
AUDIT    := $(PYTHON) -m pip_audit

IMAGE    := clarion
PORT     := 3000

install:
	$(PIP) install -e ".[dev]"

dev:
	$(PYTHON) app.py

test:
	$(PYTEST) tests/ -v --tb=short

test-cov:
	$(PYTEST) tests/ --cov=. --cov-report=term-missing --cov-report=html

lint:
	$(RUFF) check .

format:
	$(RUFF) format .
	$(RUFF) check --fix .

typecheck:
	$(MYPY) agent.py tools.py config.py thread_context.py rts_client.py slack_mcp.py \
		--ignore-missing-imports

audit:
	$(AUDIT) -r requirements.txt

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	@echo "Clean complete."

docker-build:
	docker build -t $(IMAGE):latest .

docker-run:
	docker run --rm --env-file .env $(IMAGE):latest

# ---------------------------------------------------------------------------
# Convenience aliases
# ---------------------------------------------------------------------------
check: lint typecheck test
ci: install lint typecheck test audit
