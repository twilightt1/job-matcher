# Technical Architecture

> Tài liệu kiến trúc kỹ thuật cho JobFit AI backend. Mô tả: stack, data model,
> AI pipeline, scoring engine, truth guard, API surface, observability, và
> evaluation harness. Nội dung phản ánh code thực tế trong `backend/`, không
> mô tả aspirational state.

## 1. Overview / Tổng quan

JobFit AI là split-frontend/backend web app. Phần AI/ML chạy hoàn toàn ở
backend; frontend gọi REST API.

```text
frontend/  Next.js product UI (skeleton, gọi backend qua CORS)
backend/   Python 3.11+ FastAPI + SQLAlchemy 2.0 (async) + Alembic + pgvector
docs/      Product, architecture, prompt, evaluation docs
infra/     Docker Compose + helper scripts
```

Service entrypoint: `backend/app/main.py` — tạo FastAPI app, cấu hình CORS,
include `api_router` (`/api/...`).

## 2. Repository Layout / Cấu trúc thư mục

```text
backend/
├── app/
│   ├── main.py                 # FastAPI app + CORS
│   ├── api/
│   │   ├── router.py           # Aggregate sub-routers
│   │   ├── deps.py             # get_db_session
│   │   └── routes/             # health, resumes, jobs, match_reports, optimizations
│   ├── core/                   # config (Settings), logging
│   ├── db/
│   │   ├── session.py          # async engine + Base + AsyncSessionLocal
│   │   ├── models/             # 13 ORM models (User, Resume, Job, MatchReport, …)
│   │   └── repositories/       # CRUD helpers (resume_repository, match_report_repository, …)
│   ├── schemas/                # Pydantic v2 request/response models
│   ├── ai/
│   │   ├── prompts/            # *.v1.md prompt files
│   │   ├── prompt_loader.py    # load_prompt_template()
│   │   ├── clients/            # Local/OpenAI/Gemini implementations
│   │   ├── matching/           # skill normalization
│   │   ├── scoring/            # DeterministicMatchEngine
│   │   ├── guardrails/         # truth_guard
│   │   ├── pipeline/           # parse_resume_record, parse_job_record,
│   │   │                       # create_match_report_record, optimize_resume_for_match
│   │   └── schemas.py          # ResumeExtraction, JobExtraction
│   └── evals/                  # runner, metrics, datasets, report
├── alembic/
│   ├── env.py
│   └── versions/20260613_0001_initial_foundation.py
├── pyproject.toml              # Project metadata + ruff + mypy
└── README.md
```

## 3. Tech Stack / Stack kỹ thuật

| Layer | Technology | Note |
| --- | --- | --- |
| Language | Python 3.11+ | `requires-python = ">=3.11"` |
| Web framework | FastAPI 0.115+ | Async, OpenAPI auto-gen |
| ASGI server | uvicorn[standard] | Dev: `uvicorn app.main:app --reload` |
| Validation | Pydantic 2.8+ + pydantic-settings | Settings qua env |
| ORM | SQLAlchemy 2.0 (async style, `Mapped`/`mapped_column`) | Không dùng Prisma |
| Migrations | Alembic 1.13+ | 1 migration: `20260613_0001_initial_foundation` |
| DB driver (async) | `asyncpg` 0.29+ | URL: `postgresql+asyncpg://…` |
| DB driver (sync, cho evals) | `psycopg[binary]` 3.2+ | URL: `postgresql+psycopg://…` |
| Vector store | PostgreSQL + `pgvector` extension | 384-dim embeddings |
| Local ML | scikit-learn 1.5+, sentence-transformers 3.0+ (opt.) | `pip install -e ".[local-ml]"` |
| HTTP client | httpx 0.27+ | Dùng cho OpenAI/Gemini/Anthropic clients |
| Lint / format | Ruff 0.5+, line-length 100, rules E/F/I/B/UP | |
| Type check | mypy 1.11+ strict mode | `strict = true`, `warn_return_any = true` |
| Test | pytest 8.3+ + pytest-asyncio 0.23+ | `asyncio_mode = "auto"` |
| Container | Docker Compose | `infra/docker-compose.yml` mount pgvector image |

## 4. Data Model / Mô hình dữ liệu

### 4.1 ER overview

```text
users (1) ──< resumes (1) ──< match_reports >── (1) jobs
                  │                │
                  │                ├──< match_evidence
                  │                └──< optimized_resumes ──< rewrite_suggestions
                  │
                  └──< resume_embeddings (vector 384)

jobs (1) ──< job_embeddings (vector 384)

ai_runs (1) ──< ai_outputs
ai_runs <── (FK) match_reports, optimized_resumes, rewrite_suggestions

eval_runs (1) ──< eval_results
```

