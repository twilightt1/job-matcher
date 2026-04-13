.PHONY: dev db-up backend frontend test-backend lint-backend typecheck-backend eval-all

dev:
	docker compose up --build

db-up:
	docker compose up postgres

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

test-backend:
	cd backend && pytest

lint-backend:
	cd backend && ruff check .

typecheck-backend:
	cd backend && mypy app

eval-all:
	cd backend && python -m app.evals.runner --task all --dataset v1
