from __future__ import annotations

import asyncio
import json
from argparse import ArgumentParser
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from app.ai.clients.local_job_parser import LocalJobParserClient
from app.ai.clients.local_resume_parser import LocalResumeParserClient
from app.ai.guardrails.truth_guard import LocalTruthGuard
from app.ai.schemas import JobExtraction, ResumeExtraction
from app.ai.scoring.match_engine import DeterministicMatchEngine
from app.db.models.eval_run import EvalResult, EvalRun
from app.db.session import AsyncSessionLocal
from app.evals.datasets import (
    PairEvaluationExample,
    TruthGuardEvaluationCase,
    load_pair_examples,
    load_truth_guard_cases,
)
from app.evals.metrics import (
    MatchingExampleResult,
    ParsingExampleResult,
    TruthGuardCaseResult,
    classify_score_band,
    compute_matching_metrics,
    compute_parsing_metrics,
    compute_truth_guard_metrics,
    names_match,
    skill_confusion_counts,
)
from app.evals.report import write_markdown_report
from app.evals.types import (
    EvaluationRunReport,
    ExampleEntry,
    MetricEntry,
    TaskEvaluationReport,
)

SUPPORTED_TASKS = {"resume_parser", "job_parser", "matching", "truth_guard", "all"}


async def run_evaluation_task(
    task: str,
    dataset: str,
    *,
    persist: bool = True,
) -> EvaluationRunReport:
    selected_tasks = _resolve_tasks(task)
    pair_examples = load_pair_examples(dataset)
    truth_guard_cases = load_truth_guard_cases(dataset)

    report = EvaluationRunReport(requested_task=task, dataset=dataset)
    resume_parser = LocalResumeParserClient()
    job_parser = LocalJobParserClient()
    truth_guard = LocalTruthGuard()
    match_engine = DeterministicMatchEngine()

    if "resume_parser" in selected_tasks:
        report.tasks.append(_evaluate_resume_parser(pair_examples, resume_parser))
    if "job_parser" in selected_tasks:
        report.tasks.append(_evaluate_job_parser(pair_examples, job_parser))
    if "matching" in selected_tasks:
        report.tasks.append(
            _evaluate_matching(
                pair_examples,
                resume_parser,
                job_parser,
                match_engine,
            )
        )
    if "truth_guard" in selected_tasks:
        report.tasks.append(
            _evaluate_truth_guard(
                truth_guard_cases,
                resume_parser,
                truth_guard,
            )
        )

    report.report_path = write_markdown_report(report)

    if persist:
        try:
            report.persisted_run_id = await _persist_report(report)
            report.report_path = write_markdown_report(report)
        except Exception as exc:  # pragma: no cover - exercised in runtime verification
            report.warnings.append(f"Persistence skipped: {exc}")
            report.report_path = write_markdown_report(report)

    return report


