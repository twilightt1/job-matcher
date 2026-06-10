from __future__ import annotations

import asyncio
from pathlib import Path

from app.evals.datasets import load_pair_examples, load_truth_guard_cases
from app.evals.metrics import (
    MatchingExampleResult,
    ParsingExampleResult,
    SkillConfusionCounts,
    TruthGuardCaseResult,
    compute_matching_metrics,
    compute_parsing_metrics,
    compute_truth_guard_metrics,
)
from app.evals.runner import run_evaluation_task


def test_metrics_aggregation_stays_stable() -> None:
    parsing_metrics = compute_parsing_metrics(
        [
            ParsingExampleResult(
                skill_counts=SkillConfusionCounts(
                    true_positives=2,
                    false_positives=0,
                    false_negatives=1,
                ),
                name_exact_match=True,
                confidence=0.8,
                json_valid=True,
                schema_valid=True,
            ),
            ParsingExampleResult(
                skill_counts=SkillConfusionCounts(
                    true_positives=1,
                    false_positives=1,
                    false_negatives=0,
                ),
                name_exact_match=False,
                confidence=0.6,
                json_valid=True,
                schema_valid=False,
            ),
        ]
    )
    matching_metrics = compute_matching_metrics(
        [
            MatchingExampleResult(
                matched_skill_counts=SkillConfusionCounts(
                    true_positives=2,
                    false_positives=1,
                    false_negatives=0,
                ),
                missing_skill_counts=SkillConfusionCounts(
                    true_positives=1,
                    false_positives=0,
                    false_negatives=1,
                ),
                semantic_match_counts=SkillConfusionCounts(
                    true_positives=1,
                    false_positives=1,
                    false_negatives=0,
                ),
                score_band_correct=True,
                score_in_expected_range=True,
                absolute_score_delta=12,
            )
        ]
    )
    truth_guard_metrics = compute_truth_guard_metrics(
        [
            TruthGuardCaseResult(
                expected_risky=True,
                predicted_risky=True,
                expected_safe=False,
                predicted_safe=False,
                expected_unsupported=True,
                predicted_unsupported=True,
                expected_status_matches=True,
                new_claims_match=True,
                unexpected_new_claims=False,
            ),
            TruthGuardCaseResult(
                expected_risky=False,
                predicted_risky=False,
                expected_safe=True,
                predicted_safe=True,
                expected_unsupported=False,
                predicted_unsupported=False,
                expected_status_matches=True,
                new_claims_match=True,
                unexpected_new_claims=False,
            ),
        ]
    )

    assert parsing_metrics.skill_precision == 0.75
    assert round(parsing_metrics.skill_recall, 2) == 0.75
    assert parsing_metrics.schema_pass_rate == 0.5
    assert parsing_metrics.average_confidence == 0.7

    assert round(matching_metrics.matched_skill_precision, 2) == 0.67
    assert matching_metrics.score_band_accuracy == 1.0
    assert matching_metrics.score_in_range_rate == 1.0
    assert matching_metrics.semantic_match_precision == 0.5
    assert matching_metrics.semantic_match_recall == 1.0
    assert matching_metrics.average_score_delta == 12.0

    assert truth_guard_metrics.risky_recall == 1.0
    assert truth_guard_metrics.unsupported_recall == 1.0
    assert truth_guard_metrics.status_accuracy == 1.0
    assert truth_guard_metrics.new_claim_detection_rate == 1.0
    assert truth_guard_metrics.safe_precision == 1.0
    assert truth_guard_metrics.hallucination_rate == 0.0


def test_run_evaluation_task_writes_report_without_persistence() -> None:
    report = asyncio.run(run_evaluation_task(task="all", dataset="v1", persist=False))

    assert report.report_path is not None
    assert report.report_path.exists()
    assert report.persisted_run_id is None
    assert [task.task_name for task in report.tasks] == [
        "resume_parser",
        "job_parser",
        "matching",
        "truth_guard",
    ]

    report_text = Path(report.report_path).read_text(encoding="utf-8")
    assert "# Evaluation Report (v1)" in report_text
    assert "## Resume parser" in report_text
    assert "## Truth guard" in report_text


def test_phase_3_dataset_loads_diverse_labeled_examples() -> None:
    examples = load_pair_examples("v2")

    assert len(examples) >= 20
    assert len(examples) <= 30
    assert {example.resume_id for example in examples}
    assert any(
        example.matching_expectation.expected_semantic_matches
        for example in examples
    )
    assert all(
        example.matching_expectation.expected_score_min is not None
        and example.matching_expectation.expected_score_max is not None
        for example in examples
    )
    assert any("vi" in example.example_id for example in examples)


def test_llm_judge_request_is_skipped_without_openai_provider() -> None:
    report = asyncio.run(
        run_evaluation_task(
            task="matching",
            dataset="v1",
            persist=False,
            with_llm_judge=True,
        )
    )

    assert any("LLM judge skipped" in warning for warning in report.warnings)


def test_phase_4_truth_guard_dataset_has_labeled_safety_cases() -> None:
    cases = load_truth_guard_cases("v2")
    statuses = {case.expected_truth_status for case in cases}

    assert len(cases) >= 10
    assert statuses == {"safe", "needs_review", "unsupported"}
    assert any(case.expected_new_claims for case in cases)
