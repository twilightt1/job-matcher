from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.enums import ParseStatus, ResumeSourceType
from app.db.session import Base


class Resume(Base):
    """Resume source text and parsed AI extraction output."""

    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    session_id: Mapped[str | None] = mapped_column(String(120), index=True)

    title: Mapped[str] = mapped_column(String(255), default="Untitled Resume")
    source_type: Mapped[str] = mapped_column(String(40), default=ResumeSourceType.TEXT.value)
    original_file_url: Mapped[str | None] = mapped_column(String(2048))
    original_file_key: Mapped[str | None] = mapped_column(String(1024))
    raw_text: Mapped[str] = mapped_column(Text)

    parsed_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    parse_status: Mapped[str] = mapped_column(
        String(40), default=ParseStatus.PENDING.value, index=True
    )
    parse_confidence: Mapped[float | None] = mapped_column(Float)
    parse_warnings: Mapped[list[Any] | None] = mapped_column(JSONB)
    parse_error: Mapped[str | None] = mapped_column(Text)

    language: Mapped[str] = mapped_column(String(16), default="en")
    is_default: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="resumes")
    match_reports = relationship(
        "MatchReport", back_populates="resume", cascade="all, delete-orphan"
    )
