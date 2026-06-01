from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.schemas.job import JobRead
from app.schemas.match_report import MatchReportRead
from app.schemas.optimization import OptimizedResumeRead
from app.schemas.resume import ResumeRead

JobInputType = Literal["text", "url", "file"]


class AnalyzeCreate(BaseModel):
    """JSON variant for one-shot analysis when the JD is pasted text or URL."""

    resume_text: Annotated[str, Field(min_length=20)] | None = None
    resume_title: str | None = Field(default=None, max_length=255)
    job_input_type: JobInputType = "text"
    job_text: Annotated[str, Field(min_length=50)] | None = None
    job_url: str | None = Field(default=None, max_length=2048)
    job_title: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    session_id: str | None = Field(default=None, max_length=120)


class AnalyzeRead(BaseModel):
    """Full response for one-shot AI analysis."""

    resume: ResumeRead
    job: JobRead
    match_report: MatchReportRead
    optimization: OptimizedResumeRead
