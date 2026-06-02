# JobFit AI — AI Resume Match & Optimization Product Demo

JobFit AI is a product-style AI engineering project that turns a resume and a job description into an explainable match report, evidence-backed gaps, ATS keyword coverage, and truth-guarded resume rewrite suggestions.

It is intentionally scoped as a **portfolio/CV-ready product demo**, not a full SaaS platform. The goal is to demonstrate end-to-end AI product engineering: practical document ingestion, schema-first extraction, deterministic scoring, AI safety guardrails, observability foundations, and a polished Next.js user experience.

## Product Story

Most resume tools produce generic feedback or rewrite text without proving whether the candidate actually has the underlying experience. JobFit AI focuses on a safer workflow:

1. Accept real-world resume/JD inputs.
2. Extract structured signals from both sides.
3. Score the fit with transparent evidence rows.
4. Highlight strengths, gaps, and missing ATS keywords.
5. Suggest resume improvements while flagging unsupported claims.
6. Present the result in a shareable report page.

## Demo Flow

```text
Open /analyze
  -> use the built-in EN/VI/ZH/JA demo data or upload real files
  -> submit the no-account analysis flow
  -> backend runs ingest -> parse -> match -> optimize -> truth guard
  -> open /reports/{id}
  -> share or export the report as Markdown
```

Main frontend routes:

- `/` — product landing page
- `/analyze` — no-account CV/JD analysis workbench
- `/reports/{id}` — shareable report detail page
- `/diagnostics` — AI pipeline/observability explainer page

## Key Features

| Area | What it demonstrates |
| --- | --- |
| Document ingestion | Resume/JD input via pasted text, PDF, DOCX, TXT, Markdown, or public JD URL |
| Explainable scoring | Deterministic skill/requirement/experience/language breakdown with persisted evidence rows |
| Language support | English, Vietnamese, Chinese, and Japanese detection for resume/JD language matching |
| Resume optimization | Rewrite suggestions tied to match gaps and estimated score lift |
| Truth guard | Suggestions classified as `safe`, `needs_review`, or `unsupported` to avoid invented claims |
| Product UX | Polished landing page, live analyze workflow, sticky report actions, markdown export |
| AI observability | AI run/output tables, parse diagnostics, prompt-version-ready architecture |
| Evaluation foundation | Smoke datasets and CLI runner for parser, matching, and truth-guard checks |

## Architecture

```text
frontend/  Next.js 14 App Router product UI
backend/   FastAPI API, ingestion services, AI pipeline, scoring, guardrails
backend/app/db/  SQLAlchemy models for resumes, jobs, reports, evidence, AI runs, evals
infra/     Dockerfiles, Docker Compose, pgvector init script
docs/      PRD, architecture, prompt/eval docs, case study, CV summary
```

Runtime flow:

```text
Next.js /analyze
  -> POST /api/analyze multipart form
  -> ingestion layer extracts file/text/url content
  -> local parser creates resume/job structured JSON
  -> deterministic match engine creates MatchReport + MatchEvidence
  -> optimizer creates RewriteSuggestion rows
  -> truth guard labels suggestion safety
  -> Next.js /reports/{id} reads and presents the final report
```

## Tech Stack

| Layer | Stack |
| --- | --- |
| Frontend | Next.js 14 App Router, React 18, TypeScript, vanilla CSS |
| Backend | FastAPI, SQLAlchemy 2 async, Pydantic, Alembic |
| Database | PostgreSQL 16, pgvector-ready schema, JSONB report storage |
| AI pipeline | Local deterministic parsers/optimizer by default, prompt/provider abstractions reserved |
| Ingestion | PDF/DOCX/TXT extraction, SSRF-aware public URL fetcher |
| Quality | TypeScript strict mode, Ruff/Mypy/Pytest backend config, eval harness |

> The live matching flow currently uses deterministic keyword/alias scoring. The pgvector schema is present for future semantic evidence retrieval, but runtime vector retrieval is not required for the current product demo.

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker Desktop, if running the full backend/PostgreSQL stack

### Environment

Copy the environment template:

```bash
cp .env.example .env
```

Important defaults:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
DATABASE_URL=postgresql+asyncpg://jobfit:jobfit@localhost:5432/jobfit
BACKEND_CORS_ORIGINS=http://localhost:3000
```

### Full stack with Docker Compose

```bash
docker compose up --build
```

Services:

- Frontend: <http://localhost:3000>
- Backend API: <http://localhost:8000>
- API docs: <http://localhost:8000/docs>
- PostgreSQL: `localhost:5432`

### Frontend only

```bash
cd frontend
npm install
npm run dev
```

If Next.js shows a stale cache/runtime error after major changes, run:

```bash
npm run dev:clean
```

Validation commands:

```bash
cd frontend
npm run typecheck
npm run build
# or
npm run verify
```

### Backend only

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

## API Surface

- `POST /api/analyze` — one-shot resume + JD ingestion, parsing, matching, and optimization
- `GET /api/match-reports/{id}` — read report + evidence rows
- `POST /api/optimizations` — idempotently create/read optimization for a report
- `GET /api/resumes/{id}` — read resume source + parsed JSON
- `GET /api/jobs/{id}` — read job source + parsed JSON
- `GET /health` — backend health check

## Portfolio / CV Positioning

Suggested project line:

> Built JobFit AI, an AI-powered resume-to-job matching product that ingests resumes and job descriptions, extracts structured signals, generates explainable match reports, and produces truth-guarded optimization suggestions using Next.js, FastAPI, PostgreSQL, and schema-first AI pipelines.

Impact bullets:

- Designed an end-to-end CV/JD analysis pipeline from document ingestion to shareable report UX.
- Implemented explainable deterministic scoring with persisted requirement-level evidence rows.
- Built truth-guarded resume rewrite suggestions to reduce unsupported or hallucinated claims.
- Created a polished no-account product demo with markdown export and reusable API/type layers.
- Added AI observability and evaluation foundations for prompt/schema quality tracking.

More detail:

- [Case study](docs/case_study.md)
- [CV summary](docs/cv_summary.md)
- [PRD](docs/prd.md)
- [Technical architecture](docs/technical_architecture.md)
- [Evaluation plan](docs/evaluation_plan.md)
