from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.ai.matching.normalization import normalize_skill, normalize_skill_list

ScoreBand = str


@dataclass(slots=True)
class SkillConfusionCounts:
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0


@dataclass(slots=True)
class ParsingMetrics:
    json_validity_rate: float
    schema_pass_rate: float
    skill_precision: float
    skill_recall: float
    skill_f1: float
    exact_name_match_rate: float
    average_confidence: float
    evaluated_examples: int


@dataclass(slots=True)
class MatchingMetrics:
    matched_skill_precision: float
    matched_skill_recall: float
    matched_skill_f1: float
    missing_skill_precision: float
    missing_skill_recall: float
    missing_skill_f1: float
    semantic_match_precision: float
    semantic_match_recall: float
    semantic_match_f1: float
    score_band_accuracy: float
    score_in_range_rate: float
    average_score_delta: float
    evaluated_examples: int


@dataclass(slots=True)
class TruthGuardMetrics:
    risky_recall: float
    unsupported_recall: float
    hallucination_rate: float
    safe_precision: float
    status_accuracy: float
    new_claim_detection_rate: float
    reviewed_case_rate: float
    evaluated_cases: int


@dataclass(slots=True)
class ParsingExampleResult:
    skill_counts: SkillConfusionCounts
    name_exact_match: bool
    confidence: float | None
    json_valid: bool = True
    schema_valid: bool = True


@dataclass(slots=True)
class MatchingExampleResult:
    matched_skill_counts: SkillConfusionCounts
    missing_skill_counts: SkillConfusionCounts
    semantic_match_counts: SkillConfusionCounts
    score_band_correct: bool
    score_in_expected_range: bool
    absolute_score_delta: int


@dataclass(slots=True)
class TruthGuardCaseResult:
    expected_risky: bool
    predicted_risky: bool
    expected_safe: bool
    predicted_safe: bool
    expected_unsupported: bool
    predicted_unsupported: bool
    expected_status_matches: bool
    new_claims_match: bool
    unexpected_new_claims: bool


def precision(true_positives: int, false_positives: int) -> float:
    denominator = true_positives + false_positives
    if denominator == 0:
        return 0.0
    return true_positives / denominator


def recall(true_positives: int, false_negatives: int) -> float:
    denominator = true_positives + false_negatives
    if denominator == 0:
        return 0.0
    return true_positives / denominator


def f1_score(precision_value: float, recall_value: float) -> float:
    denominator = precision_value + recall_value
    if denominator == 0:
        return 0.0
    return 2 * precision_value * recall_value / denominator


def skill_confusion_counts(
    expected_skills: list[str],
    actual_skills: list[str],
) -> SkillConfusionCounts:
    expected = set(normalize_skill_list(expected_skills))
    actual = set(normalize_skill_list(actual_skills))
    return SkillConfusionCounts(
        true_positives=len(expected & actual),
        false_positives=len(actual - expected),
        false_negatives=len(expected - actual),
    )


def compute_parsing_metrics(results: Iterable[ParsingExampleResult]) -> ParsingMetrics:
    result_list = list(results)
    total = len(result_list)
    counts = _aggregate_skill_counts(result.skill_counts for result in result_list)
    skill_precision = precision(counts.true_positives, counts.false_positives)
    skill_recall = recall(counts.true_positives, counts.false_negatives)
    average_confidence = sum(
        _or_zero(result.confidence) for result in result_list
    ) / max(total, 1)
    exact_name_match_rate = _fraction(
        sum(result.name_exact_match for result in result_list),
        total,
    )
    return ParsingMetrics(
        json_validity_rate=_fraction(sum(result.json_valid for result in result_list), total),
        schema_pass_rate=_fraction(sum(result.schema_valid for result in result_list), total),
        skill_precision=skill_precision,
        skill_recall=skill_recall,
        skill_f1=f1_score(skill_precision, skill_recall),
        exact_name_match_rate=exact_name_match_rate,
        average_confidence=average_confidence,
        evaluated_examples=total,
    )