### 4.2 ORM models (`backend/app/db/models/`)

| Model | Table | Key fields | Purpose |
| --- | --- | --- | --- |
| `User` | `users` | `id`, `email` (unique), `plan` | Optional owner (FK nullable) |
| `Resume` | `resumes` | `id`, `raw_text`, `parsed_json` (JSONB), `parse_status`, `parse_confidence` | Source text + LLM extraction |
| `Job` | `jobs` | `id`, `description`, `parsed_json` (JSONB), `parse_status`, `parse_confidence`, `seniority`, `work_mode` | Target JD + LLM extraction |
| `MatchReport` | `match_reports` | `resume_id`, `job_id` (unique together), `overall_score` (int), `breakdown_json`, `strengths_json`, `gaps_json`, `ats_report_json`, `generated_by_ai_run_id` | Deterministic match result |
| `MatchEvidence` | `match_evidence` | `match_report_id`, `requirement_id`, `job_requirement_text`, `resume_evidence_text`, `match_type`, `match_status`, `similarity_score`, `confidence` | 1 row / requirement |
| `OptimizedResume` | `optimized_resumes` | `resume_id`, `job_id`, `match_report_id`, `version_name`, `content_json`, `score_before`, `score_after`, `status` | Job-specific rewrite |
| `RewriteSuggestion` | `rewrite_suggestions` | `optimized_resume_id`, `section_type`, `original_text`, `suggested_text`, `truth_status`, `new_claims_json`, `guardrail_reason`, `decision`, `accepted_by_user` | 1 row / AI suggestion |
| `AIRun` | `ai_runs` | `task_type`, `status`, `provider`, `model_name`, `prompt_name`, `prompt_version`, `input_hash`, `output_token_count`, `cost_usd`, `latency_ms`, `validation_status`, `validation_errors` | Observability |
| `AIOutput` | `ai_outputs` | `ai_run_id`, `output_json`, `repair_attempted` | 1+ per AIRun |
| `ResumeEmbedding` | `resume_embeddings` | `resume_id`, `section_type`, `text`, `embedding` (Vector 384), `embedding_model`, `dimension` | Vector search corpus |
| `JobEmbedding` | `job_embeddings` | `job_id`, `requirement_type`, `text`, `embedding` (Vector 384) | Vector search corpus |
| `EvalRun` | `eval_runs` | `dataset_name`, `requested_task`, `status`, `summary_json`, `report_path` | 1 row / eval CLI run |
| `EvalResult` | `eval_results` | `eval_run_id`, `task_name`, `metric_name`, `metric_value`, `display_value`, `details_json` | 1 row / metric |

Enums (in `app/db/models/enums.py`): `ResumeSourceType`, `ParseStatus`,
`JobStatus`, `WorkMode`, `EmploymentType`, `Seniority`, `MatchType`,
`MatchStatus`, `AITaskType`, `AIProvider`, `AIRunStatus`, `ValidationStatus`.

## 5. AI Pipeline / Luồng AI

7 bước, mỗi bước có entry point + AIRun row tương ứng:

| # | Step | Entry function | AIRun.task_type | Prompt file |
| --- | --- | --- | --- | --- |
| 1 | Schema-first LLM extraction (resume) | `parse_resume_record` (`app/ai/pipeline/parsing.py`) | `resume_parse` | `resume_parser.v1.md` |
| 2 | Schema-first LLM extraction (job) | `parse_job_record` | `job_parse` | `job_parser.v1.md` |
| 3 | Skill normalization + alias matching | `normalize_skill_list` / `skill_aliases_for` (`app/ai/matching/normalization.py`) | — (deterministic) | — |
| 4 | Embedding-based semantic evidence retrieval | `app/ai/embedding/*` (writes to `resume_embeddings` / `job_embeddings`) | `embedding` | (local sentence-transformers) |
| 5 | Deterministic explainable scoring | `DeterministicMatchEngine.compute` (`app/ai/scoring/match_engine.py`) | — (deterministic) | — |
| 6 | Grounded resume rewrite generation | `LocalResumeOptimizer.optimize` | `resume_optimize` | `resume_optimizer.v1.md` |
| 7 | Truth guard classification (1 call / suggestion) | `LocalTruthGuard.evaluate` | `truth_guard` | `truth_guard.v1.md` |
| (8) | Match explainer narration (planned) | TBD | `match_explain` | `match_explainer.v1.md` |
| (extra) | JSON repair on invalid output | `json_repair.v1.md` driven | `json_repair` | `json_repair.v1.md` |

Step (8) is planned but not wired into the live pipeline yet — engine
currently builds explanation in code (`_build_summary`).

