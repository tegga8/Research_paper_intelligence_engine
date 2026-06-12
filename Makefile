SHELL := /bin/bash

.PHONY: cli dev setup setup-backend setup-frontend backend frontend seed test clean

PYTHON ?= python3
VENV := backend/.venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
UVICORN := $(VENV)/bin/uvicorn

cli:
	python3 terminal_app.py

setup: setup-backend setup-frontend

setup-backend:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt

setup-frontend:
	cd frontend && npm install

# Starts both apps locally without Docker. Run `make setup` first.
dev:
	@if [ ! -x "$(UVICORN)" ]; then echo "Backend venv missing. Run: make setup-backend"; exit 1; fi
	@if [ ! -d "frontend/node_modules" ]; then echo "Frontend dependencies missing. Run: make setup-frontend"; exit 1; fi
	@trap 'kill 0' EXIT; \
	( cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 ) & \
	( cd frontend && NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run dev ) & \
	wait

backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

frontend:
	cd frontend && NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run dev

seed:
	cd backend && . .venv/bin/activate && python scripts/seed_sample.py

test:
	cd backend && . .venv/bin/activate && pytest

clean:
	rm -rf backend/.venv backend/.pytest_cache frontend/node_modules frontend/.next .faiss backend/.faiss backend/research.db research_terminal.db
