# JobFit AI — Model / System Card

> **Version:** 0.5.0  
> **Last updated:** 2026-06-18  
> **Scope:** Portfolio-grade AI/ML system card for the current repository implementation.

## Summary

JobFit AI analyzes a resume against a target job description and produces an
explainable fit report, ATS keyword coverage, and truth-guarded resume rewrite
suggestions.

The system is intentionally **provider-agnostic** and **clone-and-run friendly**:
local deterministic clients keep the demo usable without API keys, while
OpenAI-compatible clients can be enabled for schema-first LLM extraction,
optimization, evaluation judging, and truth-guard entailment.

## Tasks

| Task | Output | Primary implementation |
| --- | --- | --- |
| Resume parsing | `ResumeExtraction` JSON | Local parser or OpenAI-compatible LLM |
| Job parsing | `JobExtraction` JSON | Local parser or OpenAI-compatible LLM |
| Embedding indexing | 384-dim vectors | Local MiniLM or deterministic fallback |
| Match scoring | `MatchReport` + evidence rows | Hybrid semantic + lexical scoring |
| Resume optimization | `OptimizedResumeDraft` | Local optimizer or OpenAI-compatible LLM |
| Truth guard | `TruthGuardDecision` | LLM entailment judge with local fallback |
| Evaluation | Markdown metric report | CLI harness over labeled datasets |

## Model and Provider Stack

### LLM layer

- **Default:** local deterministic parsers/optimizer/truth guard.
- **Optional:** `OpenAICompatLLMClient` for `/chat/completions` providers.
- **Schema contract:** Pydantic models with strict validation.
- **Repair:** invalid JSON can be retried through `json_repair.v1.md`.
- **Observability:** provider, model, usage, latency, repair status, and validation
  metadata are recorded in `AIRun` / `AIOutput` rows.

### Embedding layer

- **Default model:** `sentence-transformers/all-MiniLM-L6-v2`.
- **Dimension:** 384, matching `pgvector` columns.
- **Fallback:** deterministic token-hash vectors when `sentence_transformers` is
  unavailable.
- **Storage:** `resume_embeddings` and `job_embeddings`.
- **Metadata:** provider/model/fallback details are stored with embedding rows and
  propagated into match evidence where relevant.

### Matching layer

- **Engine:** `hybrid-semantic-v1`.
- **Lexical signal:** normalized skill/keyword overlap and aliases.
- **Semantic signal:** cosine similarity over resume/job embeddings.
- **Evidence labels:** `exact`, `alias`, `semantic`, `hybrid`, and `missing`.
- **Explainability:** evidence rows include similarity scores, source text, source
  IDs, embedding provider/model, and score thresholds.

## Intended Use

This project is suitable for:

- portfolio demonstrations of applied AI product engineering;
- local experimentation with resume/job matching;
- comparing extraction, matching, and truth-guard behavior across providers;
- evaluating prompt/schema changes on labeled examples.

## Out-of-Scope / Non-Goals

This implementation is not intended to be:

- a production hiring decision system;
- an automated candidate rejection tool;
- a legal/compliance-grade ATS;
- a replacement for human review;
- a guarantee that suggested resume edits are appropriate for every employer.

## Evaluation Snapshot

Latest local command:

```powershell
.\.venv\Scripts\python -m app.evals.runner --task all --dataset v2 --no-persist
```

Environment note: this run used deterministic fallback embeddings because
`sentence_transformers` was not installed.

| Area | Metric | Value |
| --- | --- | --- |
| Resume parser | JSON validity | 100.0% |
| Resume parser | Schema pass rate | 100.0% |
| Resume parser | Skill F1 | 100.0% |
| Job parser | JSON validity | 100.0% |
| Job parser | Schema pass rate | 100.0% |
| Job parser | Skill F1 | 45.5% |
| Matching | Matched skill F1 | 36.2% |
| Matching | Semantic match F1 | 50.0% |
| Matching | Score band accuracy | 54.5% |
| Truth guard | Risky recall | 100.0% |
| Truth guard | Unsupported recall | 66.7% |
| Truth guard | Safe precision | 100.0% |
| Truth guard | Status accuracy | 41.7% |

> [!IMPORTANT]
> These are baseline portfolio/eval metrics, not production-quality performance
> claims. The matching and truth-guard metrics intentionally expose calibration
> gaps that are useful for future model and prompt improvements.

## Safety and Reliability Controls

- Strict Pydantic schemas for AI outputs.
- JSON repair loop for LLM structured output failures.
- Local fallback clients for clone-and-run behavior.
- Truth guard classification for resume rewrite suggestions.
- Persisted evidence rows for match explanations.
- SSRF-aware URL ingestion for public job descriptions.
- CI quality gates: Ruff, mypy, pytest, eval smoke, frontend typecheck/build.

## Known Limitations

- Local parser and optimizer are heuristic and intentionally conservative.
- Deterministic fallback embeddings are useful for tests/demos but are not a
  substitute for real semantic embeddings.
- The current truth guard catches risky cases but can over-flag grounded rewrites.
- Eval datasets are curated and modest in size; they do not represent all job
  markets, industries, or languages.
- No user authentication, authorization, or production data retention controls are
  implemented.

## Recommended Operating Modes

| Mode | Configuration | Use case |
| --- | --- | --- |
| Offline demo | `AI_PROVIDER=local`, `EMBEDDING_PROVIDER=local` | Clone-and-run, tests, CI |
| Local ML demo | install `backend[local-ml]` | Real MiniLM embeddings without API keys |
| Provider demo | `AI_PROVIDER=openai` + compatible endpoint | LLM-backed parsing/optimization/truth guard |
| Evaluation | `python -m app.evals.runner --task all --dataset v2 --no-persist` | Reproducible metric snapshot |

## Future Improvements

- Add OpenAI-compatible `/embeddings` support.
- Expand labeled datasets beyond `v2`.
- Improve score calibration and semantic recall.
- Add regression thresholds for eval metrics in CI.
- Add provider-specific cost/latency dashboards.
