# JobFit AI — Technical Architecture

> **Phiên bản:** 0.3.0  
> **Cập nhật:** 2026-06-14  
> **Phạm vi:** tài liệu mô tả kiến trúc hiện tại trong repository `job-matcher`.
> Nội dung ưu tiên phản ánh code đang có, không mô tả tính năng chưa được nối vào
> runtime trừ khi được ghi rõ là "planned" hoặc "not wired yet".

## 1. Executive Summary

JobFit AI là một ứng dụng portfolio-grade giúp người dùng:

1. Upload CV/resume bằng PDF, DOCX, TXT/Markdown hoặc paste text.
2. Nhập Job Description bằng text, public URL hoặc file PDF/DOCX/TXT.
3. Backend tự động ingest, parse, match, optimize và trả về báo cáo phù hợp.
4. Frontend hiển thị score, evidence, gaps, ATS keywords và rewrite suggestions.

Kiến trúc hiện tại là **split frontend/backend**:

- **Frontend:** Next.js 14 App Router, React 18, TypeScript, CSS thuần.
- **Backend:** FastAPI, SQLAlchemy 2 async, PostgreSQL + pgvector, Alembic.
- **AI/ML pipeline:** local deterministic clients + prompt contracts + AIRun audit.
- **Ingestion:** PDF/DOCX/TXT parser, public URL fetcher có SSRF guard.

```mermaid
flowchart LR
    User["User"] --> FE["Next.js frontend\n/analyze"]
    FE -->|multipart FormData| API["FastAPI backend"]
    API --> ING["Ingestion layer\nfile/text/url"]
    ING --> DB[("PostgreSQL + pgvector")]
    API --> PIPE["AI pipeline\nparse → match → optimize"]
    PIPE --> DB
    PIPE --> API
    API --> FE
```

## 2. Repository Layout

```text
job-matcher/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app + CORS + router mount
│   │   ├── api/
│   │   │   ├── deps.py             # DB session dependency re-export
│   │   │   ├── router.py           # Aggregate API routers
│   │   │   └── routes/             # health, resumes, jobs, analyze, reports, optimizations
│   │   ├── ai/
│   │   │   ├── clients/            # Local parser/optimizer clients
│   │   │   ├── guardrails/         # LocalTruthGuard
│   │   │   ├── matching/           # Skill normalization helpers
│   │   │   ├── pipeline/           # parse, match, optimize orchestration
│   │   │   ├── prompts/            # Versioned prompt contracts (*.v1.md)
│   │   │   ├── schemas/            # AI output Pydantic schemas
│   │   │   └── scoring/            # DeterministicMatchEngine
│   │   ├── core/                   # Settings + logging
│   │   ├── db/
│   │   │   ├── models/             # 13 SQLAlchemy ORM models
│   │   │   ├── repositories/       # CRUD and query helpers
│   │   │   └── session.py          # Async engine/session factory
│   │   ├── evals/                  # Evaluation runner and metrics
│   │   ├── schemas/                # API Pydantic request/response models
│   │   ├── services/
│   │   │   └── ingestion/          # Extractors, URL fetcher, storage, workflow
│   │   └── tests/                  # Unit tests
│   ├── alembic/                    # Migration environment + versions
│   ├── pyproject.toml              # Backend deps + ruff/mypy/pytest config
│   └── README.md
├── frontend/
│   ├── src/app/
│   │   ├── analyze/                # Live upload/link analyze workflow
│   │   ├── diagnostics/            # Diagnostics UI
│   │   ├── reports/[id]/           # Shareable report detail route
│   │   ├── globals.css             # Design system + page styling
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── src/lib/                    # Shared JobFit API helpers and response types
│   ├── package.json
│   └── tsconfig.json
├── docs/
│   ├── prd.md
│   ├── prompt_design.md
│   ├── evaluation_plan.md
│   └── technical_architecture.md
├── infra/
│   ├── docker/                     # Backend/frontend Dockerfiles
│   └── scripts/                    # DB init script for pgvector
├── docker-compose.yml              # Local postgres + backend + frontend stack
└── .env.example
```

## 3. Runtime Components

### 3.1 Frontend

