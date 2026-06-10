from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.ai.clients.base import LLMUsage
from app.ai.clients.openai_compat import OpenAICompatLLMClient
from app.ai.prompt_loader import load_prompt_template
from app.ai.schemas.evaluation import MatchRelevanceJudgment, ParseQualityJudgment
from app.core.config import Settings
from app.evals.datasets import PairEvaluationExample

PARSE_JUDGE_PROMPT = "eval_parse_judge.v1.md"
MATCH_JUDGE_PROMPT = "eval_match_judge.v1.md"


@dataclass(slots=True)
class EvalJudgeResult:
    judgment: ParseQualityJudgment | MatchRelevanceJudgment
    usage: LLMUsage


class EvalJudgeClient:
    def __init__(self, settings: Settings) -> None:
        self._client = OpenAICompatLLMClient(settings)

    async def judge_resume_parse(
        self,
        example: PairEvaluationExample,
        actual_json: dict[str, Any],
    ) -> EvalJudgeResult:
        expected_json = {
            "expected_candidate_name": example.resume_expectation.expected_candidate_name,
            "expected_skills": example.resume_expectation.expected_skills,
            "expected_languages": example.resume_expectation.expected_languages,
            "min_years_experience": example.resume_expectation.min_years_experience,
        }
        prompt = _render_parse_prompt(example.resume_text, expected_json, actual_json)
        judgment, usage = await self._client.generate_structured(
            prompt=prompt,
            output_model=ParseQualityJudgment,
        )
        return EvalJudgeResult(judgment=judgment, usage=usage)

    async def judge_job_parse(
        self,
        example: PairEvaluationExample,
        actual_json: dict[str, Any],
    ) -> EvalJudgeResult:
        expected_json = {
            "expected_title": example.job_expectation.expected_title,
            "expected_company": example.job_expectation.expected_company,
            "expected_required_skills": example.job_expectation.expected_required_skills,
            "expected_preferred_skills": example.job_expectation.expected_preferred_skills,
            "expected_seniority": example.job_expectation.expected_seniority,
        }
        prompt = _render_parse_prompt(example.job_text, expected_json, actual_json)
        judgment, usage = await self._client.generate_structured(
            prompt=prompt,
            output_model=ParseQualityJudgment,
        )
        return EvalJudgeResult(judgment=judgment, usage=usage)

    async def judge_match(
        self,
        example: PairEvaluationExample,
        match_json: dict[str, Any],
    ) -> EvalJudgeResult:
        expected_json = {
            "expected_score_band": example.matching_expectation.expected_score_band,
            "expected_score_min": example.matching_expectation.expected_score_min,
            "expected_score_max": example.matching_expectation.expected_score_max,
            "expected_matched_skills": example.matching_expectation.expected_matched_skills,
            "expected_missing_skills": example.matching_expectation.expected_missing_skills,
            "expected_semantic_matches": [
                {
                    "job_requirement": match.job_requirement,
                    "resume_evidence": match.resume_evidence,
                }
                for match in example.matching_expectation.expected_semantic_matches
            ],
        }
        prompt = load_prompt_template(MATCH_JUDGE_PROMPT)
        prompt = (
            prompt.replace("<<<RESUME_TEXT>>>", example.resume_text)
            .replace("<<<JOB_TEXT>>>", example.job_text)
            .replace("<<<EXPECTED_JSON>>>", json.dumps(expected_json, ensure_ascii=False))
            .replace("<<<MATCH_JSON>>>", json.dumps(match_json, ensure_ascii=False))
        )
        judgment, usage = await self._client.generate_structured(
            prompt=prompt,
            output_model=MatchRelevanceJudgment,
        )
        return EvalJudgeResult(judgment=judgment, usage=usage)


def create_eval_judge(
    settings: Settings,
    *,
    requested: bool,
) -> tuple[EvalJudgeClient | None, str | None]:
    if not requested:
        return None, None
    if settings.ai_provider != "openai":
        return None, "LLM judge skipped: AI_PROVIDER must be 'openai'."
    try:
        return EvalJudgeClient(settings), None
    except Exception as exc:
        return None, f"LLM judge skipped: {exc}"


def _render_parse_prompt(
    source_text: str,
    expected_json: dict[str, Any],
    actual_json: dict[str, Any],
) -> str:
    prompt = load_prompt_template(PARSE_JUDGE_PROMPT)
    return (
        prompt.replace("<<<SOURCE_TEXT>>>", source_text)
        .replace("<<<EXPECTED_JSON>>>", json.dumps(expected_json, ensure_ascii=False))
        .replace("<<<ACTUAL_JSON>>>", json.dumps(actual_json, ensure_ascii=False))
    )
