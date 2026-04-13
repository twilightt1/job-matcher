# JobFit AI — AI Job Match & Resume Optimizer

JobFit AI is a portfolio-grade AI/ML engineering project that combines structured LLM extraction, embedding-based semantic matching, explainable scoring, and truth-guarded resume optimization.

## Architecture

```text
frontend/  Next.js product UI
backend/   Python FastAPI API + AI/ML pipeline
docs/      Product, architecture, API, and evaluation docs
infra/     Docker and infrastructure helpers
```

## MVP Flow

```text
Paste resume text
  -> Paste job description
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
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Frontend only

```bash
cd frontend
npm install
npm run dev
```

## Portfolio Highlights

- **Schema-first LLM extraction** for resumes and job descriptions.
- **Explainable matching** with evidence rows and confidence values.
- **Deterministic scoring** separated from LLM text generation.
- **Truth guard** to flag unsupported resume claims.
- **AI run logging** for model, prompt version, latency, tokens, and cost.
- **Evaluation harness** for extraction, matching, and hallucination metrics.

## Current Status

Milestone 0 foundation is being implemented:

- FastAPI backend skeleton
- Next.js frontend skeleton
- PostgreSQL + pgvector Docker setup
- Repository documentation and environment template