| Item | Current implementation |
| --- | --- |
| Framework | Next.js 14 App Router |
| Runtime | React 18 client/server components |
| Main workflow | `/analyze` page |
| Shareable output | `/reports/[id]` report detail page |
| Shared client layer | `src/lib/jobfit-api.ts`, `src/lib/jobfit-types.ts` |
| API base | `NEXT_PUBLIC_API_BASE_URL`, default `http://localhost:8000` |
| Styling | Vanilla CSS in `src/app/globals.css` |
| Output | Inline match preview plus shareable match report and markdown export |

The `/analyze` client sends `multipart/form-data` to `POST /api/analyze`, renders
an inline preview from the returned `AnalyzeRead` payload, and links to the
shareable `/reports/[id]` route for the persisted report.

### 3.2 Backend API

| Item | Current implementation |
| --- | --- |
| Framework | FastAPI |
| Entrypoint | `backend/app/main.py` |
| Router aggregate | `backend/app/api/router.py` |
| CORS | `BACKEND_CORS_ORIGINS` from settings |
| DB access | SQLAlchemy async `AsyncSession` dependency |
| API style | REST JSON + multipart upload endpoints |

### 3.3 Database

| Item | Current implementation |
| --- | --- |
| Primary DB | PostgreSQL 16 via `pgvector/pgvector:pg16` image |
| ORM | SQLAlchemy 2 declarative models |
| Migration | Alembic |
| JSON storage | PostgreSQL JSONB for parsed AI outputs and reports |
| Vector-ready tables | `resume_embeddings`, `job_embeddings` |

> **Important:** embedding tables and config exist, but the live matching flow
> currently uses deterministic keyword/alias scoring. Runtime vector generation
> is not wired yet.

## 4. Deployment / Local Runtime View

Local Docker Compose starts three services:

```mermaid
flowchart TB
    subgraph Compose["docker-compose.yml"]
        PG[("postgres\npgvector/pgvector:pg16\n:5432")]
        BE["backend\nuvicorn app.main:app\n:8000"]
        FE["frontend\nnext dev\n:3000"]
    end

    FE -->|NEXT_PUBLIC_API_BASE_URL| BE
    BE -->|DATABASE_URL| PG
    PG -->|healthcheck| BE
```

Key runtime notes:

- Backend container mounts `./backend:/app` for reload-friendly development.
- Frontend container mounts `./frontend:/app` and keeps `node_modules` in a
  Docker volume.
- Postgres initializes pgvector using
  `infra/scripts/create_pgvector_extension.sql`.

## 5. Tech Stack

| Layer | Technology | Notes |
| --- | --- | --- |
| Frontend | Next.js 14, React 18, TypeScript | App Router |
| Frontend styling | Vanilla CSS | Premium UI without Tailwind |
| Backend language | Python 3.11+ | `requires-python = ">=3.11"` |
| Backend framework | FastAPI 0.115+ | Async API + OpenAPI |
| ASGI server | `uvicorn[standard]` | Dev reload supported |
| Validation | Pydantic 2 + pydantic-settings | API schemas + env settings |
| ORM | SQLAlchemy 2 async | `Mapped` / `mapped_column` style |
| Migrations | Alembic | Initial foundation migration |
| DB driver | `asyncpg`, `psycopg[binary]` | Async runtime + sync eval/migration paths |
| Database | PostgreSQL + pgvector | JSONB + vector-capable schema |
| HTTP client | httpx | JD URL ingestion path |
| Document parsing | pypdf, python-docx, BeautifulSoup4, python-multipart | PDF/DOCX/TXT upload + HTML extraction |
| Local ML optional | sentence-transformers | Optional `[local-ml]` extra |
| Lint/type/test | Ruff, mypy, pytest, pytest-asyncio | Backend quality gates |

## 6. Backend Architecture

### 6.1 FastAPI application

`backend/app/main.py` performs the runtime bootstrapping:

1. Configure logging.
2. Load settings from `.env` / environment.
3. Create the FastAPI app.
4. Add CORS middleware.
5. Include the aggregate API router.

