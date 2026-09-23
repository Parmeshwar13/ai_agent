PYTHON ?= python3
VENV ?= .venv
PY := $(VENV)/bin/python

.PHONY: install test migrate seed

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -r backend/requirements-dev.txt
	cd frontend && npm install

test:
	$(PY) -m pytest

migrate:
	cd backend && ../$(PY) manage.py migrate

seed:
	cd backend && ../$(PY) manage.py seed_demo
