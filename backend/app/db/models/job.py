from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.enums import (
    EmploymentType,
    JobStatus,
    ParseStatus,
    Seniority,
    WorkMode,
)
from app.db.session import Base


class Job(Base):
    """Target job description and parsed AI requirements."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    session_id: Mapped[str | None] = mapped_column(String(120), index=True)

    title: Mapped[str | None] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(255), index=True)
    location: Mapped[str | None] = mapped_column(String(255))
    work_mode: Mapped[str] = mapped_column(String(40), default=WorkMode.UNKNOWN.value)
    employment_type: Mapped[str] = mapped_column(String(40), default=EmploymentType.UNKNOWN.value)
    seniority: Mapped[str] = mapped_column(String(40), default=Seniority.UNKNOWN.value)

    description: Mapped[str] = mapped_column(Text)
    parsed_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    parse_status: Mapped[str] = mapped_column(
        String(40), default=ParseStatus.PENDING.value, index=True
    )
    parse_confidence: Mapped[float | None] = mapped_column(Float)
    parse_warnings: Mapped[list[Any] | None] = mapped_column(JSONB)
    parse_error: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(40), default=JobStatus.SAVED.value, index=True)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    salary_text: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="jobs")
    match_reports = relationship("MatchReport", back_populates="job", cascade="all, delete-orphan")