```mermaid
flowchart TD
    main["app/main.py"] --> settings["core/config.py\nSettings"]
    main --> cors["CORSMiddleware"]
    main --> router["api/router.py"]
    router --> health["routes/health.py"]
    router --> resumes["routes/resumes.py"]
    router --> jobs["routes/jobs.py"]
    router --> analyze["routes/analyze.py"]
    router --> reports["routes/match_reports.py"]
    router --> optimizations["routes/optimizations.py"]
```

### 6.2 Request layering

Backend follows a simple layered style:

```text
FastAPI route
  ↓ validates request via Pydantic/FastAPI
Service / AI pipeline function
  ↓ applies business orchestration
Repository helper / ORM model
  ↓ persists through AsyncSession
PostgreSQL
```

The route layer should stay thin. Heavy work belongs in:

- `app/services/ingestion/*` for upload, file extraction, URL extraction.
- `app/ai/pipeline/*` for parse, match and optimization orchestration.
- `app/db/repositories/*` for persistence helpers.

### 6.3 DB session lifecycle

`app/db/session.py` creates:

- `engine = create_async_engine(settings.database_url, pool_pre_ping=True)`
- `AsyncSessionLocal = async_sessionmaker(..., expire_on_commit=False)`
- `get_db_session()` async dependency

Routes receive `AsyncSession` via `Depends(get_db_session)`.

## 7. Frontend Architecture

The current frontend is intentionally lightweight and API-driven.

```mermaid
flowchart TD
    Page["/analyze/page.tsx\nserver metadata wrapper"] --> Client["analyze-client.tsx\nclient workflow"]
    Client --> State["React state\nfiles, text, mode, phase, result"]
    Client --> FormData["FormData builder"]
    FormData --> API["POST /api/analyze"]
    API --> Result["AnalyzeResponse"]
    Result --> UI["score, evidence, gaps, suggestions"]
```

### 7.1 `/analyze` flow

`frontend/src/app/analyze/analyze-client.tsx` owns the UX state:

- `resumeFile` or `resumeText`
- `jobInputType`: `text`, `url`, or `file`
- `jobText`, `jobUrl`, or `jobFile`
- `phase`: `idle`, `uploading`, `analyzing`, `done`, `error`
- `result`: typed `AnalyzeResponse`

On submit, it builds `FormData` and calls:

```text
POST {NEXT_PUBLIC_API_BASE_URL}/api/analyze
```

### 7.2 Result rendering

The page renders the backend response inline:

- overall score and confidence
- score breakdown JSON
- strengths, gaps, recommendations
- evidence rows from `match_evidence`
- optimized resume suggestion cards
- truth guard status per rewrite suggestion

## 8. Data Model

### 8.1 ER overview

```mermaid
erDiagram
    USERS ||--o{ RESUMES : owns
    USERS ||--o{ JOBS : owns
    RESUMES ||--o{ MATCH_REPORTS : evaluated_by
    JOBS ||--o{ MATCH_REPORTS : target_for
    MATCH_REPORTS ||--o{ MATCH_EVIDENCE : contains
    MATCH_REPORTS ||--o{ OPTIMIZED_RESUMES : produces
    OPTIMIZED_RESUMES ||--o{ REWRITE_SUGGESTIONS : contains
    RESUMES ||--o{ RESUME_EMBEDDINGS : has
    JOBS ||--o{ JOB_EMBEDDINGS : has
    AI_RUNS ||--o{ AI_OUTPUTS : records
    EVAL_RUNS ||--o{ EVAL_RESULTS : records
```

### 8.2 Core ORM models

| Model | Table | Purpose |
| --- | --- | --- |
| `User` | `users` | Optional owner. Auth is not active yet. |
| `Resume` | `resumes` | Raw resume text, source metadata, parsed JSON. |
| `Job` | `jobs` | Raw JD text/URL metadata, parsed JSON. |
| `MatchReport` | `match_reports` | Overall score, breakdown, ATS report, explanation. |
| `MatchEvidence` | `match_evidence` | Per requirement/skill evidence row. |
| `OptimizedResume` | `optimized_resumes` | Job-specific optimized resume draft. |
| `RewriteSuggestion` | `rewrite_suggestions` | One rewrite suggestion + truth guard decision. |
| `AIRun` | `ai_runs` | Audit row for parse/optimizer/truth-guard calls. |
| `AIOutput` | `ai_outputs` | Raw structured output for an AIRun. |
| `ResumeEmbedding` | `resume_embeddings` | Vector-ready resume section storage. |
| `JobEmbedding` | `job_embeddings` | Vector-ready job requirement storage. |
| `EvalRun` | `eval_runs` | One evaluation CLI run. |
| `EvalResult` | `eval_results` | One metric result from an eval run. |

