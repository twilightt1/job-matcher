# Evaluation Plan

> Mô tả harness đánh giá AI, datasets, metric formulas, runner CLI, và định dạng
> report cho JobFit AI. File này dành cho reviewer muốn hiểu **làm sao mình biết
> pipeline đang chạy đúng**.

## 1. Purpose / Mục tiêu

The evaluation harness exists to answer three questions, in order of priority:

1. **Extraction quality:** Are `ResumeExtraction` and `JobExtraction` JSON
   outputs correct and stable?
2. **Scoring quality:** Does the deterministic match engine produce scores that
   agree with human-labelled ground truth?
3. **Truth-guard quality:** Does the guard correctly flag unsupported
   resume rewrite suggestions?

Harness code lives in [`backend/app/evals/`](../backend/app/evals/):

```text
backend/app/evals/
├── __init__.py
├── datasets.py          # PairEvaluationExample + TruthGuardEvaluationCase
├── metrics.py           # Precision/Recall/F1, score band classification
├── report.py            # Markdown report renderer
├── runner.py            # CLI entrypoint + EvaluationRunReport orchestration
├── types.py             # TaskEvaluationReport / EvaluationRunReport dataclasses
└── datasets/            # JSON ground-truth files (gitignored secrets)
    ├── ground_truth/*.json
    ├── resumes/*.txt
    └── truth_guard_cases.json
```

## 2. Supported Tasks / Task được hỗ trợ

Runner CLI accepts one of `resume_parser`, `job_parser`, `matching`,
`truth_guard`, or `all` (default for CI).

| Task | Input | Output | Source of truth |
| --- | --- | --- | --- |
| `resume_parser` | Resume text | `ResumeExtraction` JSON | `ground_truth/<resumeId>.json` |
| `job_parser` | Job description text | `JobExtraction` JSON | `ground_truth/<jobId>.json` |
| `matching` | Resume + job pair | Overall score + breakdown | Expected score band + matched/missing skills |
| `truth_guard` | Resume text + suggestion draft | `TruthGuardDecision` | `truth_guard_cases.json` |

The runner is the only allowed way to score; do not call parsers directly
without writing the run to the `eval_runs` table.

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
- `matching_expectation`: `expected_score_band` (`strong_match` / `partial_match` / `weak_match`), `expected_matched_skills`, `expected_missing_skills`

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
| `average_score_delta` | mean of `|predicted − expected_band_midpoint|` | Sai số trung bình |

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
| `safe_precision` | safe_tp / (safe_tp + safe_fp) | Không block nhầm suggestion safe |
| `hallucination_rate` | count(unexpected_new_claims) / total | Đo guard có bỏ sót claim mới |
| `reviewed_case_rate` | count(predicted_risky) / total | Có quá conservative không |

## 5. Runner CLI / Cách chạy

Từ `backend/`:

```bash
# 1. Cài dev extras
pip install -e ".[dev]"

# 2. Đảm bảo DATABASE_URL trỏ về DB đã apply migration
alembic upgrade head

# 3. Chạy eval (default task = all, dataset = smoke)
python -m app.evals.runner --task all --dataset smoke

# Hoặc chỉ một task
python -m app.evals.runner --task matching --dataset smoke
```

Sau khi chạy:

- File `app/evals/reports/eval_report_{dataset}.md` được sinh
- Nếu `persist=True` (mặc định), một `EvalRun` row + nhiều `EvalResult` rows
  được insert vào DB (cột `summary_json` chứa toàn bộ metric snapshot)

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

## 7. CI integration (planned) / Tích hợp CI

Suggested next steps (not yet wired):

- `pytest` test load `eval_report_*.md` và assert `skill_f1 >= 0.8`,
  `risky_recall >= 0.9`, `hallucination_rate <= 0.1`
- Diff report giữa 2 run liên tiếp để detect regression
- Persist report file artifact trong GitHub Actions run

## 8. Cross-References

- Per-prompt contracts & versions → [Prompt Design](prompt_design.md)
- Hệ thống ghi log AI runs → [Technical Architecture](technical_architecture.md#9-observability--ai-runs)
- PRD scope & build status → [Product Requirements](prd.md)
