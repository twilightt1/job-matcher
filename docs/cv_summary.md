# JobFit AI — CV / Portfolio Summary

## One-line Summary

Built JobFit AI, an AI-powered resume-to-job matching product that ingests resumes and job descriptions, extracts structured signals, generates explainable match reports, and produces truth-guarded optimization suggestions using Next.js, FastAPI, PostgreSQL, and schema-first AI pipelines.

## CV Bullet Version

- Built **JobFit AI**, a product-style AI resume matching app using **Next.js, FastAPI, PostgreSQL, SQLAlchemy, and TypeScript**.
- Implemented an end-to-end CV/JD analysis pipeline covering document ingestion, structured extraction, deterministic scoring, evidence rows, optimization suggestions, and truth-guard validation.
- Designed explainable match reports with score breakdowns, ATS keyword coverage, requirement-level evidence, and shareable `/reports/{id}` pages.
- Added AI safety guardrails that classify resume rewrite suggestions as `safe`, `needs_review`, or `unsupported` to reduce hallucinated claims.
- Created a polished no-account product demo with built-in sample data, markdown export, and portfolio-ready documentation.

## Short Portfolio Description

JobFit AI is an AI engineering product demo that helps job seekers understand how well a resume matches a specific job description. Users can paste text or upload documents, run a one-click analysis, and receive a shareable report showing match score, strengths, gaps, ATS keywords, evidence rows, and guarded resume rewrite suggestions.

The project demonstrates practical AI product engineering rather than a simple chat wrapper: document ingestion, schema-first parsing, deterministic scoring, persisted evidence, truth guardrails, observability-friendly data models, and a polished Next.js interface.

## Technical Highlights

- **Frontend:** Next.js 14 App Router, React, TypeScript, vanilla CSS design system.
- **Backend:** FastAPI, Pydantic, SQLAlchemy async, Alembic.
- **Database:** PostgreSQL with JSONB report storage and pgvector-ready schema.
- **AI pipeline:** local deterministic parsers/optimizer, prompt-version-ready architecture, provider abstraction planned.
- **Safety:** truth-guard classification for unsupported resume claims.
- **Explainability:** persisted match evidence rows connected to job requirements.
- **Demo UX:** no-account analyze page, shareable report route, copy link, markdown export.

## Recruiter-friendly Pitch

I built JobFit AI to show that I can turn an AI concept into a real product workflow. It is not just a chatbot: the system ingests messy resume/JD inputs, structures them, scores the match with explainable evidence, generates resume improvements, and uses guardrails to avoid unsupported claims. I also built the frontend product experience, shareable reports, and documentation needed to present it as a portfolio-ready product.

## Interview Deep-dive Topics

### Why this architecture?

I separated ingestion, parsing, matching, optimization, and truth-guarding so each stage is testable and explainable. This is easier to debug than a single giant prompt.

### Why deterministic scoring?

For a match score, deterministic logic is more reliable and easier to explain than asking an LLM to invent a percentage. The LLM-style layer is better suited for extraction and rewrite suggestions, while scoring should remain auditable.

### How does the truth guard work?

Each rewrite suggestion receives a safety label. Suggestions that add claims not supported by the original resume can be marked `needs_review` or `unsupported`, and the UI surfaces the guardrail reason.

### What would you improve next?

For a stronger public demo, I would deploy it, add real LLM provider wiring behind the existing abstraction, and optionally wire pgvector-based semantic evidence retrieval using the schema already present in the project.

## GitHub README Project Tagline Options

1. **AI resume-to-job matching product with explainable reports and truth-guarded resume rewrites.**
2. **Portfolio-grade AI product demonstrating document ingestion, structured extraction, matching, guardrails, and polished UX.**
3. **Next.js + FastAPI AI product that turns resumes and job descriptions into shareable, evidence-backed match reports.**

## LinkedIn / Portfolio Snippet

I built JobFit AI, a product-style AI engineering project that analyzes a resume against a target job description and generates an explainable match report. The system supports document ingestion, structured parsing, deterministic scoring, requirement-level evidence rows, ATS keyword analysis, and truth-guarded resume rewrite suggestions. I used Next.js, FastAPI, PostgreSQL, SQLAlchemy, and TypeScript to build a polished no-account demo flow with shareable report pages and markdown export.