### 8.3 Important data choices

- IDs are string UUIDs generated by ORM defaults.
- `session_id` is used to correlate anonymous workflow artifacts.
- `parsed_json`, report breakdowns and AI outputs use JSONB.
- `match_reports` has a unique constraint on `(resume_id, job_id)`.
- `deleted_at` exists for soft-delete style fields on resume/job.
- `user_id` is nullable because current UX does not implement auth.

## 9. Ingestion Architecture

The ingestion layer is under `backend/app/services/ingestion/`.

```mermaid
flowchart TD
    Input["Resume/JD input\nfile, text, url"] --> Validate["Validate size/type/source"]
    Validate --> Extract["Extract normalized text"]
    Extract --> Store["Persist upload bytes\nwhen file input"]
    Store --> Record["Create Resume or Job row"]
    Record --> Analyze["Optional parse or one-shot analysis"]
```

### 9.1 File upload ingestion

Supported upload types:

- PDF
- DOCX
- TXT
- Markdown/plain text

Key functions:

| Function | Responsibility |
| --- | --- |
| `read_limited_upload()` | Enforce `MAX_UPLOAD_BYTES`. |
| `extract_uploaded_text()` | Dispatch by file/content type. |
| `extract_pdf_text()` | Extract text using `pypdf`. |
| `extract_docx_text()` | Extract paragraphs and table cells using `python-docx`. |
| `extract_txt_text()` | Decode text with UTF-8/UTF-8-SIG/CP1252/Latin-1 fallback. |
| `validate_extracted_text()` | Normalize whitespace and reject too-short content. |
| `save_upload_bytes()` | Store original upload bytes under `UPLOAD_STORAGE_DIR`. |

### 9.2 JD URL ingestion

`fetch_job_description_from_url()` supports public JD pages.

Security and reliability constraints:

- Only `http` and `https` URLs are accepted.
- Hostname DNS resolution is checked before fetch.
- Private, loopback, link-local, multicast, reserved and unspecified IPs are blocked.
- Redirects are limited and the final URL is revalidated.
- Response size is capped by `MAX_URL_RESPONSE_BYTES`.
- Timeout is controlled by `URL_FETCH_TIMEOUT_SECONDS`.
- Allowed content types are HTML, XHTML and plain text.
- BeautifulSoup removes scripts, styles, forms, nav/header/footer before text extraction.

### 9.3 One-shot analyze endpoint

`POST /api/analyze` accepts multipart input:

```text
resume_file OR resume_text
job_input_type = text | url | file
job_text OR job_url OR job_file
optional resume_title, job_title, company, session_id
```

It returns a single payload containing:

- `resume`
- `job`
- `match_report`
- `optimization`

## 10. AI Pipeline

The live backend AI pipeline is local and deterministic-first.
Although env vars for Gemini/OpenAI/Anthropic exist, current pipeline functions
instantiate local clients directly.

```mermaid
sequenceDiagram
    participant UI as Frontend /analyze
    participant API as POST /api/analyze
    participant ING as Ingestion workflow
    participant PARSE as Parsing pipeline
    participant MATCH as DeterministicMatchEngine
    participant OPT as Resume optimizer
    participant GUARD as Truth guard
    participant DB as PostgreSQL

    UI->>API: multipart resume + JD input
    API->>ING: create resume/job from file, text or URL
    ING->>DB: persist Resume + Job
    API->>PARSE: parse_resume_record + parse_job_record
    PARSE->>DB: parsed_json + AIRun + AIOutput
    API->>MATCH: create_match_report_record
    MATCH->>DB: MatchReport + MatchEvidence
    API->>OPT: optimize_resume_for_match
    OPT->>GUARD: evaluate each suggestion
    OPT->>DB: OptimizedResume + RewriteSuggestion + AIRun rows
    API-->>UI: AnalyzeRead response
```

