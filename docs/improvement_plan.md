# JobFit AI — Improvement Plan (AI/ML Engineer Portfolio)

> Mục tiêu: nâng JobFit AI từ một project software/backend sạch sẽ nhưng "AI giả"
> (toàn bộ regex/keyword) thành một **AI/ML engineering project thực thụ** đủ mạnh
> để đưa vào CV AI/ML Engineer.

## Bối cảnh / Đánh giá hiện trạng

Kiến trúc rất tốt và **đã sẵn sàng** để gắn AI thật:
- Prompt templates có versioning (`resume_parser.v1.md`, `json_repair.v1.md`, ...).
- Observability có sẵn: bảng `AIRun` / `AIOutput`, `AIProvider` enum (đã có `OPENAI`),
  `AIRunStatus.REPAIRED`, `temperature`, `repair_attempted`, token/latency fields.
- Client `Protocol` abstraction (`base.py`), factory-ready.
- pgvector schema `Vector(384)` + bảng `resume_embeddings` / `job_embeddings`.
- Pydantic schemas dùng `extra="forbid"` → hợp structured output.
- Quality gate thật: ruff + mypy strict + 22 pytest tests.

### Gap chính (lý do chưa đạt chuẩn AI/ML)

| # | Gap | Hiện trạng |
| - | --- | ---------- |
| 1 | Không có LLM client thật | `AI_PROVIDER=gemini` nhưng pipeline hardcode `LocalResumeParserClient` (regex) |
| 2 | Embeddings chết | Schema `Vector(384)` có, không có code generate/query |
| 3 | Matching không semantic | Chỉ Jaccard keyword overlap + alias thủ công |
| 4 | Eval dataset = 1 mẫu | Harness tốt nhưng 1 resume + 1 job → metrics vô nghĩa |
| 5 | Truth guard sơ khai | Set-difference keywords, không entailment |
| 6 | Thiếu ML rigor | Không CI, không model card, không metrics thật trong README |

---

## Quyết định kiến trúc đã chốt

- **LLM = OpenAI-compatible client (1 client cho mọi provider)**: OpenAI, Gemini
  (`/v1beta/openai/`), Ollama, vLLM, OpenRouter, LM Studio, Together — đổi provider
  bằng config, không sửa code.
- **Embeddings = local default** (`sentence-transformers/all-MiniLM-L6-v2`, 384-dim,
  khớp schema sẵn có) + OpenAI-compatible `/embeddings` optional.
