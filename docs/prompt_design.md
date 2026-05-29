# Prompt Design

> Nguyên tắc thiết kế prompt, version policy, và contract cho từng prompt file
> trong JobFit AI. Mỗi prompt là một file Markdown độc lập, loadable qua
> `app/ai/prompt_loader.load_prompt_template()`.

## 1. Storage / Nơi lưu

```text
backend/app/ai/prompts/
├── resume_parser.v1.md
├── job_parser.v1.md
├── match_explainer.v1.md
├── resume_optimizer.v1.md
├── truth_guard.v1.md
└── json_repair.v1.md
```

Loader (single source of truth, 11 lines):

```python
# backend/app/ai/prompt_loader.py
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
def load_prompt_template(prompt_name: str) -> str:
    return (PROMPTS_DIR / prompt_name).read_text(encoding="utf-8")
```

## 2. Design Principles / Nguyên tắc thiết kế

| # | Principle | Implementation hint |
| --- | --- | --- |
| 1 | **JSON-only output** | Mọi prompt extraction kết thúc bằng `"Return valid JSON only."` |
| 2 | **Schema-first** | Output validate bằng Pydantic schema trong `app/ai/schemas/` |
| 3 | **Grounded in input** | "Use only the provided resume text. Do not invent missing facts." |
| 4 | **Versioned in filename** | `<task>.v{n}.md`, bump số khi thay đổi contract |
| 5 | **Tracked in DB** | `AIRun.prompt_name` + `prompt_version` lưu mỗi lần gọi |
| 6 | **Separation of concerns** | Một prompt = một task; không chain nhiều task trong 1 prompt |
| 7 | **Repair fallback** | Prompt invalid → `json_repair.v1.md` tự sửa theo schema |

## 3. Temperature Policy

| Task type | Temperature | Lý do |
| --- | --- | --- |
| `resume_parser`, `job_parser` | `0.0` | Reproducible extraction |
| `truth_guard`, `match_explainer` | `0.0` | Deterministic classification |
| `resume_optimizer` | `0.2` | Cần chút variation để tránh generic phrasing |
| `json_repair` | `0.0` | Schema-conformity là deterministic |

Giá trị set tại `app/ai/pipeline/parsing.py` (parsing) và
`app/ai/pipeline/optimization.py` (optimization + truth guard).

## 4. Prompt Catalog / Danh sách prompt

### 4.1 `resume_parser.v1.md`

- **Mục đích:** Extract structured `ResumeExtraction` JSON từ raw text
- **Placeholder:** `<<<RESUME_TEXT>>>`
- **Output keys (Pydantic):** `candidate_name`, `summary`, `skills[]`,
  `experience_highlights[]`, `languages[]`, `total_years_experience`
- **Caller:** `LocalResumeParserClient.parse_resume()`
- **Default temperature:** `0.0`

### 4.2 `job_parser.v1.md`

- **Mục đích:** Extract structured `JobExtraction` JSON từ JD text
- **Placeholder:** `<<<JOB_DESCRIPTION>>>`
- **Output keys:** `title`, `company`, `summary`, `required_skills[]`,
  `preferred_skills[]`, `responsibilities[]`, `requirements[]`,
  `seniority`, `location`, `work_mode`, `employment_type`
- **Lưu ý prompt:** "Separate required skills from nice-to-have skills and
  cite evidence text"
- **Caller:** `LocalJobParserClient.parse_job()`
- **Default temperature:** `0.0`

### 4.3 `match_explainer.v1.md`

- **Mục đích:** Sinh narrative explanation từ deterministic match result
- **Placeholder:** `<<<MATCH_ANALYSIS_JSON>>>`
- **Output keys:** `summary`, `top_strengths[]`, `top_gaps[]`
- **Quy tắc cứng:** "Do not invent or change score values" — chỉ diễn giải
  số đã có trong JSON input
- **Caller:** Sau `DeterministicMatchEngine.compute()` (planned — hiện
  tại engine tự sinh explanation rule-based)

### 4.4 `resume_optimizer.v1.md`

