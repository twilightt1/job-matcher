from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.enums import MatchStatus, MatchType
from app.db.session import Base


class MatchReport(Base):
    """Explainable resume-job match score and AI-generated analysis."""

    __tablename__ = "match_reports"
    __table_args__ = (UniqueConstraint("resume_id", "job_id", name="uq_match_report_resume_job"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    session_id: Mapped[str | None] = mapped_column(String(120), index=True)

    resume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("resumes.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )

    overall_score: Mapped[int] = mapped_column(Integer, index=True)
    analysis_confidence: Mapped[float | None] = mapped_column(Float)

    breakdown_json: Mapped[dict[str, Any]] = mapped_column(JSONB)
    strengths_json: Mapped[list[Any] | None] = mapped_column(JSONB)
    gaps_json: Mapped[list[Any] | None] = mapped_column(JSONB)
    recommendations_json: Mapped[list[Any] | None] = mapped_column(JSONB)
    ats_report_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    explanation_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    model_metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    generated_by_ai_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ai_runs.id", ondelete="SET NULL")
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="match_reports")
    resume = relationship("Resume", back_populates="match_reports")
    job = relationship("Job", back_populates="match_reports")
    evidence = relationship(
        "MatchEvidence", back_populates="match_report", cascade="all, delete-orphan"
    )


class MatchEvidence(Base):
    """Evidence row linking a job requirement to resume support."""

    __tablename__ = "match_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    match_report_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("match_reports.id", ondelete="CASCADE"), index=True
    )

    requirement_id: Mapped[str | None] = mapped_column(String(120))
    job_requirement_text: Mapped[str] = mapped_column(Text)
    resume_section_id: Mapped[str | None] = mapped_column(String(120))
    resume_section_type: Mapped[str | None] = mapped_column(String(80))
    resume_evidence_text: Mapped[str | None] = mapped_column(Text)

    match_type: Mapped[str] = mapped_column(String(40), default=MatchType.MISSING.value, index=True)
    match_status: Mapped[str] = mapped_column(
        String(40), default=MatchStatus.MISSING.value, index=True
    )
    similarity_score: Mapped[float | None] = mapped_column(Float, index=True)
    confidence: Mapped[float | None] = mapped_column(Float)

    explanation: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    match_report = relationship("MatchReport", back_populates="evidence")
