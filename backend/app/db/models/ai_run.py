from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.enums import AIProvider, AIRunStatus, AITaskType, ValidationStatus
from app.db.session import Base


class AIRun(Base):
    """Observability record for every AI/model call."""

    __tablename__ = "ai_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    session_id: Mapped[str | None] = mapped_column(String(120), index=True)

    task_type: Mapped[str] = mapped_column(String(60), default=AITaskType.EVAL.value, index=True)
    status: Mapped[str] = mapped_column(String(40), default=AIRunStatus.QUEUED.value, index=True)

    provider: Mapped[str] = mapped_column(String(40), default=AIProvider.OTHER.value, index=True)
    model_name: Mapped[str] = mapped_column(String(120), index=True)
    prompt_name: Mapped[str | None] = mapped_column(String(120), index=True)
    prompt_version: Mapped[str | None] = mapped_column(String(40))
    schema_version: Mapped[str | None] = mapped_column(String(80))
    temperature: Mapped[float | None] = mapped_column(Float)

    input_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    input_summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    input_token_count: Mapped[int | None]
    output_token_count: Mapped[int | None]
    total_token_count: Mapped[int | None]
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6))
    latency_ms: Mapped[int | None]

    validation_status: Mapped[str] = mapped_column(
        String(40), default=ValidationStatus.NOT_VALIDATED.value, index=True
    )
    validation_errors: Mapped[list[Any] | None] = mapped_column(JSONB)

    error_type: Mapped[str | None] = mapped_column(String(120))
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(default=0)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="ai_runs")
    outputs = relationship("AIOutput", back_populates="ai_run", cascade="all, delete-orphan")


class AIOutput(Base):
    """Validated or repaired output from an AI run."""

    __tablename__ = "ai_outputs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    ai_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_runs.id", ondelete="CASCADE"), index=True
    )

    output_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB)
    output_text: Mapped[str | None] = mapped_column(Text)
    validation_status: Mapped[str] = mapped_column(
        String(40), default=ValidationStatus.NOT_VALIDATED.value, index=True
    )
    validation_errors: Mapped[list[Any] | None] = mapped_column(JSONB)
    repair_attempted: Mapped[bool] = mapped_column(default=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ai_run = relationship("AIRun", back_populates="outputs")
