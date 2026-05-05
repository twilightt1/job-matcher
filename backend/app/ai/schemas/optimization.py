from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RewriteSuggestionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_type: str
    target_location: str | None = None
    original_text: str | None = None
    suggested_text: str
    targeted_requirements: list[str] = Field(default_factory=list)
    keywords_added: list[str] = Field(default_factory=list)
    reason: str
    estimated_score_lift: int = Field(ge=0, le=25)


class OptimizedResumeDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_name: str = "Targeted resume draft"
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_highlights: list[str] = Field(default_factory=list)
    suggestions: list[RewriteSuggestionDraft] = Field(default_factory=list)
    projected_score: int = Field(ge=0, le=100)
