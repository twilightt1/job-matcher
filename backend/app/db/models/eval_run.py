from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class EvalRun(Base):
    """One persisted evaluation harness execution."""

    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    session_id: Mapped[str | None] = mapped_column(String(120), index=True)
    dataset_name: Mapped[str] = mapped_column(String(80), index=True)
    requested_task: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(40), default="success", index=True)
    report_path: Mapped[str | None] = mapped_column(String(1024))
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSONB)
    warnings_json: Mapped[list[Any] | None] = mapped_column(JSONB)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="eval_runs")
    results = relationship("EvalResult", back_populates="eval_run", cascade="all, delete-orphan")


class EvalResult(Base):
    """Per-task evaluation output and metrics."""

    __tablename__ = "eval_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    eval_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("eval_runs.id", ondelete="CASCADE"), index=True
    )
    task_name: Mapped[str] = mapped_column(String(80), index=True)
    metric_name: Mapped[str] = mapped_column(String(120), index=True)
    metric_value: Mapped[float] = mapped_column(Float)
    display_value: Mapped[str] = mapped_column(String(80))
    details_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    eval_run = relationship("EvalRun", back_populates="results")
