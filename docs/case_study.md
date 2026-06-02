# JobFit AI Case Study

## Summary

JobFit AI is a product-style AI engineering project that helps a candidate compare a resume against a target job description, understand the fit, and improve the resume without inventing unsupported claims.

The project is designed as a CV/portfolio product demo: polished enough to show as a product, but scoped tightly enough to highlight engineering decisions instead of SaaS features like billing or user management.

## Problem

Job seekers often face three problems:

1. They do not know which parts of their resume match a specific job.
2. Generic resume feedback tools rarely explain the evidence behind a score.
3. AI rewrite tools can hallucinate achievements that are not supported by the original resume.

For an AI engineering portfolio, this is a strong product problem because it requires more than a chat UI. It needs document ingestion, structured extraction, scoring, evidence, guardrails, and a clear user workflow.

## Solution

JobFit AI turns a resume and job description into a structured, explainable report.

The user flow:

1. Open the no-account analyze workbench.
2. Use built-in demo data or upload/paste real resume and JD sources.
3. Submit a single analysis request.
4. Backend ingests and parses the source material.
5. Match engine creates a score breakdown and evidence rows.
6. Optimizer proposes resume rewrites.
7. Truth guard labels each suggestion as safe, needs review, or unsupported.
8. Frontend renders a shareable report page with export actions.

## What I Built

### Product UI

- Landing page explaining the value proposition and system capabilities.
- `/analyze` workbench with resume/JD input modes and a one-click demo path.
- Inline generated report preview after analysis.
- `/reports/[id]` shareable report detail page with:
  - overall score
  - confidence
  - score breakdown
  - ATS keyword coverage
  - strengths/gaps/recommendations
  - requirement-level evidence rows
  - truth-guarded rewrite cards
  - copy-link, refresh, and markdown export actions

### Backend Pipeline

- FastAPI REST API with multipart upload support.
- Resume and JD ingestion from text, file upload, and public JD URL.
- SSRF-aware public URL fetcher.
- Local deterministic parsers for offline/reproducible development.
- Match report creation with idempotent report constraints.
- Optimization generation tied to match reports.
- AI run/output observability models.

### Matching and Guardrails

- Skill normalization and alias matching.
- Weighted deterministic score model:
  - skills
  - job requirements
  - experience
  - language coverage
- Supported language matching for English, Vietnamese, Chinese, and Japanese.
- Persisted match evidence rows for explainability.
- Truth guard status on each rewrite suggestion.
- Guardrail reason field to explain risky suggestions.

### Documentation and Demo Packaging

- Product README with demo flow and CV positioning.
- PRD documenting scope and build status.
- Technical architecture with repository/runtime details.
- Evaluation plan and smoke evaluation harness.
- CV-ready summary and interview talking points.

## Architecture

```text
User
  -> Next.js /analyze
  -> FastAPI POST /api/analyze
  -> ingestion service
  -> parser pipeline
  -> deterministic match engine
  -> optimizer + truth guard
  -> PostgreSQL records
  -> Next.js /reports/{id}
```

Key persistence objects:

- `resumes`
- `jobs`
- `match_reports`
- `match_evidence`
- `optimized_resumes`
- `rewrite_suggestions`
- `ai_runs`
- `ai_outputs`
- `eval_runs`
- `eval_results`

## Technical Decisions

### Keep scoring deterministic for the demo

The matching score is deterministic instead of pure LLM-generated text. This makes the product easier to test, explain, and debug.

### Separate extraction, scoring, and optimization

The pipeline avoids one giant prompt. Each stage has a clear responsibility:

- extraction turns messy inputs into structured JSON
- scoring converts structured signals into explainable metrics
- optimization generates user-facing rewrite suggestions
- truth guard checks whether suggestions stay grounded

### Persist evidence, not just final text

The product stores match evidence rows so the report can explain why the score exists. This is stronger than showing only a percentage.

### Productize without overbuilding SaaS

Authentication, billing, and user history are intentionally out of scope. The goal is a strong product demo for CV/portfolio use, not a commercial SaaS launch.

## Challenges

### AI hallucination risk

Resume rewriting can easily invent claims. The project mitigates this with `truth_status` and `guardrail_reason` fields on every suggestion.

### Real-world input formats

Users may have PDFs, DOCX files, pasted text, or job links. The ingestion layer handles these formats behind a single analyze workflow.

### Demo reliability

A portfolio project must be easy to run. The frontend now includes clean/verify scripts and a richer built-in demo sample for fast validation.

## Results

The current product demo supports:

- no-account analysis workflow
- shareable report route
- markdown export
- explainable score breakdown
- persisted evidence rows
- guarded rewrite suggestions
- four-language matching support: English, Vietnamese, Chinese, Japanese
- frontend typecheck/build verification
- product documentation suitable for CV/portfolio review

## Future Improvements

These are optional and should only be added if they improve the portfolio story:

1. Deploy a public demo with managed Postgres.
2. Add real LLM provider wiring behind the existing provider abstraction.
3. Add a curated demo report seed for static showcase mode.
4. Wire runtime embedding retrieval using the existing pgvector-ready schema.
5. Add a short demo video/GIF to the README.

## Interview Talking Points

- Why deterministic scoring is safer than an opaque LLM score.
- How truth-guarding reduces resume hallucination risk.
- How the data model supports auditability and future provider swapping.
- Why the product avoids auth/billing at this stage.
- How the project balances product polish with engineering depth.