- **Local fallback ở mọi layer**: repo clone-and-run không cần API key (quan trọng cho portfolio).
- `.env` driven: `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `LLM_MODEL`, `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`.

---

## Phase 1 — OpenAI-compatible LLM client + provider abstraction

Một client duy nhất nói chuẩn OpenAI Chat Completions.

- [x] `OpenAICompatLLMClient` (httpx async) gọi `/chat/completions` với
      `response_format={"type":"json_object"}` + JSON schema validation.
- [x] Config: thêm `openai_base_url`, `llm_model`, `llm_temperature`,
      `llm_request_timeout_seconds`, `llm_max_repair_attempts` vào `core/config.py`.
- [x] Wrap 3 task dùng prompt templates có sẵn:
  - `LLMResumeParser` (→ `ResumeExtraction`)
  - `LLMJobParser` (→ `JobExtraction`)
  - `LLMResumeOptimizer` (→ `OptimizedResumeDraft`)
- [x] **JSON repair loop**: validate qua Pydantic; fail → retry với `json_repair.v1.md`,
      set `AIRunStatus.REPAIRED` + `repair_attempted=True`.
- [x] **Factory** chọn client theo `AI_PROVIDER` (`local` / `openai`); local là fallback.
- [x] Capture latency + token thật từ `usage` response vào `AIRun` / `AIOutput` metadata.
- [x] Ghi provider/model/repair status thật trong parsing + optimization pipelines.
- [x] Tests: mock httpx, test happy-path + schema-fail-then-repair + fallback.
- [x] Verification: `pytest`, `mypy`, `ruff` đều pass sau Phase 1 refactor.

## Phase 2 — Real embeddings + semantic matching (pgvector)

- [x] `EmbeddingClient` abstraction với **local sentence-transformers mặc định**
      (`sentence-transformers/all-MiniLM-L6-v2`, 384-dim).
- [x] Giữ cửa mở cho OpenAI-compatible `/embeddings` như extension sau này,
      nhưng không bắt buộc cho vòng triển khai đầu tiên.
- [x] Generate embeddings cho resume bullets + job requirements; lưu vào
      `resume_embeddings` / `job_embeddings` qua pgvector.
- [x] **Hybrid match engine**: kết hợp cosine similarity (semantic) + keyword overlap
      (lexical) → giải quyết "built SPAs" ↔ "frontend frameworks".
- [x] Giữ explainability: similarity scores thật trong `MatchEvidence` và tận dụng
      `MatchType.SEMANTIC` / `MatchType.HYBRID` khi phù hợp.
- [x] Tests: embedding shape/dimension, cosine ranking, hybrid weight, idempotent indexing,
      fallback/error behavior khi local embedding runtime chưa sẵn sàng.
- [x] Docs/eval: cập nhật `README`/`improvement_plan` để không còn claim deterministic-only khi bật semantic path.

### Phase 2 implementation order
1. Embedding client abstraction + local implementation.
2. Resume/job embedding indexing workflow (idempotent).
3. Hybrid semantic + lexical scoring trong matching engine.
4. Wire semantic path vào analysis pipeline.
5. Expand tests/eval/docs.

### Phase 2 current decision
- **Default**: local embeddings để project clone-and-run, reproducible, không phụ thuộc API key.
- **Future extension**: OpenAI-compatible `/embeddings` có thể thêm sau khi semantic path local đã ổn định.
- **Scoring strategy**: hybrid, không semantic-only, để giữ transparency của evidence rows hiện tại.

### Checkpoint after Phase 2
- [x] `pytest -q` → `60 passed, 1 warning`.
- [x] `./.venv/Scripts/python -m mypy app` → `Success: no issues found in 105 source files`.
- [x] `./.venv/Scripts/python -m ruff check app` → `All checks passed!`.
- [x] End-to-end flow vẫn hoạt động: parse → embed → match → optimize.
- [x] Match evidence vẫn explainable và tương thích với persisted report shape.

**Status:** Phase 2 completed. Semantic matching is wired through persisted embeddings, hybrid evidence is explainable, and clone-and-run fallback embeddings are available when `sentence-transformers` is not installed.

**Files expected to be central in Phase 2:**
- `backend/app/db/models/embedding.py`
- `backend/alembic/versions/20260613_0002_optimization_embeddings.py`
- `backend/app/ai/scoring/match_engine.py`
- `backend/app/ai/pipeline/matching.py`
- `backend/app/services/ingestion/workflow.py`
- `backend/app/evals/runner.py`
- new embedding client/service modules under `backend/app/ai/`

**Note:** current Phase 1 implementation already makes this phase easier because provider abstraction,
telemetry, and async client wiring are in place.

---

### Current execution note
Phase 2 hardening is complete. The matching eval smoke command completed against dataset `v2` and wrote `artifacts/eval_reports/eval_report_v2.md`; this environment used deterministic fallback embeddings because `sentence_transformers` is not installed.

## Phase 3 — Eval harness nghiêm túc

- [x] Mở rộng dataset lên **20-30 cặp resume/JD** đa dạng (FE/BE/ML/data; junior→senior; EN/VI).
- [x] **LLM-as-judge** (dùng client Phase 1) cho parse quality + match relevance.
- [x] Metrics thêm: semantic match accuracy, hallucination rate, score calibration.
- [x] Commit markdown report vào `artifacts/eval_reports/` làm bằng chứng.

**Status:** Phase 3 completed with dataset `v2` (22 resume/JD pairs), optional `--with-llm-judge`, semantic/calibration metrics, and generated report artifact at `artifacts/eval_reports/eval_report_v2.md`.

## Phase 4 — Truth guard nâng cấp (AI safety)

- [x] Nâng từ set-difference → **LLM-judge entailment** (resume có support claim không),
      giữ local rule làm fallback.
- [x] Mở rộng `truth_guard_cases.json` với labeled cases → đo hallucination recall thật.

**Status:** Phase 4 completed with OpenAI-compatible `LLMTruthGuard`, local fallback, 12 labeled v2 truth-guard cases, and expanded safety metrics (`unsupported_recall`, `status_accuracy`, `new_claim_detection_rate`).

## Phase 5 — ML engineering rigor

- [x] **CI** (GitHub Actions): ruff + mypy strict + pytest + eval smoke run.
- [x] Model card + provider matrix trong `docs/`.
- [x] README: section "AI/ML Architecture" (sơ đồ embedding/retrieval/eval) + bảng metrics thật.
- [x] Cập nhật CV bullets: RAG / embeddings / LLM-eval / JSON-repair thay vì "deterministic scoring".

**Status:** Phase 5 completed with GitHub Actions backend/frontend quality gates, `v2` eval smoke artifact upload, model/system card, provider matrix, README AI/ML architecture diagram + metrics table, refreshed evaluation/architecture docs, and CV bullets focused on OpenAI-compatible LLMs, JSON-repair, pgvector embeddings, semantic retrieval, truth guard, and CI.

---

## Thứ tự triển khai đề xuất

**Phase 1 → 2 → 3 → 5 → 4**

Lý do: Phase 1+2 cho impact CV lớn nhất (LLM thật + semantic/RAG). Phase 3 chứng minh
rigor. Phase 5 đóng gói signals. Phase 4 phức tạp nhất nên để cuối.

## CV positioning sau khi hoàn thành

> Built JobFit AI, an AI-powered resume-to-job matching system using an OpenAI-compatible
> LLM pipeline (schema-first extraction with JSON-repair self-correction), semantic
> matching via sentence-transformer embeddings + pgvector retrieval, an LLM-as-judge
> evaluation harness, and truth-guard hallucination checks — built on FastAPI, Next.js,
> and PostgreSQL with CI and provider-agnostic model abstraction.
