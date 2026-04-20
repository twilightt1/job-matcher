from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class JobRequirementItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str
    evidence_text: str | None = None
    requirement_type: str = Field(default="required")


class JobExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    company: str | None = None
    location: str | None = None
    summary: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    requirements: list[JobRequirementItem] = Field(default_factory=list)
    seniority: str | None = None
    employment_type: str | None = None
    work_mode: str | None = None