- **Mục đích:** Sinh danh sách `RewriteSuggestionDraft` cho từng gap
- **Placeholders:** `<<<RESUME_JSON>>>`, `<<<JOB_JSON>>>`,
  `<<<MATCH_ANALYSIS_JSON>>>`
- **Output keys (per suggestion):** `section_type`, `target_location`,
  `original_text`, `suggested_text`, `targeted_requirements[]`,
  `keywords_added[]`, `reason`, `estimated_score_lift`
- **Quy tắc cứng:** "Do not invent metrics, skills, tools, leadership,
  scale, or business impact"
- **Caller:** `LocalResumeOptimizer.optimize()`
- **Default temperature:** `0.2`

### 4.5 `truth_guard.v1.md`

- **Mục đích:** Phân loại mỗi suggestion là `safe` / `needs_review` /
  `unsupported` bằng cách đối chiếu với resume evidence
- **Placeholders:** `<<<RESUME_JSON>>>`, `<<<SUGGESTION_JSON>>>`
- **Output keys:** `truth_status`, `new_claims[]`, `guardrail_reason`
- **Decision rule (mirror trong prompt):**
  - `safe` — suggestion chỉ rephrase evidence đã có
  - `needs_review` — suggestion có thể đúng nhưng cần user xác nhận
  - `unsupported` — suggestion bịa metric, tool, ownership, scale, awards
- **Caller:** `LocalTruthGuard.evaluate()` (chạy 1 lần / suggestion)
- **Default temperature:** `0.0`

### 4.6 `json_repair.v1.md`

- **Mục đích:** Sửa JSON invalid / partial về đúng schema
- **Placeholders:** `<<<SCHEMA>>>`, `<<<INVALID_JSON_OR_TEXT>>>`,
  `<<<VALIDATION_ERRORS>>>`
- **Quy tắc cứng:** "Do not add new factual content" — chỉ fix syntax + type
- **Caller:** Pipeline validation step khi `AIRun.validation_status = invalid`
- **Default temperature:** `0.0`

## 5. Validation & Repair Flow / Luồng validate-sửa

```text
Prompt output (text or JSON)
  ↓
Pydantic schema validation
  ↓
[valid] → AIRun.validation_status = "valid" → persist
[invalid] → AIRun.validation_status = "invalid"
  ↓
json_repair.v1.md retry
  ↓
[re-valid] → AIRun.validation_status = "repaired" → persist
[still invalid] → AIRun.status = "failed", error_message populated
```

Status enum lives in `app/db/models/enums.py`:

```python
class ValidationStatus(StrEnum):
    NOT_VALIDATED = "not_validated"
    VALID = "valid"
    INVALID = "invalid"
    REPAIRED = "repaired"

class AIRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    REPAIRED = "repaired"
    CANCELLED = "cancelled"
```

## 6. Versioning / Cách bump version

- File: tăng `.v1` → `.v2` (giữ `.v1` cũ để reproducible replay)
- Code reference: bump constant trong pipeline module, vd
  `RESUME_PROMPT_NAME = "resume_parser.v2.md"`,
  `PROMPT_VERSION = "v2"`
- DB column: `AIRun.prompt_version` lưu version đang dùng → query để phân
  tích theo version

## 7. Out of Scope (chưa có prompt)

| Prompt | Status | Note |
| --- | --- | --- |
| `common_system.v1.md` | ❌ Not built | Engine dùng per-task prompt trực tiếp, không có shared prefix |
| `cover_letter.v1.md` | ❌ Reserved | Đề cập trong roadmap, chưa build |
| `interview_prep.v1.md` | ❌ Reserved | Đề cập trong roadmap, chưa build |

## 8. Cross-References

- Metric đánh giá prompt output → [Evaluation Plan](evaluation_plan.md)
- Caller pipeline (parsing, matching, optimization) → [Technical Architecture](technical_architecture.md#5-ai-pipeline)
- PRD scope về tính năng prompt-driven → [Product Requirements](prd.md#3-mvp-scope-built--phạm-vi-mvp-đã-build)