def _evaluate_resume_parser(
    pair_examples: list[PairEvaluationExample],
    parser: LocalResumeParserClient,
) -> TaskEvaluationReport:
    metrics_input: list[ParsingExampleResult] = []
    examples: list[ExampleEntry] = []
    latencies: list[float] = []

    for example in pair_examples:
        started_at = perf_counter()
        parsed = parser.parse_resume(example.resume_text)
        latencies.append((perf_counter() - started_at) * 1000)

        extraction_json = parsed.extraction.model_dump()
        skill_counts = skill_confusion_counts(
            example.resume_expectation.expected_skills,
            parsed.extraction.skills,
        )
        name_matches = names_match(
            example.resume_expectation.expected_candidate_name,
            parsed.extraction.candidate_name,
        )
        metrics_input.append(
            ParsingExampleResult(
                skill_counts=skill_counts,
                name_exact_match=name_matches,
                confidence=parsed.confidence,
                json_valid=_is_json_ready(extraction_json),
                schema_valid=_schema_valid(ResumeExtraction, extraction_json),
            )
        )

        expected_language_set = {
            language.lower()
            for language in example.resume_expectation.expected_languages
        }
        actual_language_set = {
            language.lower() for language in parsed.extraction.languages
        }
        language_pass = expected_language_set.issubset(actual_language_set)
        years_pass = _minimum_years_pass(
            example.resume_expectation.min_years_experience,
            parsed.extraction.total_years_experience,
        )
        status = "pass" if name_matches and language_pass and years_pass else "review"
        examples.append(
            ExampleEntry(
                example_id=example.example_id,
                status=status,
                summary=(
                    f"Parsed `{parsed.extraction.candidate_name or 'unknown'}` with "
                    f"{len(parsed.extraction.skills)} skills and confidence "
                    f"{parsed.confidence:.2f}."
                ),
                details_json={
                    "expected_skills": example.resume_expectation.expected_skills,
                    "actual_skills": parsed.extraction.skills,
                    "expected_languages": example.resume_expectation.expected_languages,
                    "actual_languages": parsed.extraction.languages,
                    "expected_years": example.resume_expectation.min_years_experience,
                    "actual_years": parsed.extraction.total_years_experience,
                },
            )
        )

    aggregated = compute_parsing_metrics(metrics_input)
    return TaskEvaluationReport(
        task_name="resume_parser",
        display_name="Resume parser",
        metrics=[
            _percent_metric(
                "json_validity_rate",
                aggregated.json_validity_rate,
                "How often resume parser output can be serialized to JSON.",
            ),
            _percent_metric(
                "schema_pass_rate",
                aggregated.schema_pass_rate,
                "How often parsed resumes satisfy the strict Pydantic schema.",
            ),
            _percent_metric(
                "skill_precision",
                aggregated.skill_precision,
                "Share of extracted resume skills that were expected by the dataset.",
            ),
            _percent_metric(
                "skill_recall",
                aggregated.skill_recall,
                "Share of expected resume skills recovered by the parser.",
            ),
            _percent_metric(
                "skill_f1",
                aggregated.skill_f1,
                "Balanced precision and recall for extracted resume skills.",
            ),
            _percent_metric(
                "exact_name_match_rate",
                aggregated.exact_name_match_rate,
                "How often the parser captures the expected candidate name.",
            ),
            _float_metric(
                "average_confidence",
                aggregated.average_confidence,
                "Average parser confidence across resume examples.",
            ),
        ],
        examples=examples,
        average_latency_ms=_average(latencies),
    )


