# JobFit AI — CV / Portfolio Summary

## One-line Summary

Built JobFit AI, an AI-powered resume-to-job matching system with schema-first OpenAI-compatible LLM pipelines, JSON-repair self-correction, pgvector-backed semantic matching, truth-guarded resume optimization, and CI-backed evaluation reporting.

## CV Bullet Version

- Built **JobFit AI**, a product-style AI resume matching app using **Next.js, FastAPI, PostgreSQL/pgvector, SQLAlchemy, and TypeScript**.
- Implemented schema-first OpenAI-compatible LLM extraction/optimization with strict Pydantic validation, JSON-repair self-correction, and local fallback clients.
- Added pgvector-backed resume/JD embeddings using local sentence-transformer indexing plus deterministic fallback embeddings for clone-and-run demos.
- Designed explainable hybrid semantic/lexical match reports with ATS coverage, requirement-level evidence, semantic similarity scores, and shareable `/reports/{id}` pages.
- Built truth-guarded resume rewrite suggestions with local and LLM-entailment guard paths to reduce unsupported or hallucinated claims.
- Added an eval harness with parser/matching/semantic/truth-guard metrics, model/provider documentation, and GitHub Actions CI quality gates.

## Short Portfolio Description

JobFit AI is an AI engineering product demo that helps job seekers understand how well a resume matches a specific job description. Users can paste text or upload documents, run a one-click analysis, and receive a shareable report showing match score, strengths, gaps, ATS keywords, evidence rows, and guarded resume rewrite suggestions.

The project demonstrates practical AI product engineering rather than a simple chat wrapper: document ingestion, schema-first parsing, JSON-repair self-correction, provider abstractions, pgvector-backed embedding storage, hybrid semantic/lexical matching, persisted evidence, truth guardrails, observability-friendly data models, eval reporting, model/provider docs, CI gates, and a polished Next.js interface.

## Technical Highlights

- **Frontend:** Next.js 14 App Router, React, TypeScript, vanilla CSS design system.
- **Backend:** FastAPI, Pydantic, SQLAlchemy async, Alembic.
- **Database:** PostgreSQL with JSONB report storage and pgvector embedding tables.
- **AI pipeline:** OpenAI-compatible LLM abstraction, strict Pydantic schemas, JSON-repair loop, local fallback clients, local sentence-transformer embeddings, deterministic fallback embeddings.
- **Safety:** truth-guard classification for unsupported resume claims with local and LLM-entailment paths.
- **Explainability:** persisted match evidence rows connected to job requirements with lexical/semantic/hybrid match types.
- **Evaluation:** parser/matching/semantic/truth-guard eval harness with markdown reports, model card, provider matrix, and CI smoke run.
- **Demo UX:** no-account analyze page, shareable report route, copy link, markdown export.

## Recruiter-friendly Pitch

I built JobFit AI to show that I can turn an AI concept into a real product workflow. It is not just a chatbot: the system ingests messy resume/JD inputs, structures them through schema-first parsing, scores the match with semantic and lexical evidence, generates resume improvements, and uses truth guardrails to avoid unsupported claims. I also added eval reports, CI quality gates, model/provider docs, and a polished frontend experience so the project reads like production-minded AI engineering rather than a prompt demo.

## Interview Deep-dive Topics

### Why this architecture?

I separated ingestion, parsing, matching, optimization, and truth-guarding so each stage is testable and explainable. This is easier to debug than a single giant prompt.

### Why hybrid scoring?

The final score remains auditable because lexical overlap, semantic similarity, experience, and language coverage each produce explicit evidence. Semantic embeddings help with wording mismatches, while deterministic lexical rules keep the report explainable.

### How does the truth guard work?

Each rewrite suggestion receives a safety label. Suggestions that add claims not supported by the original resume can be marked `needs_review` or `unsupported`, and the UI surfaces the guardrail reason.

### What would you improve next?

For a stronger public demo, I would deploy it, add threshold-based eval regression gates, publish provider-specific cost/latency comparisons, expand the labeled dataset, and optionally add OpenAI-compatible `/embeddings` support beside the local sentence-transformer path.

## GitHub README Project Tagline Options

1. **AI resume-to-job matching product with explainable reports and truth-guarded resume rewrites.**
2. **Portfolio-grade AI product demonstrating document ingestion, structured extraction, matching, guardrails, and polished UX.**
3. **Next.js + FastAPI AI product that turns resumes and job descriptions into shareable, evidence-backed match reports.**

## LinkedIn / Portfolio Snippet

I built JobFit AI, a product-style AI engineering project that analyzes a resume against a target job description and generates an explainable match report. The system supports document ingestion, schema-first OpenAI-compatible LLM extraction with JSON-repair self-correction, pgvector-backed embedding storage, hybrid semantic/lexical scoring, requirement-level evidence rows, ATS keyword analysis, truth-guarded resume rewrite suggestions, LLM-as-judge evaluation hooks, and GitHub Actions CI. I used Next.js, FastAPI, PostgreSQL, SQLAlchemy, and TypeScript to build a polished no-account demo flow with shareable report pages and markdown export.