### 10.1 Parsing

Entry functions:

- `parse_resume_record(session, resume)`
- `parse_job_record(session, job)`

Current clients:

- `LocalResumeParserClient`
- `LocalJobParserClient`

Outputs are validated into AI schemas and persisted to:

- `resumes.parsed_json`
- `jobs.parsed_json`
- `ai_runs`
- `ai_outputs`

### 10.2 Matching

Entry function:

- `create_match_report_record(session, resume, job)`

The matching pipeline:

1. Validate `resume.parsed_json` into `ResumeExtraction`.
2. Validate `job.parsed_json` into `JobExtraction`.
3. Run `DeterministicMatchEngine.compute()`.
4. Persist one `MatchReport`.
5. Persist many `MatchEvidence` rows.

Matching is deterministic and does not create an `AIRun`.

### 10.3 Optimization

Entry function:

- `optimize_resume_for_match(session, resume, job, match_report)`

The optimizer:

1. Builds an optimizer prompt from resume/job/report JSON.
2. Runs `LocalResumeOptimizer`.
3. Creates one optimizer `AIRun` and `AIOutput`.
4. Runs `LocalTruthGuard` for each suggestion.
5. Creates one truth-guard `AIRun` and `AIOutput` per suggestion.
6. Persists `OptimizedResume` and `RewriteSuggestion` rows.

## 11. Scoring Engine

Source: `backend/app/ai/scoring/match_engine.py`.

### 11.1 Score weights

```python
SKILL_WEIGHT = 0.5
REQUIREMENT_WEIGHT = 0.3
EXPERIENCE_WEIGHT = 0.1
LANGUAGE_WEIGHT = 0.1
```

Final score:

```text
overall_score = round(weighted_sum * 100)
```

### 11.2 Score band semantics

| Score | Meaning in summary |
| --- | --- |
| `>= 80` | strong deterministic fit |
| `>= 60` | promising deterministic fit |
| `< 60` | limited deterministic fit |

### 11.3 Evidence semantics

| Concept | Meaning |
| --- | --- |
| `match_type` | How evidence was found: exact, alias/hybrid, fuzzy, missing. |
| `match_status` | How strong the match is: strong, partial, weak, missing. |
| `similarity_score` | Numeric evidence similarity/overlap signal. |
| `confidence` | Heuristic confidence for the evidence row. |

### 11.4 Report JSON shape

`MatchReport.breakdown_json` contains:

```json
{
  "skills": { "score": 0, "matched": [], "missing": [] },
  "requirements": { "score": 0, "evaluated": 0 },
  "experience": { "score": 0, "years": null },
  "languages": { "score": 0, "matched": [] }
}
```

`MatchReport.ats_report_json` contains:

```json
{
  "keywords_matched": [],
  "keywords_missing": [],
  "coverage_ratio": 0.0,
  "warnings": []
}
```

Supported language detection is centralized in `backend/app/ai/languages.py` and currently
covers these canonical labels:

| Canonical label | Example aliases |
| --- | --- |
| English | `english`, `tiếng anh`, `英語`, `英语` |
| Vietnamese | `vietnamese`, `tiếng việt`, `ベトナム語`, `越南语` |
| Chinese | `chinese`, `mandarin`, `tiếng trung`, `中国語`, `中文` |
| Japanese | `japanese`, `tiếng nhật`, `nihongo`, `日本語` |

The local resume parser uses the same helper to extract candidate languages, and
the match engine uses it to detect language requirements from job summary,
responsibilities, skills, and requirement text.

## 12. Truth Guard

Source: `backend/app/ai/guardrails/truth_guard.py`.

Truth Guard prevents resume rewrite suggestions from adding unsupported claims.
It compares important keywords in the suggested rewrite against parsed resume
evidence.

### 12.1 Truth statuses

| Status | Meaning | Resulting optimization status impact |
| --- | --- | --- |
| `safe` | Suggestion appears grounded in resume evidence. | Optimized resume can remain `draft`. |
| `needs_review` | Suggestion adds wording not directly supported. | Optimized resume becomes `review_recommended`. |
| `unsupported` | Suggestion introduces high-impact unsupported claims. | Optimized resume becomes `needs_review`. |

