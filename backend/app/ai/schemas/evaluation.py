from __future__ import annotations

from pydantic import BaseModel, Field


class ParseQualityJudgment(BaseModel):
    quality_score: float = Field(ge=0.0, le=1.0)
    hallucinated_items: list[str] = Field(default_factory=list)
    missing_items: list[str] = Field(default_factory=list)
    rationale: str


class MatchRelevanceJudgment(BaseModel):
    relevance_score: float = Field(ge=0.0, le=1.0)
    semantic_match_correct: bool
    score_calibration: str
    false_positive_evidence: list[str] = Field(default_factory=list)
    false_negative_evidence: list[str] = Field(default_factory=list)
    rationale: str
