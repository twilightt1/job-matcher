# JobFit AI Backend

Python FastAPI backend for the JobFit AI portfolio project.

## Responsibilities

- Product API for resumes, jobs, match reports, optimizations, and one-shot analysis.
- Resume/JD ingestion from PDF, DOCX, TXT, pasted text, and public JD URLs.
- SSRF-aware URL fetching and local upload persistence.
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

API docs are available at <http://localhost:8000/docs>.

## Ingestion endpoints

- `POST /api/resumes/upload` — multipart resume upload; accepts PDF, DOCX, TXT, or Markdown.
- `POST /api/jobs/upload` — multipart JD upload; accepts PDF, DOCX, TXT, or Markdown.
- `POST /api/jobs/from-url` — JSON body with a public `http(s)` job URL.
- `POST /api/analyze` — multipart one-shot workflow:
  - `resume_file` or `resume_text`
  - `job_input_type=text|url|file`
  - `job_text`, `job_url`, or `job_file`
  - returns `resume`, `job`, `match_report`, and `optimization`

## Ingestion configuration

- `UPLOAD_STORAGE_DIR` — local upload root, default `storage/uploads`.
- `MAX_UPLOAD_BYTES` — default `10000000`.
- `URL_FETCH_TIMEOUT_SECONDS` — default `10`.
- `MAX_URL_RESPONSE_BYTES` — default `2000000`.

Uploaded files are stored under `backend/storage/uploads/`, which is gitignored. URL ingestion only allows public HTTP/HTTPS destinations and blocks private, loopback, link-local, multicast, reserved, and unspecified IP addresses.

## Common commands

```bash
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m mypy app
.venv\Scripts\python -m pytest
```