### 12.2 Audit trail

Each `rewrite_suggestions` row stores:

- `truth_status`
- `new_claims_json`
- `guardrail_reason`
- `generated_by_ai_run_id`
- user decision fields: `decision`, `accepted_by_user`, `decided_at`

## 13. Observability

The backend records AI-adjacent operations in `ai_runs` and `ai_outputs`.

### 13.1 AIRun captures

| Category | Fields |
| --- | --- |
| Identity | `task_type`, `status`, `provider`, `model_name` |
| Prompt trace | `prompt_name`, `prompt_version`, `schema_version`, `temperature` |
| Input trace | `input_hash`, `input_summary_json` |
| Cost/token placeholders | `input_token_count`, `output_token_count`, `total_token_count`, `cost_usd` |
| Performance | `latency_ms`, `started_at`, `completed_at` |
| Validation | `validation_status`, `validation_errors` |
| Errors | `error_type`, `error_message`, `retry_count` |

### 13.2 Diagnostics endpoints

Diagnostics endpoints return AI runs by session:

- `GET /api/resumes/{id}/parse-diagnostics`
- `GET /api/jobs/{id}/parse-diagnostics`

## 14. API Surface

Routes are mounted through `backend/app/api/router.py`.

| Method | Path | Purpose | Source |
| --- | --- | --- | --- |
| `GET` | `/health` | Liveness check | `routes/health.py` |
| `POST` | `/api/resumes` | Create resume from text | `routes/resumes.py` |
| `POST` | `/api/resumes/upload` | Upload resume PDF/DOCX/TXT/MD | `routes/resumes.py` |
| `GET` | `/api/resumes/{id}` | Read resume | `routes/resumes.py` |
| `POST` | `/api/resumes/{id}/parse` | Parse resume | `routes/resumes.py` |
| `GET` | `/api/resumes/{id}/parse-diagnostics` | Resume parse AIRuns | `routes/resumes.py` |
| `POST` | `/api/jobs` | Create JD from text | `routes/jobs.py` |
| `POST` | `/api/jobs/upload` | Upload JD PDF/DOCX/TXT/MD | `routes/jobs.py` |
| `POST` | `/api/jobs/from-url` | Fetch public JD URL | `routes/jobs.py` |
| `GET` | `/api/jobs/{id}` | Read job | `routes/jobs.py` |
| `POST` | `/api/jobs/{id}/parse` | Parse job | `routes/jobs.py` |
| `GET` | `/api/jobs/{id}/parse-diagnostics` | Job parse AIRuns | `routes/jobs.py` |
| `POST` | `/api/analyze` | One-shot ingest → parse → match → optimize | `routes/analyze.py` |
| `POST` | `/api/match-reports` | Create/read match report for resume + job | `routes/match_reports.py` |
| `GET` | `/api/match-reports/{id}` | Read match report + evidence | `routes/match_reports.py` |
| `POST` | `/api/optimizations` | Generate optimized resume | `routes/optimizations.py` |
| `GET` | `/api/optimizations/{id}` | Read optimized resume + suggestions | `routes/optimizations.py` |

Common validation behavior:

- Missing resume/job records return `404`.
- Creating match/optimization without parsed JSON returns `409`.
- Ingestion validation failures return `422`.

## 15. Configuration

Settings are loaded by `app/core/config.py` via `pydantic-settings`.
The default env file is `.env`; examples live in `.env.example`.