def _evaluate_job_parser(
    pair_examples: list[PairEvaluationExample],
    parser: LocalJobParserClient,
) -> TaskEvaluationReport:
    metrics_input: list[ParsingExampleResult] = []
    examples: list[ExampleEntry] = []
    latencies: list[float] = []

    for example in pair_examples:
        started_at = perf_counter()
        parsed = parser.parse_job(example.job_text)
        latencies.append((perf_counter() - started_at) * 1000)

        extraction_json = parsed.extraction.model_dump()
        expected_skills = (
            example.job_expectation.expected_required_skills
            + example.job_expectation.expected_preferred_skills
        )
        actual_skills = (
            parsed.extraction.required_skills + parsed.extraction.preferred_skills
        )
        skill_counts = skill_confusion_counts(expected_skills, actual_skills)
        title_matches = names_match(
            example.job_expectation.expected_title,
            parsed.extraction.title,
        )
        metrics_input.append(
            ParsingExampleResult(
                skill_counts=skill_counts,
                name_exact_match=title_matches,
                confidence=parsed.confidence,
                json_valid=_is_json_ready(extraction_json),
                schema_valid=_schema_valid(JobExtraction, extraction_json),
            )
        )

        company_matches = names_match(
            example.job_expectation.expected_company,
            parsed.extraction.company,
        )
        seniority_matches = (
            parsed.extraction.seniority == example.job_expectation.expected_seniority
        )
        status = "pass" if title_matches and company_matches and seniority_matches else "review"
        examples.append(
            ExampleEntry(
                example_id=example.example_id,
                status=status,
                summary=(
                    f"Parsed job `{parsed.extraction.title or 'unknown'}` with "
                    f"{len(parsed.extraction.required_skills)} required skills."
                ),
                details_json={
                    "expected_required_skills": example.job_expectation.expected_required_skills,
                    "actual_required_skills": parsed.extraction.required_skills,
                    "expected_preferred_skills": example.job_expectation.expected_preferred_skills,
                    "actual_preferred_skills": parsed.extraction.preferred_skills,
                    "expected_company": example.job_expectation.expected_company,
                    "actual_company": parsed.extraction.company,
                },
            )
        )

    aggregated = compute_parsing_metrics(metrics_input)
    return TaskEvaluationReport(
        task_name="job_parser",
        display_name="Job parser",
        metrics=[
            _percent_metric(
                "json_validity_rate",
                aggregated.json_validity_rate,
                "How often job parser output can be serialized to JSON.",
            ),
            _percent_metric(
                "schema_pass_rate",
                aggregated.schema_pass_rate,
                "How often parsed jobs satisfy the strict Pydantic schema.",
            ),
            _percent_metric(
                "skill_precision",
                aggregated.skill_precision,
                "Share of extracted job skills that were expected by the dataset.",
            ),
            _percent_metric(
                "skill_recall",
                aggregated.skill_recall,
                "Share of expected job skills recovered by the parser.",
            ),
            _percent_metric(
                "skill_f1",
                aggregated.skill_f1,
                "Balanced precision and recall for extracted job skills.",
            ),
            _percent_metric(
                "exact_title_match_rate",
                aggregated.exact_name_match_rate,
                "How often the parser captures the expected job title.",
            ),
            _float_metric(
                "average_confidence",
                aggregated.average_confidence,
                "Average parser confidence across job examples.",
            ),
        ],
        examples=examples,
        average_latency_ms=_average(latencies),
    )


def _evaluate_matching(
    pair_examples: list[PairEvaluationExample],
    resume_parser: LocalResumeParserClient,
    job_parser: LocalJobParserClient,
    engine: DeterministicMatchEngine,
) -> TaskEvaluationReport:
    metrics_input: list[MatchingExampleResult] = []
    examples: list[ExampleEntry] = []
    latencies: list[float] = []

    for example in pair_examples:
        parsed_resume = resume_parser.parse_resume(example.resume_text)
        parsed_job = job_parser.parse_job(example.job_text)

        started_at = perf_counter()
        result = engine.compute(
            parsed_resume.extraction,
            parsed_job.extraction,
            resume_parse_confidence=parsed_resume.confidence,
            job_parse_confidence=parsed_job.confidence,
        )
        latencies.append((perf_counter() - started_at) * 1000)

        predicted_band = classify_score_band(result.overall_score)
        metrics_input.append(
            MatchingExampleResult(
                matched_skill_counts=skill_confusion_counts(
                    example.matching_expectation.expected_matched_skills,
                    result.matched_skills,
                ),
                missing_skill_counts=skill_confusion_counts(
                    example.matching_expectation.expected_missing_skills,
                    result.missing_skills,
                ),
                score_band_correct=(
                    predicted_band
                    == example.matching_expectation.expected_score_band
                ),
                absolute_score_delta=abs(
                    result.overall_score
                    - _expected_band_anchor(
                        example.matching_expectation.expected_score_band
                    )
                ),
            )
        )

        status = (
            "pass"
            if predicted_band == example.matching_expectation.expected_score_band
            else "review"
        )
        examples.append(
            ExampleEntry(
                example_id=example.example_id,
                status=status,
                summary=(
                    f"Computed score `{result.overall_score}` with predicted band "
                    f"`{predicted_band}`."
                ),
                details_json={
                    "expected_band": example.matching_expectation.expected_score_band,
                    "predicted_band": predicted_band,
                    "expected_matched_skills": example.matching_expectation.expected_matched_skills,
                    "actual_matched_skills": result.matched_skills,
                    "expected_missing_skills": example.matching_expectation.expected_missing_skills,
                    "actual_missing_skills": result.missing_skills,
                },
            )
        )

    aggregated = compute_matching_metrics(metrics_input)
    return TaskEvaluationReport(
        task_name="matching",
        display_name="Matching engine",
        metrics=[
            _percent_metric(
                "matched_skill_precision",
                aggregated.matched_skill_precision,
                "Precision for the skills the match engine claims are covered.",
            ),
            _percent_metric(
                "matched_skill_recall",
                aggregated.matched_skill_recall,
                "Recall for expected matched skills.",
            ),
            _percent_metric(
                "matched_skill_f1",
                aggregated.matched_skill_f1,
                "Balanced score for matched-skill quality.",
            ),
            _percent_metric(
                "missing_skill_precision",
                aggregated.missing_skill_precision,
                "Precision for the skills the engine flags as missing.",
            ),
            _percent_metric(
                "missing_skill_recall",
                aggregated.missing_skill_recall,
                "Recall for expected missing skills.",
            ),
            _percent_metric(
                "missing_skill_f1",
                aggregated.missing_skill_f1,
                "Balanced score for missing-skill quality.",
            ),
            _percent_metric(
                "score_band_accuracy",
                aggregated.score_band_accuracy,
                "How often the deterministic score lands in the expected band.",
            ),
            _float_metric(
                "average_score_delta",
                aggregated.average_score_delta,
                "Average absolute distance from the target score band anchor.",
            ),
        ],
        examples=examples,
        average_latency_ms=_average(latencies),
    )


