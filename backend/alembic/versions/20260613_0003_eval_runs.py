"""add evaluation run tables

Revision ID: 20260613_0003
Revises: 20260613_0002
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260613_0003"
down_revision: str | None = "20260613_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "eval_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("session_id", sa.String(length=120), nullable=True),
        sa.Column("dataset_name", sa.String(length=80), nullable=False),
        sa.Column("requested_task", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="success"),
        sa.Column("report_path", sa.String(length=1024), nullable=True),
        sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("warnings_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_eval_runs_user_id", "eval_runs", ["user_id"])
    op.create_index("ix_eval_runs_session_id", "eval_runs", ["session_id"])
    op.create_index("ix_eval_runs_dataset_name", "eval_runs", ["dataset_name"])
    op.create_index("ix_eval_runs_requested_task", "eval_runs", ["requested_task"])
    op.create_index("ix_eval_runs_status", "eval_runs", ["status"])

    op.create_table(
        "eval_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "eval_run_id",
            sa.String(length=36),
            sa.ForeignKey("eval_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("task_name", sa.String(length=80), nullable=False),
        sa.Column("metric_name", sa.String(length=120), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("display_value", sa.String(length=80), nullable=False),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_eval_results_eval_run_id", "eval_results", ["eval_run_id"])
    op.create_index("ix_eval_results_task_name", "eval_results", ["task_name"])
    op.create_index("ix_eval_results_metric_name", "eval_results", ["metric_name"])


def downgrade() -> None:
    op.drop_table("eval_results")
    op.drop_table("eval_runs")
