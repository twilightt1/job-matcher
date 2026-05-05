from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TruthStatus = Literal["safe", "needs_review", "unsupported"]


class TruthGuardDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    truth_status: TruthStatus
    new_claims: list[str] = Field(default_factory=list)
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)


class GuardedRewriteSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_type: str
    target_location: str | None = None
    original_text: str | None = None
    suggested_text: str
    targeted_requirements: list[str] = Field(default_factory=list)
    keywords_added: list[str] = Field(default_factory=list)
    reason: str
    estimated_score_lift: int = Field(ge=0, le=25)
    truth_status: TruthStatus
    new_claims: list[str] = Field(default_factory=list)
    guardrail_reason: str
