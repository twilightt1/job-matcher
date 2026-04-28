.PHONY: dev db-up backend frontend test-backend lint-backend typecheck-backend eval-all backend-venv

dev:
	docker compose up --build

db-up:
	docker compose up postgres

backend-venv:
	cd backend && python -m venv .venv && .venv\Scripts\python -m pip install --upgrade pip && .venv\Scripts\python -m pip install -e ".[dev]"

backend:
	cd backend && .venv\Scripts\python -m uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

test-backend:
	cd backend && .venv\Scripts\python -m pytest

lint-backend:
	cd backend && .venv\Scripts\python -m ruff check .

typecheck-backend:
	cd backend && .venv\Scripts\python -m mypy app

eval-all:
	cd backend && .venv\Scripts\python -m app.evals.runner --task all --dataset v1