def compute_matching_metrics(results: Iterable[MatchingExampleResult]) -> MatchingMetrics:
    result_list = list(results)
    total = len(result_list)
    matched_counts = _aggregate_skill_counts(result.matched_skill_counts for result in result_list)
    missing_counts = _aggregate_skill_counts(result.missing_skill_counts for result in result_list)
    semantic_counts = _aggregate_skill_counts(
        result.semantic_match_counts for result in result_list
    )

    matched_precision = precision(matched_counts.true_positives, matched_counts.false_positives)
    matched_recall = recall(matched_counts.true_positives, matched_counts.false_negatives)
    missing_precision = precision(missing_counts.true_positives, missing_counts.false_positives)
    missing_recall = recall(missing_counts.true_positives, missing_counts.false_negatives)
    semantic_precision = precision(
        semantic_counts.true_positives,
        semantic_counts.false_positives,
    )
    semantic_recall = recall(
        semantic_counts.true_positives,
        semantic_counts.false_negatives,
    )

    average_score_delta = sum(
        result.absolute_score_delta for result in result_list
    ) / max(total, 1)
    score_band_accuracy = _fraction(
        sum(result.score_band_correct for result in result_list),
        total,
    )
    score_in_range_rate = _fraction(
        sum(result.score_in_expected_range for result in result_list),
        total,
    )
    return MatchingMetrics(
        matched_skill_precision=matched_precision,
        matched_skill_recall=matched_recall,
        matched_skill_f1=f1_score(matched_precision, matched_recall),
        missing_skill_precision=missing_precision,
        missing_skill_recall=missing_recall,
        missing_skill_f1=f1_score(missing_precision, missing_recall),
        semantic_match_precision=semantic_precision,
        semantic_match_recall=semantic_recall,
        semantic_match_f1=f1_score(semantic_precision, semantic_recall),
        score_band_accuracy=score_band_accuracy,
        score_in_range_rate=score_in_range_rate,
        average_score_delta=average_score_delta,
        evaluated_examples=total,
    )


def compute_truth_guard_metrics(results: Iterable[TruthGuardCaseResult]) -> TruthGuardMetrics:
    result_list = list(results)
    total = len(result_list)
    risky_tp = sum(result.expected_risky and result.predicted_risky for result in result_list)
    risky_fn = sum(result.expected_risky and not result.predicted_risky for result in result_list)
    safe_tp = sum(result.expected_safe and result.predicted_safe for result in result_list)
    safe_fp = sum((not result.expected_safe) and result.predicted_safe for result in result_list)
    unsupported_tp = sum(
        result.expected_unsupported and result.predicted_unsupported
        for result in result_list
    )
    unsupported_fn = sum(
        result.expected_unsupported and not result.predicted_unsupported
        for result in result_list
    )

    return TruthGuardMetrics(
        risky_recall=recall(risky_tp, risky_fn),
        unsupported_recall=recall(unsupported_tp, unsupported_fn),
        hallucination_rate=_fraction(
            sum(result.unexpected_new_claims for result in result_list),
            total,
        ),
        safe_precision=precision(safe_tp, safe_fp),
        status_accuracy=_fraction(
            sum(result.expected_status_matches for result in result_list),
            total,
        ),
        new_claim_detection_rate=_fraction(
            sum(result.new_claims_match for result in result_list),
            total,
        ),
        reviewed_case_rate=_fraction(
            sum(result.predicted_risky for result in result_list),
            total,
        ),
        evaluated_cases=total,
    )


def classify_score_band(score: int) -> ScoreBand:
    if score >= 80:
        return "strong_match"
    if score >= 60:
        return "partial_match"
    return "weak_match"


def names_match(expected_name: str | None, actual_name: str | None) -> bool:
    if expected_name is None:
        return True
    if actual_name is None:
        return False
    return normalize_skill(expected_name) == normalize_skill(actual_name)


def _aggregate_skill_counts(counts: Iterable[SkillConfusionCounts]) -> SkillConfusionCounts:
    aggregate = SkillConfusionCounts()
    for count in counts:
        aggregate.true_positives += count.true_positives
        aggregate.false_positives += count.false_positives
        aggregate.false_negatives += count.false_negatives
    return aggregate


def _fraction(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _or_zero(value: float | None) -> float:
    if value is None:
        return 0.0
    return value
