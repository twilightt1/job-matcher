# Evaluation Plan

> Mô tả harness đánh giá AI, datasets, metric formulas, runner CLI, và định dạng
> report cho JobFit AI. File này dành cho reviewer muốn hiểu **làm sao mình biết
> pipeline đang chạy đúng**.

## 1. Purpose / Mục tiêu

The evaluation harness exists to answer three questions, in order of priority:

1. **Extraction quality:** Are `ResumeExtraction` and `JobExtraction` JSON
   outputs correct and stable?
2. **Scoring quality:** Does the hybrid semantic/lexical match engine produce
   scores and evidence that agree with human-labelled ground truth?
3. **Semantic retrieval quality:** Does embedding evidence recover labeled
   semantic matches that lexical matching alone may miss?
4. **Truth-guard quality:** Does the guard correctly flag unsupported
   resume rewrite suggestions?

Harness code lives in [`backend/app/evals/`](../backend/app/evals/):

```text
backend/app/evals/
├── __init__.py
├── datasets.py          # PairEvaluationExample + TruthGuardEvaluationCase
├── metrics.py           # Precision/Recall/F1, score band classification
├── report.py            # Markdown report renderer
├── runner.py            # CLI entrypoint + EvaluationRunReport orchestration
├── semantic.py          # Semantic eval match builder
├── types.py             # TaskEvaluationReport / EvaluationRunReport dataclasses
└── datasets/            # JSON ground-truth files
    ├── ground_truth/*.json
    ├── resumes/*.txt
    ├── jobs/*.txt
    └── truth_guard_cases.json
```

## 2. Supported Tasks / Task được hỗ trợ

Runner CLI accepts one of `resume_parser`, `job_parser`, `matching`,
`truth_guard`, or `all` (default for CI smoke).

| Task | Input | Output | Source of truth |
| --- | --- | --- | --- |
| `resume_parser` | Resume text | `ResumeExtraction` JSON | `ground_truth/<resumeId>.json` |
| `job_parser` | Job description text | `JobExtraction` JSON | `ground_truth/<jobId>.json` |
| `matching` | Resume + job pair | Overall score + breakdown | Expected score band + matched/missing skills |
| `truth_guard` | Resume text + suggestion draft | `TruthGuardDecision` | `truth_guard_cases.json` |

The runner is the preferred way to score. Use `--no-persist` for CI and local
smoke runs that do not have a database available; omit it when you want to write
`eval_runs` / `eval_results` records.

## 3. Datasets / Bộ dữ liệu

### 3.1 Pair dataset (resume_parser / job_parser / matching)

Each example is a directory entry:

```text
evals/datasets/
├── ground_truth/
│   ├── alex_pm__stripe_pm.json     # expects {resumeId, jobId, resume_expectation, job_expectation, matching_expectation}
│   └── ...
├── resumes/
│   ├── alex_pm.txt
│   └── ...
└── jobs/
    ├── stripe_pm.txt
    └── ...
```

`PairEvaluationExample` carries:

- `resume_id`, `job_id` (string IDs, joined into `example_id`)
- `resume_text`, `job_text` (loaded from `.txt` files)
- `resume_expectation`: `expected_candidate_name`, `expected_skills`, `expected_languages`, `min_years_experience`
- `job_expectation`: `expected_title`, `expected_company`, `expected_required_skills`, `expected_preferred_skills`, `expected_seniority`
- `matching_expectation`: `expected_score_band` (`strong_match` / `partial_match` / `weak_match`), `expected_score_min`, `expected_score_max`, `expected_matched_skills`, `expected_missing_skills`, and labeled semantic matches where available

### 3.2 Truth-guard dataset

Single file `truth_guard_cases.json` with one object per case:

```json
{
  "case_id": "tg_001",
  "resume_text": "...",
  "suggestion": { "section_type": "experience", "suggested_text": "..." },
  "expected_truth_status": "safe",
  "expected_new_claims": []
}
```

## 4. Metrics / Các metric

### 4.1 Parsing metrics (`ParsingMetrics`)

| Metric | Formula | Mục đích |
| --- | --- | --- |
| `json_validity_rate` | valid JSON outputs / total examples | Bắt lỗi parse JSON |
| `schema_pass_rate` | Pydantic-valid outputs / total | Bắt schema drift |
| `skill_precision` | TP / (TP + FP) trên normalized skills | Tránh bịa skill |
| `skill_recall` | TP / (TP + FN) | Không miss skill có sẵn |
| `skill_f1` | 2 · P · R / (P + R) | Tổng hợp P/R |
| `exact_name_match_rate` | fraction of exact candidate-name matches | Bắt parser bịa tên |
| `average_confidence` | mean of parser-reported confidence | Tự đánh giá parser |

Where skills are normalized via `normalize_skill_list` (lowercase, strip
punctuation, apply alias dictionary) before TP/FP/FN counting.

### 4.2 Matching metrics (`MatchingMetrics`)

