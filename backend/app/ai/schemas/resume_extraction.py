from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ResumeContact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None


class ResumeEducationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    school: str
    degree: str | None = None
    field_of_study: str | None = None


class ResumeExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_name: str | None = None
    headline: str | None = None
    contact: ResumeContact = Field(default_factory=ResumeContact)
    summary: str | None = None
    total_years_experience: float | None = None
    skills: list[str] = Field(default_factory=list)
    experience_highlights: list[str] = Field(default_factory=list)
    education: list[ResumeEducationItem] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