def _evaluate_truth_guard(
    truth_guard_cases: list[TruthGuardEvaluationCase],
    resume_parser: LocalResumeParserClient,
    truth_guard: LocalTruthGuard,
) -> TaskEvaluationReport:
    metrics_input: list[TruthGuardCaseResult] = []
    examples: list[ExampleEntry] = []
    latencies: list[float] = []

    for case in truth_guard_cases:
        parsed_resume = resume_parser.parse_resume(case.resume_text)

        started_at = perf_counter()
        decision = truth_guard.evaluate(case.suggestion, parsed_resume.extraction)
        latencies.append((perf_counter() - started_at) * 1000)

        actual_claims = {_normalize_claim(claim) for claim in decision.new_claims}
        expected_claims = {_normalize_claim(claim) for claim in case.expected_new_claims}
        expected_risky = case.expected_truth_status != "safe"
        predicted_risky = decision.truth_status != "safe"
        metrics_input.append(
            TruthGuardCaseResult(
                expected_risky=expected_risky,
                predicted_risky=predicted_risky,
                expected_safe=case.expected_truth_status == "safe",
                predicted_safe=decision.truth_status == "safe",
                expected_status_matches=decision.truth_status == case.expected_truth_status,
                unexpected_new_claims=actual_claims != expected_claims,
            )
        )

        status = (
            "pass"
            if (
                decision.truth_status == case.expected_truth_status
                and actual_claims == expected_claims
            )
            else "review"
        )
        examples.append(
            ExampleEntry(
                example_id=case.case_id,
                status=status,
                summary=(
                    f"Truth guard returned `{decision.truth_status}` with "
                    f"{len(decision.new_claims)} flagged claims."
                ),
                details_json={
                    "expected_truth_status": case.expected_truth_status,
                    "actual_truth_status": decision.truth_status,
                    "expected_new_claims": case.expected_new_claims,
                    "actual_new_claims": decision.new_claims,
                },
            )
        )

    aggregated = compute_truth_guard_metrics(metrics_input)
    return TaskEvaluationReport(
        task_name="truth_guard",
        display_name="Truth guard",
        metrics=[
            _percent_metric(
                "risky_recall",
                aggregated.risky_recall,
                "How often risky suggestions are escalated away from safe status.",
            ),
            _percent_metric(
                "hallucination_rate",
                aggregated.hallucination_rate,
                "Rate of cases where expected new-claim warnings were missed.",
            ),
            _percent_metric(
                "safe_precision",
                aggregated.safe_precision,
                "Precision of safe decisions when the suggestion is truly grounded.",
            ),
            _percent_metric(
                "reviewed_case_rate",
                aggregated.reviewed_case_rate,
                "Share of cases that the guard escalates for review or rejects.",
            ),
        ],
        examples=examples,
        average_latency_ms=_average(latencies),
    )