| Metric | Formula | Mục đích |
| --- | --- | --- |
| `matched_skill_precision` | TP / (TP + FP) trên matched skills | Không match nhầm |
| `matched_skill_recall` | TP / (TP + FN) | Bắt match thiếu |
| `matched_skill_f1` | 2PR / (P+R) | Tổng hợp |
| `missing_skill_precision` | TP / (TP + FP) trên "skill declared missing" | Không thiếu sót |
| `missing_skill_recall` | TP / (TP + FN) | Không kê thiếu nhầm |
| `missing_skill_f1` | 2PR / (P+R) | Tổng hợp |
| `score_band_accuracy` | fraction đúng band (`strong` ≥80, `partial` ≥60, `weak` <60) | So khớp verdict |
| `score_in_range_rate` | fraction nằm trong labeled score range | Kiểm tra calibration range |
| `average_score_delta` | mean distance from expected range/band anchor | Sai số trung bình |
| `semantic_match_precision` | TP / (TP + FP) trên semantic/hybrid evidence | Không match semantic nhầm |
| `semantic_match_recall` | TP / (TP + FN) trên labeled semantic matches | Bắt semantic match thiếu |
| `semantic_match_f1` | 2PR / (P+R) | Tổng hợp semantic quality |

Score bands are defined in `app/evals/metrics.py:192`:

```python
def classify_score_band(score: int) -> ScoreBand:
    if score >= 80: return "strong_match"
    if score >= 60: return "partial_match"
    return "weak_match"
```

### 4.3 Truth-guard metrics (`TruthGuardMetrics`)

| Metric | Formula | Mục đích |
| --- | --- | --- |
| `risky_recall` | risky_tp / (risky_tp + risky_fn) | Bắt suggestion có vấn đề |
| `unsupported_recall` | unsupported_tp / (unsupported_tp + unsupported_fn) | Bắt hallucination phải reject |
| `safe_precision` | safe_tp / (safe_tp + safe_fp) | Không block nhầm suggestion safe |
| `status_accuracy` | exact status matches / total cases | Đúng nhãn safe/needs_review/unsupported |
| `hallucination_rate` | count(unexpected_new_claims) / total | Đo guard có bỏ sót claim mới |
| `new_claim_detection_rate` | exact new-claim set matches / total cases | Độ chính xác claim-level |
| `reviewed_case_rate` | count(predicted_risky) / total | Có quá conservative không |

## 5. Runner CLI / Cách chạy

Từ `backend/`:

```bash
# 1. Cài dev extras
pip install -e ".[dev]"

# 2. Chạy eval smoke không cần DB persistence
python -m app.evals.runner --task all --dataset v2 --no-persist

# 3. Nếu muốn persist kết quả, đảm bảo DB đã apply migration rồi bỏ --no-persist
alembic upgrade head
python -m app.evals.runner --task all --dataset v2

# Hoặc chỉ một task
python -m app.evals.runner --task matching --dataset v2 --no-persist
```

Tùy chọn LLM-as-judge cho parser eval:

```bash
python -m app.evals.runner --task all --dataset v2 --with-llm-judge --no-persist
```

Sau khi chạy:

- File `artifacts/eval_reports/eval_report_{dataset}.md` được sinh
- Nếu `persist=True` (mặc định), một `EvalRun` row + nhiều `EvalResult` rows
  được insert vào DB (cột `summary_json` chứa toàn bộ metric snapshot)
- CI dùng `--no-persist` để không cần PostgreSQL trong smoke run

## 6. Report format / Định dạng report

Markdown report structure (`render_markdown_report` in `report.py`):

```text
# Evaluation Report ({dataset})

- Requested task: `{task}`
- Generated at: `{iso timestamp}`
- Persisted run id: `{uuid or "not_persisted"}`
- [Optional] ## Warnings  ← nếu có warning (vd: persistence failed)

## {Task display name}
Average latency: `{ms} ms`

| Metric | Value | Description |
| --- | --- | --- |
| `{metric_name}` | `{display_value}` | {description} |

### Example outcomes
- **{example_id}** — `{status}` — {summary}
```

## 7. CI integration / Tích hợp CI

Implemented in `.github/workflows/ci.yml`.

Backend quality gates:

- `python -m ruff check app`
- `python -m mypy app`
- `python -m pytest -q`
- `python -m app.evals.runner --task all --dataset v2 --no-persist`
- upload `artifacts/eval_reports/eval_report_v2.md` as a workflow artifact

Frontend quality gates:

- `npm ci`
- `npm run verify`

Current CI intentionally uses deterministic fallback embeddings when local ML
runtime is unavailable. This keeps PR checks fast and reproducible. Real MiniLM
embedding performance should be measured by installing `backend[local-ml]` and
rerunning the same eval command locally or in a heavier benchmark workflow.

## 8. Latest v2 Snapshot

Command:

```powershell
.\.venv\Scripts\python -m app.evals.runner --task all --dataset v2 --no-persist
```

| Area | Metric | Value |
| --- | --- | --- |
| Resume parser | Skill F1 | 100.0% |
| Job parser | Skill F1 | 45.5% |
| Matching | Matched skill F1 | 36.2% |
| Matching | Semantic match F1 | 50.0% |
| Matching | Score band accuracy | 54.5% |
| Truth guard | Risky recall | 100.0% |
| Truth guard | Unsupported recall | 66.7% |
| Truth guard | Status accuracy | 41.7% |

## 9. Cross-References

- Per-prompt contracts & versions → [Prompt Design](prompt_design.md)
- Hệ thống ghi log AI runs → [Technical Architecture](technical_architecture.md#13-observability)
- PRD scope & build status → [Product Requirements](prd.md)
