# Product Requirements Document (PRD)

> Tài liệu product scope, đối tượng người dùng, và trạng thái build hiện tại của
> JobFit AI. Section kỹ thuật chi tiết xem trong
> [`technical_architecture.md`](technical_architecture.md), [`prompt_design.md`](prompt_design.md),
> [`evaluation_plan.md`](evaluation_plan.md).

## 1. Product Overview / Tổng quan sản phẩm

**JobFit AI** is a portfolio-grade AI/ML engineering project that scores a
candidate's resume against a target job description, explains *why* the score
came out the way it did, and produces grounded, truth-guarded resume rewrite
suggestions.

- **Tên sản phẩm:** JobFit AI — AI Job Match & Resume Optimizer
- **Loại sản phẩm:** Split-frontend/backend web app với REST API
- **Phiên bản hiện tại:** 0.3.0 (product-demo package)
- **Mục tiêu:** Present JobFit AI as a CV/portfolio-ready AI product demo:
  document ingestion, schema-first extraction, skill normalization, explainable
  scoring, truth guard, observability, evals, and polished shareable UX.

## 2. Target Users / Đối tượng người dùng

| Persona | Need | Outcome they get |
| --- | --- | --- |
| **Job seeker** | So sánh CV với JD nhanh, biết thiếu gì | Match score + strengths/gaps/recommendations |
| **Career coach** | Tư vấn candidate, cần giải thích khách quan | Evidence rows + truth-graded rewrite suggestions |
| **Recruiter (read-only)** | Lọc ứng viên match JD | Score breakdown + matched/missing skills |
| **AI/ML reviewer** | Đánh giá portfolio | Reproducible eval metrics, prompt versions, AI run logs |

## 3. MVP Scope (Built) / Phạm vi MVP đã build

Đây là các tính năng **đã chạy được trong repo hiện tại**:

### Core AI pipeline
- Resume input: pasted text hoặc upload PDF/DOCX/TXT/MD
- JD input: pasted text, upload PDF/DOCX/TXT/MD, hoặc public URL
- Schema-first LLM extraction cho cả resume và job description
- Skill normalization + alias matching (`normalize_skill` / `skill_aliases_for`)
- Deterministic evidence generation with pgvector-ready schema for future semantic retrieval
- Deterministic explainable scoring engine (weighted: skills 0.5 / req 0.3 / exp 0.1 / lang 0.1)
- Supported language matching: English, Vietnamese, Chinese, Japanese
- Truth-guard classification cho resume rewrite suggestions (safe / needs_review / unsupported)
- One-shot analyze workflow: ingest → parse → match → optimize
- Shareable report detail page with copy-link and markdown export
- Product-demo packaging: case study docs, CV summary, and demo-ready README
- AI run observability (model, prompt version, latency, cost, validation status)

### Backend API
- `POST /api/resumes` — create resume record from pasted text
- `POST /api/resumes/upload` — upload resume PDF/DOCX/TXT/MD
- `GET /api/resumes/{id}` — read resume + parsed JSON
- `POST /api/resumes/{id}/parse` — chạy LLM extraction
- `GET /api/resumes/{id}/parse-diagnostics` — list AI runs cho session
- `POST /api/jobs` — create job record from pasted text
- `POST /api/jobs/upload` — upload JD PDF/DOCX/TXT/MD
- `POST /api/jobs/from-url` — fetch/extract public JD HTML/text URL
- `GET /api/jobs/{id}` — read job + parsed JSON
- `POST /api/jobs/{id}/parse` — chạy job parser
- `GET /api/jobs/{id}/parse-diagnostics` — diagnostics
- `POST /api/analyze` — one-shot multipart ingest + parse + match + optimize
- `POST /api/match-reports` — tạo match report (idempotent qua unique constraint)
- `GET /api/match-reports/{id}` — read report + evidence rows
- `POST /api/optimizations` — tạo optimized resume (chạy truth-guard từng suggestion)
- `GET /api/optimizations/{id}` — read optimized resume
- `GET /health` — health check

### Data model
- 13 ORM tables (users, resumes, jobs, match_reports, match_evidence,
  ai_runs, ai_outputs, optimized_resumes, rewrite_suggestions,
  resume_embeddings, job_embeddings, eval_runs, eval_results)
- Alembic migration: `20260613_0001_initial_foundation.py`
- pgvector extension cho embedding columns

### Evaluation harness
- CLI runner: `python -m app.evals.runner --task all --dataset smoke`
- 4 task families: resume_parser, job_parser, matching, truth_guard
- Markdown report → `app/evals/reports/eval_report_{dataset}.md`
- Persist kết quả vào `eval_runs` + `eval_results`

### Local AI (default)
- Local regex/heuristic parsers (resume + job) — chạy offline, deterministic
- Local resume optimizer + truth guard (rule-based)
- Local embeddings config/schema reserved for future semantic retrieval (`pgvector`, 384-dim)
- Production parser/optimizer providers can be wired behind the existing env/provider abstractions

## 4. Out of Scope (Chưa build) / Tính năng ngoài phạm vi

- **Authentication / user login** — `User` table tồn tại nhưng chưa có JWT/OAuth
- **Cover letter generation** — schema reserved, chưa có prompt/UI
- **Interview prep question generation** — đề cập trong roadmap, chưa build
- **Job board scraping/crawling at scale** — chỉ fetch public JD URL đơn lẻ với SSRF guard
- **OCR cho scanned PDF** — PDF text extraction có warning, chưa chạy OCR
- **Multi-tenant billing** — `User.plan` column có nhưng chưa enforce

## 5. Build Status / Trạng thái build

| Milestone | Status | Notes |
| --- | --- | --- |
| M0 — Repo + Docker scaffold | ✅ Done | FastAPI + Next.js + Postgres + pgvector |
| M1 — DB schema + Alembic | ✅ Done | 13 tables, initial migration applied |
| M2 — Resume/Job parse pipeline | ✅ Done | Local parser + AIRun logging |
| M3 — Skill normalization + matching | ✅ Done | Deterministic match engine với evidence rows |
| M4 — Truth guard + optimization | ✅ Done | Truth-guard per suggestion, decision tracking |
| M5 — Evaluation harness | ✅ Done | Runner, datasets, metrics, markdown report |
| M6 — AI observability + diagnostics | ✅ Done | AIRun/AIOutput/EvalRun/EvalResult |
| Ingestion upgrade | ✅ Done | Resume/JD upload, JD URL fetch, one-shot analyze API |
| M7 — Frontend product polish | ✅ Done | `/analyze` workbench + `/reports/{id}` share/export report UX |
| M8 — Product demo package | ✅ Done | Demo stability scripts, product README, case study, CV summary |
| Language support | ✅ Done | English, Vietnamese, Chinese, Japanese detection for resume/JD matching |

> Xem chi tiết pipeline và stack trong [Technical Architecture](technical_architecture.md).

## 6. Cross-References

- System architecture & data model → [Technical Architecture](technical_architecture.md)
- Prompt contracts & versioning → [Prompt Design](prompt_design.md)
- Eval tasks, metrics, datasets → [Evaluation Plan](evaluation_plan.md)
- Backend service & API surface → [`../backend/README.md`](../backend/README.md)
