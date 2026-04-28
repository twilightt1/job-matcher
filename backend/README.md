# JobFit AI Backend

Python FastAPI backend for the JobFit AI portfolio project.

## Responsibilities

- Product API for resumes, jobs, match reports, and optimizations.
- AI/ML orchestration for parsing, embeddings, matching, scoring, and guardrails.
- AI run logging and evaluation harness.
- PostgreSQL + pgvector persistence.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Common commands

```bash
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m mypy app
.venv\Scripts\python -m pytest
```

API docs are available at <http://localhost:8000/docs>.