async def _persist_report(report: EvaluationRunReport) -> str:
    eval_run = EvalRun(
        id=str(uuid4()),
        dataset_name=report.dataset,
        requested_task=report.requested_task,
        status="completed_with_warnings" if report.warnings else "success",
        report_path=str(report.report_path) if report.report_path is not None else None,
        summary_json=report.summary_json(),
        warnings_json=report.warnings or None,
        started_at=report.generated_at,
        completed_at=report.generated_at,
    )

    async with AsyncSessionLocal() as session:
        session.add(eval_run)
        for task in report.tasks:
            for metric in task.metrics:
                session.add(
                    EvalResult(
                        id=str(uuid4()),
                        eval_run_id=eval_run.id,
                        task_name=task.task_name,
                        metric_name=metric.name,
                        metric_value=metric.value,
                        display_value=metric.display_value,
                        details_json={
                            "description": metric.description,
                            "example_ids": [example.example_id for example in task.examples],
                        },
                        notes=None,
                    )
                )
        await session.commit()
    return eval_run.id


def _resolve_tasks(task: str) -> list[str]:
    if task not in SUPPORTED_TASKS:
        raise ValueError(f"Unsupported task: {task}")
    if task == "all":
        return ["resume_parser", "job_parser", "matching", "truth_guard"]
    return [task]


def _expected_band_anchor(score_band: str) -> int:
    if score_band == "strong_match":
        return 90
    if score_band == "partial_match":
        return 70
    return 40


def _minimum_years_pass(expected_years: float | None, actual_years: float | None) -> bool:
    if expected_years is None:
        return True
    if actual_years is None:
        return False
    return actual_years >= expected_years


def _is_json_ready(payload: dict[str, Any]) -> bool:
    try:
        json.dumps(payload)
    except TypeError:
        return False
    return True


def _schema_valid(
    schema_type: type[ResumeExtraction] | type[JobExtraction],
    payload: dict[str, Any],
) -> bool:
    try:
        schema_type.model_validate(payload)
    except Exception:
        return False
    return True


def _normalize_claim(claim: str) -> str:
    return claim.strip().lower()


def _percent_metric(name: str, value: float, description: str) -> MetricEntry:
    return MetricEntry(
        name=name,
        value=value,
        display_value=f"{value * 100:.1f}%",
        description=description,
    )


def _float_metric(name: str, value: float, description: str) -> MetricEntry:
    return MetricEntry(
        name=name,
        value=value,
        display_value=f"{value:.2f}",
        description=description,
    )


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def main() -> None:
    parser = ArgumentParser(description="Run JobFit AI evaluation tasks.")
    parser.add_argument("--task", default="all", help="Evaluation task to run.")
    parser.add_argument("--dataset", default="v1", help="Dataset version to evaluate.")
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Skip database persistence and only write the markdown report.",
    )
    args = parser.parse_args()

    report = asyncio.run(
        run_evaluation_task(
            task=args.task,
            dataset=args.dataset,
            persist=not args.no_persist,
        )
    )
    report_path = report.report_path or Path("app/evals/reports")
    print(f"Completed evaluation for task={args.task!r}, dataset={args.dataset!r}.")
    print(f"Report written to: {report_path}")
    if report.persisted_run_id is not None:
        print(f"Persisted run id: {report.persisted_run_id}")
    if report.warnings:
        print("Warnings:")
        for warning in report.warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
