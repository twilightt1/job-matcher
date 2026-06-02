# JobFit AI — AI Job Match & Resume Optimizer

JobFit AI is a portfolio-grade AI/ML engineering project that combines document ingestion, structured LLM extraction, explainable scoring, and truth-guarded resume optimization.

## Architecture

```text
frontend/  Next.js product UI with a live analyze workflow
backend/   Python FastAPI API + ingestion + AI/ML pipeline
docs/      Product, architecture, API, and evaluation docs
infra/     Docker and infrastructure helpers
```

## MVP Flow

```text
Upload resume PDF/DOCX/TXT or paste resume text
  -> Provide a JD via pasted text, public URL, PDF, DOCX, or TXT
  -> Extract and validate source text
  -> Parse both into structured JSON
  -> Normalize skills
  -> Retrieve semantic evidence
  -> Calculate explainable match score
  -> Generate optimization suggestions
  -> Run truth guard
  -> Show a portfolio-ready report
```

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker Desktop

### Environment

Copy the environment template:

```bash
cp .env.example .env
```

Key ingestion settings are included in `.env.example`:

- `UPLOAD_STORAGE_DIR=storage/uploads`
- `MAX_UPLOAD_BYTES=10000000`
- `URL_FETCH_TIMEOUT_SECONDS=10`
- `MAX_URL_RESPONSE_BYTES=2000000`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

### Start with Docker Compose

```bash
docker compose up --build
```

Services:

- Frontend: <http://localhost:3000>
- Backend API: <http://localhost:8000>
- API docs: <http://localhost:8000/docs>
- PostgreSQL: `localhost:5432`

### Backend only

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Frontend only

```bash
cd frontend
npm install
npm run dev
```

Open the live analyze UI at <http://localhost:3000/analyze>.

## Key API Endpoints

- `POST /api/resumes` — create resume from pasted text
- `POST /api/resumes/upload` — upload resume PDF/DOCX/TXT
- `POST /api/jobs` — create JD from pasted text
- `POST /api/jobs/upload` — upload JD PDF/DOCX/TXT
- `POST /api/jobs/from-url` — fetch and extract a public JD URL
- `POST /api/analyze` — one-shot resume + JD ingestion, parsing, matching, and optimization
- `GET /api/match-reports/{id}` — read explainable report + evidence rows
- `GET /api/optimizations/{id}` — read optimized resume + guarded suggestions

## Portfolio Highlights

- **Document ingestion** for resume/JD PDF, DOCX, TXT, and Markdown text sources.
- **SSRF-aware JD URL fetcher** for public HTML/text job pages.
- **One-shot AI analyze workflow** from source material to match report and optimization.
- **Schema-first LLM extraction** for resumes and job descriptions.
- **Explainable matching** with evidence rows and confidence values.
- **Deterministic scoring** separated from LLM text generation.
- **Truth guard** to flag unsupported resume claims.
- **AI run logging** for model, prompt version, latency, tokens, and cost.
- **Evaluation harness** for extraction, matching, and hallucination metrics.

## Current Status

Milestone 0–6 backend foundation plus the ingestion upgrade are implemented (see [docs/prd.md](docs/prd.md)):

- FastAPI backend skeleton + CORS configuration
- Next.js frontend skeleton with a live `/analyze` upload/link workflow
- PostgreSQL + pgvector Docker setup
- Schema-first resume/job parsing APIs (local parser + AIRun logging)
- PDF/DOCX/TXT upload ingestion and safe public JD URL extraction
- One-shot analyze endpoint that runs parse → match → optimize
- Deterministic match engine with skill normalization and evidence rows
- Truth-guard classification for resume rewrite suggestions
- AI run / AI output observability tables and parse-diagnostics endpoints
- Evaluation harness (CLI runner, datasets, metrics, markdown report)
- Alembic initial migration applied
