SHELL := /bin/bash

.PHONY: dev backend frontend test seed docker

dev:
	docker compose up --build

backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest

seed:
	cd backend && python scripts/seed_sample.py

docker:
	docker compose up --build