| Env var | Default | Purpose |
| --- | --- | --- |
| `APP_ENV` | `development` | Environment name. |
| `LOG_LEVEL` | `INFO` | Logging level. |
| `DATABASE_URL` | `postgresql+asyncpg://jobfit:jobfit@localhost:5432/jobfit` | Async runtime DB URL. |
| `SYNC_DATABASE_URL` | `postgresql+psycopg://jobfit:jobfit@localhost:5432/jobfit` | Sync DB URL for Alembic/evals. |
| `BACKEND_CORS_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins. |
| `AI_PROVIDER` | `gemini` | Provider setting exists; live pipeline currently uses local clients. |
| `GEMINI_API_KEY` | empty | Future/provider integration key. |
| `OPENAI_API_KEY` | empty | Future/provider integration key. |
| `ANTHROPIC_API_KEY` | empty | Future/provider integration key. |
| `EMBEDDING_PROVIDER` | `local` | Embedding config; runtime matching not wired to embeddings yet. |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Intended local embedding model. |
| `EMBEDDING_DIMENSION` | `384` | Must match vector columns. |
| `UPLOAD_STORAGE_DIR` | `storage/uploads` | Local upload storage root. |
| `MAX_UPLOAD_BYTES` | `10000000` | Upload size limit in bytes. |
| `URL_FETCH_TIMEOUT_SECONDS` | `10` | JD URL fetch timeout. |
| `MAX_URL_RESPONSE_BYTES` | `2000000` | JD URL response size cap. |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Frontend API base URL. |

## 16. Security and Reliability

### 16.1 Implemented safeguards

- Upload byte limit enforced before extraction.
- Unsupported file types are rejected.
- Very short extracted text is rejected before AI pipeline execution.
- Public JD URL ingestion includes SSRF-oriented host/IP checks.
- URL response size, timeout and redirect behavior are bounded.
- Parser/optimizer/truth-guard outputs are persisted with audit records.
- Match report creation validates that resume/job have parsed JSON.

### 16.2 Current non-goals / gaps

- No user authentication or authorization is active.
- No antivirus scanning for uploaded files.
- No OCR for scanned PDFs.
- Local upload storage is not exposed through signed URLs.
- External LLM provider selection is configured but not wired into live pipeline.
- Vector embedding retrieval is schema-ready but not active in matching.
- No background job queue; one-shot analyze runs synchronously in the request.

## 17. Testing and Quality Gates

Backend configuration:

- Ruff: line length 100, rules `E/F/I/B/UP`.
- mypy: strict mode.
- pytest: async mode auto, tests under `app/tests`.

Recent verification for the ingestion/analyze upgrade:

| Check | Result |
| --- | --- |
| Backend tests | `19 passed` |
| Backend Ruff | `All checks passed` |
| Backend mypy | `Success: no issues found in 85 source files` |
| Frontend TypeScript | `tsc --noEmit` passed |
| `/analyze` browser load | HTTP 200 in Next dev server |

Note: frontend `npm run lint` currently opens Next.js first-time ESLint setup
because an ESLint config has not been created yet.

## 18. Evaluation Harness

Evaluation code lives under `backend/app/evals/`.

Primary command:

```bash
python -m app.evals.runner --task all --dataset smoke
```

Supported tasks include:

- `resume_parser`
- `job_parser`
- `matching`
- `truth_guard`
- `all`

Evaluation persistence:

- `eval_runs`
- `eval_results`

Report output pattern:

```text
app/evals/reports/eval_report_{dataset}.md
```

## 19. Known Architecture Decisions

| Decision | Rationale |
| --- | --- |
| Split frontend/backend | Keeps AI/ML logic server-side and frontend thin. |
| PostgreSQL + JSONB | Easy persistence for evolving AI output schemas. |
| pgvector-ready schema | Allows future semantic retrieval without replacing DB. |
| Local deterministic clients | Makes MVP testable, cheap and reproducible. |
| AIRun audit model | Enables prompt/output traceability and diagnostics. |
| Truth guard before display | Reduces risk of fabricated resume claims. |
| Synchronous one-shot analyze | Simpler UX/MVP; queue can be added later. |

## 20. Roadmap Hooks

The architecture leaves room for these upgrades:

1. Wire `AI_PROVIDER` to real OpenAI/Gemini/Anthropic clients.
2. Add async background jobs for long analyze/optimization flows.
3. Generate and query embeddings for semantic evidence retrieval.
4. Add OCR for scanned resumes/JDs.
5. Implement auth and user-owned resources.
6. Add report detail route, e.g. `/reports/[id]`.
7. Add frontend ESLint config and component-level UI tests.
8. Serve original uploads through secure signed URLs if needed.

## 21. Cross References

- Product scope: [Product Requirements](prd.md)
- Prompt contracts: [Prompt Design](prompt_design.md)
- Evaluation design: [Evaluation Plan](evaluation_plan.md)
- Backend docs: [Backend README](../backend/README.md)
- Root setup: [Project README](../README.md)
