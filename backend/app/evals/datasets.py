from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from app.ai.schemas.optimization import RewriteSuggestionDraft
from app.ai.schemas.truth_guard import TruthStatus

ScoreBand = str


@dataclass(slots=True)
class ResumeParserExpectation:
    expected_candidate_name: str | None
    expected_skills: list[str]
    expected_languages: list[str]
    min_years_experience: float | None


@dataclass(slots=True)
class JobParserExpectation:
    expected_title: str | None
    expected_company: str | None
    expected_required_skills: list[str]
    expected_preferred_skills: list[str]
    expected_seniority: str | None


@dataclass(slots=True)
class MatchingExpectation:
    expected_score_band: ScoreBand
    expected_matched_skills: list[str]
    expected_missing_skills: list[str]


@dataclass(slots=True)
class PairEvaluationExample:
    example_id: str
    resume_id: str
    job_id: str
    resume_text: str
    job_text: str
    resume_expectation: ResumeParserExpectation
    job_expectation: JobParserExpectation
    matching_expectation: MatchingExpectation


@dataclass(slots=True)
class TruthGuardEvaluationCase:
    case_id: str
    resume_text: str
    suggestion: RewriteSuggestionDraft
    expected_truth_status: TruthStatus
    expected_new_claims: list[str]


DATASET_ROOT = Path(__file__).resolve().parent / "datasets"
TRUTH_GUARD_FILENAME = "truth_guard_cases.json"


def load_pair_examples(dataset: str) -> list[PairEvaluationExample]:
    dataset_root = _dataset_root(dataset)
    ground_truth_dir = dataset_root / "ground_truth"
    examples: list[PairEvaluationExample] = []

    for path in sorted(ground_truth_dir.glob("*.json")):
        if path.name == TRUTH_GUARD_FILENAME:
            continue
        payload = _read_json(path)
        resume_id = _read_str(payload, "resumeId")
        job_id = _read_str(payload, "jobId")
        example_id = f"{resume_id}__{job_id}"
        examples.append(
            PairEvaluationExample(
                example_id=example_id,
                resume_id=resume_id,
                job_id=job_id,
                resume_text=_read_text(dataset_root / "resumes" / f"{resume_id}.txt"),
                job_text=_read_text(dataset_root / "jobs" / f"{job_id}.txt"),
                resume_expectation=_load_resume_expectation(payload),
                job_expectation=_load_job_expectation(payload),
                matching_expectation=_load_matching_expectation(payload),
            )
        )

    return examples


def load_truth_guard_cases(dataset: str) -> list[TruthGuardEvaluationCase]:
    dataset_root = _dataset_root(dataset)
    payload = _read_json(dataset_root / "ground_truth" / TRUTH_GUARD_FILENAME)
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("truth_guard_cases.json must contain a 'cases' array")

    cases: list[TruthGuardEvaluationCase] = []
    for raw_case in raw_cases:
        if not isinstance(raw_case, dict):
            raise ValueError("Each truth guard case must be a JSON object")
        suggestion_payload = raw_case.get("suggestion")
        if not isinstance(suggestion_payload, dict):
            raise ValueError("Each truth guard case must include a suggestion object")
        cases.append(
            TruthGuardEvaluationCase(
                case_id=_read_str(raw_case, "caseId"),
                resume_text=_read_str(raw_case, "resumeText"),
                suggestion=RewriteSuggestionDraft.model_validate(suggestion_payload),
                expected_truth_status=_read_truth_status(raw_case),
                expected_new_claims=_read_str_list(raw_case, "expectedNewClaims"),
            )
        )
    return cases


def _load_resume_expectation(payload: dict[str, Any]) -> ResumeParserExpectation:
    raw = _read_dict(payload, "resumeParser")
    return ResumeParserExpectation(
        expected_candidate_name=_read_optional_str(raw, "expectedCandidateName"),
        expected_skills=_read_str_list(raw, "expectedSkills"),
        expected_languages=_read_str_list(raw, "expectedLanguages"),
        min_years_experience=_read_optional_float(raw, "minYearsExperience"),
    )


def _load_job_expectation(payload: dict[str, Any]) -> JobParserExpectation:
    raw = _read_dict(payload, "jobParser")
    return JobParserExpectation(
        expected_title=_read_optional_str(raw, "expectedTitle"),
        expected_company=_read_optional_str(raw, "expectedCompany"),
        expected_required_skills=_read_str_list(raw, "expectedRequiredSkills"),
        expected_preferred_skills=_read_str_list(raw, "expectedPreferredSkills"),
        expected_seniority=_read_optional_str(raw, "expectedSeniority"),
    )


def _load_matching_expectation(payload: dict[str, Any]) -> MatchingExpectation:
    raw = _read_dict(payload, "matching")
    return MatchingExpectation(
        expected_score_band=_read_str(raw, "expectedScoreBand"),
        expected_matched_skills=_read_str_list(raw, "expectedMatchedSkills"),
        expected_missing_skills=_read_str_list(raw, "expectedMissingSkills"),
    )


def _dataset_root(dataset: str) -> Path:
    dataset_root = DATASET_ROOT / dataset
    if not dataset_root.exists():
        raise FileNotFoundError(f"Dataset {dataset!r} was not found")
    return dataset_root


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON file {path} must contain an object")
    return payload


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _read_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Field {key!r} must be a JSON object")
    return value


def _read_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Field {key!r} must be a string")
    return value


def _read_optional_str(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Field {key!r} must be a string or null")
    return value


def _read_optional_float(payload: dict[str, Any], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, (float, int)):
        raise ValueError(f"Field {key!r} must be a number or null")
    return float(value)


def _read_str_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Field {key!r} must be an array of strings")
    return list(value)


def _read_truth_status(payload: dict[str, Any]) -> TruthStatus:
    value = _read_str(payload, "expectedTruthStatus")
    if value not in {"safe", "needs_review", "unsupported"}:
        raise ValueError("expectedTruthStatus must be safe, needs_review, or unsupported")
    return cast(TruthStatus, value)
