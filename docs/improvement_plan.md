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

- [ ] `OpenAICompatLLMClient` (httpx async) gọi `/chat/completions` với
      `response_format={"type":"json_object"}` + JSON schema inject từ Pydantic.
- [ ] Config: thêm `openai_base_url`, `llm_model`, `llm_temperature` vào `core/config.py`.
- [ ] Wrap 3 task dùng prompt templates có sẵn:
  - `LLMResumeParser` (→ `ResumeExtraction`)
  - `LLMJobParser` (→ `JobExtraction`)
  - `LLMResumeOptimizer` (→ `OptimizedResumeDraft`)
- [ ] **JSON repair loop**: validate qua Pydantic; fail → retry với `json_repair.v1.md`,
      set `AIRunStatus.REPAIRED` + `repair_attempted=True`.
- [ ] **Factory** chọn client theo `AI_PROVIDER` (`local` / `openai`); local là fallback.
- [ ] Capture latency + token thật từ `usage` response vào `AIRun` (thay `latency_ms=1`).
- [ ] Ghi `AIProvider.OPENAI.value` thật trong pipeline thay vì hardcode `LOCAL`.
- [ ] Tests: mock httpx, test happy-path + schema-fail-then-repair + fallback.

## Phase 2 — Real embeddings + semantic matching (pgvector)

- [ ] `EmbeddingClient` interface + 2 backend:
  - Local: `sentence-transformers/all-MiniLM-L6-v2` (default).
  - OpenAI-compatible `/embeddings` (dùng lại base_url infra Phase 1).
- [ ] Generate embeddings cho resume bullets + job requirements; lưu vào
      `resume_embeddings` / `job_embeddings` qua pgvector.
- [ ] **Hybrid match engine**: kết hợp cosine similarity (semantic) + keyword overlap
      (lexical) → giải quyết "built SPAs" ↔ "frontend frameworks".
- [ ] Giữ explainability: similarity scores thật trong `MatchEvidence`.
- [ ] Tests: cosine ranking, hybrid weight, fallback khi không có pgvector.

## Phase 3 — Eval harness nghiêm túc

- [ ] Mở rộng dataset lên **20-30 cặp resume/JD** đa dạng (FE/BE/ML/data; junior→senior; EN/VI).
- [ ] **LLM-as-judge** (dùng client Phase 1) cho parse quality + match relevance.
- [ ] Metrics thêm: semantic match accuracy, hallucination rate, score calibration.
- [ ] Commit markdown report vào `artifacts/eval_reports/` làm bằng chứng.

## Phase 4 — Truth guard nâng cấp (AI safety)

- [ ] Nâng từ set-difference → **LLM-judge entailment** (resume có support claim không),
      giữ local rule làm fallback.
- [ ] Mở rộng `truth_guard_cases.json` với labeled cases → đo hallucination recall thật.

## Phase 5 — ML engineering rigor

- [ ] **CI** (GitHub Actions): ruff + mypy strict + pytest + eval smoke run.
- [ ] Model card + provider matrix trong `docs/`.
- [ ] README: section "AI/ML Architecture" (sơ đồ embedding/retrieval/eval) + bảng metrics thật.
- [ ] Cập nhật CV bullets: RAG / embeddings / LLM-eval / JSON-repair thay vì "deterministic scoring".

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
