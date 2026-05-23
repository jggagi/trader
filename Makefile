.PHONY: help setup run run-cloud test compile check status pull push clean

PYTHON ?= python
PORT ?= 8502

help:
	@echo "QQQ Trader workflow"
	@echo ""
	@echo "make setup      Install local dependencies"
	@echo "make run        Run local Streamlit server on PORT=$(PORT)"
	@echo "make run-cloud  Run locally with APP_MODE=cloud"
	@echo "make test       Run tests"
	@echo "make compile    Byte-compile app and package"
	@echo "make check      Run compile + tests"
	@echo "make status     Show git status"
	@echo "make pull       Pull latest main"
	@echo "make push       Push current branch"
	@echo "make clean      Remove local caches"

setup:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e ".[dev]"

run:
	streamlit run app.py --server.port $(PORT)

run-cloud:
	APP_MODE=cloud streamlit run app.py --server.port $(PORT)

test:
	pytest

compile:
	$(PYTHON) -m compileall app.py trader tests

check: compile test

status:
	git status -sb

pull:
	git pull --ff-only origin main

push:
	git push origin $$(git branch --show-current)

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