## 6. Scoring Engine / Engine chấm điểm

Source: `backend/app/ai/scoring/match_engine.py:51` — class
`DeterministicMatchEngine`.

### 6.1 Weights

```python
SKILL_WEIGHT        = 0.5   # normalized overlap of required + preferred skills
REQUIREMENT_WEIGHT  = 0.3   # aggregate of per-requirement evidence (strong=1.0, partial=0.6)
EXPERIENCE_WEIGHT   = 0.1   # ratio of total_years vs. seniority target (senior=5y, mid=3y, else=1y)
LANGUAGE_WEIGHT     = 0.1   # matched spoken languages / required languages
```

`overall_score = round((weighted_sum) * 100)` — integer 0..100.

### 6.2 Score bands

```python
def classify_score_band(score: int) -> ScoreBand:
    if score >= 80: return "strong_match"
    if score >= 60: return "partial_match"
    return "weak_match"
```

Verdict phrasing in `_build_summary`:

| Score | Verdict |
| --- | --- |
| ≥ 80 | "strong" |
| ≥ 60 | "promising" |
| < 60 | "limited" |

### 6.3 MatchType vs MatchStatus

| `MatchType` (how it was matched) | `MatchStatus` (how well it was matched) |
| --- | --- |
| `EXACT`, `ALIAS`, `FUZZY`, `SEMANTIC`, `HYBRID`, `MISSING` | `STRONG`, `PARTIAL`, `WEAK`, `MISSING` |

Evidence rows are persisted in `match_evidence` với:

- `match_type = EXACT` nếu `normalize_skill(matched) == skill`, ngược lại `HYBRID`
- `similarity_score = 1.0` cho exact, `0.84` cho hybrid
- `confidence = 0.82` cho matched, `0.55` cho missing

### 6.4 Output breakdown

`MatchReport.breakdown_json`:

```json
{
  "skills":       { "score": 0-100, "matched": [...], "missing": [...] },
  "requirements": { "score": 0-100, "evaluated": <int> },
  "experience":   { "score": 0-100, "years": <float|null> },
  "languages":    { "score": 0-100, "matched": [...] }
}
```

`MatchReport.ats_report_json`:

```json
{
  "keywords_matched": [...],
  "keywords_missing": [...],
  "coverage_ratio": 0.0-1.0,
  "warnings": [<top 4 gap messages>]
}
```

`MatchReport.analysis_confidence` formula:

```python
clamp(0.6 + 0.15*(resume_conf + job_conf) + 0.1*req_score, max=0.97)
```

## 7. Truth Guard / Bộ chặn "bịa"

Source: `backend/app/ai/guardrails/truth_guard.py` (`LocalTruthGuard`).

### 7.1 Decision classes (output)

| Truth status | Meaning | DB column `rewrite_suggestions.truth_status` default |
| --- | --- | --- |
| `safe` | Suggestion chỉ rephrase evidence đã có trong resume | `safe` |
| `needs_review` | Suggestion có thể đúng nhưng cần user xác nhận | (set by guard) |
| `unsupported` | Suggestion bịa metric, tool, ownership, scale, award | (set by guard) |

Truth status được lưu ở `rewrite_suggestions.truth_status` cùng
`new_claims_json` (audit trail) và `guardrail_reason` (giải thích LLM đưa ra).

### 7.2 Decision flow

Mỗi `RewriteSuggestionDraft` đi qua `LocalTruthGuard.evaluate()` độc lập.
Decision flow:

```text
optimizer draft
  ↓
LocalTruthGuard.evaluate (1 call / suggestion)
  ↓
[truth_status = "safe"]            → rewrite_suggestions.truth_status = "safe"
[truth_status = "needs_review"]    → rewrite_suggestions.truth_status = "needs_review"
[truth_status = "unsupported"]     → rewrite_suggestions.truth_status = "unsafe"
                                     + new_claims_json recorded
  ↓
user can accept / reject via decision column
```

## 8. Embeddings / Vector search

- **Storage:** PostgreSQL + `pgvector` extension (`CREATE EXTENSION IF NOT EXISTS vector;`)
- **Tables:** `resume_embeddings`, `job_embeddings`
- **Dimension:** 384 (matches `EMBEDDING_DIMENSION` default)
- **Default model:** `sentence-transformers/all-MiniLM-L6-v2` (local)
- **Config keys (`app/core/config.py`):** `embedding_provider`, `embedding_model`, `embedding_dimension`
- **Optional install:** `pip install -e ".[local-ml]"` (khi cần chạy local embedding)

## 9. Observability — AI Runs

Every LLM extraction, embedding, optimizer, truth-guard, repair call ghi 1
`AIRun` row + 1+ `AIOutput` rows.

Captured per run (xem `app/db/models/ai_run.py`):

- Identity: `task_type`, `status`, `provider`, `model_name`
- Reproducibility: `prompt_name`, `prompt_version`, `schema_version`, `temperature`
- Input trace: `input_hash` (SHA-256), `input_summary_json` (preview, char count, ids)
- Cost: `input_token_count`, `output_token_count`, `total_token_count`, `cost_usd`
- Perf: `latency_ms`, `started_at`, `completed_at`
- Validation: `validation_status` (not_validated/valid/invalid/repaired), `validation_errors` (JSONB)
- Error: `error_type`, `error_message`, `retry_count`

Per output: `output_json` or `output_text`, `validation_status`,
`validation_errors`, `repair_attempted`, `metadata_json`.

Diagnostics endpoint: `GET /api/resumes/{id}/parse-diagnostics` trả về
`{ ai_runs: [...] }` cho session của resume.

## 10. API Surface / Danh sách endpoint

Base path: `/api`. Source: `backend/app/api/router.py` aggregate 5 sub-routers.

| Method | Path | Purpose | Source file |
| --- | --- | --- | --- |
| GET | `/health` | Liveness check | `routes/health.py` |
| POST | `/api/resumes` | Create resume record | `routes/resumes.py` |
| GET | `/api/resumes/{id}` | Read resume + parsed JSON | `routes/resumes.py` |
| POST | `/api/resumes/{id}/parse` | Trigger LLM extraction (idempotent) | `routes/resumes.py` |
| GET | `/api/resumes/{id}/parse-diagnostics` | List AIRuns cho session | `routes/resumes.py` |
| POST | `/api/jobs` | Create job record | `routes/jobs.py` |
| GET | `/api/jobs/{id}` | Read job + parsed JSON | `routes/jobs.py` |
| POST | `/api/jobs/{id}/parse` | Trigger job extraction | `routes/jobs.py` |
| GET | `/api/jobs/{id}/parse-diagnostics` | List AIRuns cho session | `routes/jobs.py` |
| POST | `/api/match-reports` | Compute match (unique constraint dedup) | `routes/match_reports.py` |
| GET | `/api/match-reports/{id}` | Read report + evidence rows | `routes/match_reports.py` |
| POST | `/api/optimizations` | Generate rewrite + run truth-guard | `routes/optimizations.py` |
| GET | `/api/optimizations/{id}` | Read optimized resume + suggestions | `routes/optimizations.py` |

Validation rule chung: `POST /api/match-reports` và
`POST /api/optimizations` trả về **HTTP 409** nếu `resume.parsed_json` /
`job.parsed_json` rỗng (chưa parse).

## 11. Evaluation Harness

Xem chi tiết tại [Evaluation Plan](evaluation_plan.md). Tóm tắt:

- `python -m app.evals.runner --task all --dataset smoke`
- Tasks: `resume_parser`, `job_parser`, `matching`, `truth_guard`, `all`
- Metrics: xem `app/evals/metrics.py` (`ParsingMetrics`, `MatchingMetrics`, `TruthGuardMetrics`)
- Persistence: `eval_runs` + `eval_results` tables
- Report: `app/evals/reports/eval_report_{dataset}.md`

## 12. Configuration / Biến môi trường

Load bởi `app/core/config.py` (`Settings(BaseSettings)`). Env file: `.env`.

| Env var | Default | Mục đích |
| --- | --- | --- |
| `APP_ENV` | `development` | Tên môi trường |
| `LOG_LEVEL` | `INFO` | Log level |
| `DATABASE_URL` | `postgresql+asyncpg://jobfit:jobfit@localhost:5432/jobfit` | Async DB URL (runtime) |
| `SYNC_DATABASE_URL` | `postgresql+psycopg://jobfit:jobfit@localhost:5432/jobfit` | Sync URL (Alembic + evals) |
| `BACKEND_CORS_ORIGINS` | `["http://localhost:3000"]` | CSV list, dùng cho CORS |
| `AI_PROVIDER` | `gemini` | `gemini` / `openai` / `anthropic` / `local` |
| `GEMINI_API_KEY` | (None) | |
| `OPENAI_API_KEY` | (None) | |
| `ANTHROPIC_API_KEY` | (None) | |
| `EMBEDDING_PROVIDER` | `local` | `local` (sentence-transformers) |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | |
| `EMBEDDING_DIMENSION` | `384` | Phải match với `Vector(N)` column |

## 13. Cross-References

- PRD scope & build status → [Product Requirements](prd.md)
- Per-prompt contracts & versioning → [Prompt Design](prompt_design.md)
- Eval tasks, metrics, datasets → [Evaluation Plan](evaluation_plan.md)
