"""initial foundation tables

Revision ID: 20260613_0001
Revises:
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260613_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("plan", sa.String(length=40), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_plan", "users", ["plan"])

    op.create_table(
        "resumes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("session_id", sa.String(length=120), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False, server_default="Untitled Resume"),
        sa.Column("source_type", sa.String(length=40), nullable=False, server_default="text"),
        sa.Column("original_file_url", sa.String(length=2048), nullable=True),
        sa.Column("original_file_key", sa.String(length=1024), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("parsed_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("parse_status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("parse_confidence", sa.Float(), nullable=True),
        sa.Column("parse_warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("parse_error", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="en"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])
    op.create_index("ix_resumes_session_id", "resumes", ["session_id"])
    op.create_index("ix_resumes_parse_status", "resumes", ["parse_status"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("session_id", sa.String(length=120), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("work_mode", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column(
            "employment_type", sa.String(length=40), nullable=False, server_default="unknown"
        ),
        sa.Column("seniority", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("parsed_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("parse_status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("parse_confidence", sa.Float(), nullable=True),
        sa.Column("parse_warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("parse_error", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="saved"),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("salary_text", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"])
    op.create_index("ix_jobs_session_id", "jobs", ["session_id"])
    op.create_index("ix_jobs_company", "jobs", ["company"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_parse_status", "jobs", ["parse_status"])

    op.create_table(
        "ai_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("session_id", sa.String(length=120), nullable=True),
        sa.Column("task_type", sa.String(length=60), nullable=False, server_default="eval"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="queued"),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="other"),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("prompt_name", sa.String(length=120), nullable=True),
        sa.Column("prompt_version", sa.String(length=40), nullable=True),
        sa.Column("schema_version", sa.String(length=80), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("input_hash", sa.String(length=128), nullable=True),
        sa.Column("input_summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("input_token_count", sa.Integer(), nullable=True),
        sa.Column("output_token_count", sa.Integer(), nullable=True),
        sa.Column("total_token_count", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "validation_status",
            sa.String(length=40),
            nullable=False,
            server_default="not_validated",
        ),
        sa.Column("validation_errors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_type", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_runs_user_id", "ai_runs", ["user_id"])
    op.create_index("ix_ai_runs_session_id", "ai_runs", ["session_id"])
    op.create_index("ix_ai_runs_task_type", "ai_runs", ["task_type"])
    op.create_index("ix_ai_runs_status", "ai_runs", ["status"])
    op.create_index("ix_ai_runs_provider", "ai_runs", ["provider"])
    op.create_index("ix_ai_runs_model_name", "ai_runs", ["model_name"])
    op.create_index("ix_ai_runs_prompt_name", "ai_runs", ["prompt_name"])
    op.create_index("ix_ai_runs_input_hash", "ai_runs", ["input_hash"])
    op.create_index("ix_ai_runs_validation_status", "ai_runs", ["validation_status"])

    op.create_table(
        "ai_outputs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "ai_run_id", sa.String(length=36), sa.ForeignKey("ai_runs.id", ondelete="CASCADE")
        ),
        sa.Column("output_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column(
            "validation_status",
            sa.String(length=40),
            nullable=False,
            server_default="not_validated",
        ),
        sa.Column("validation_errors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("repair_attempted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_outputs_ai_run_id", "ai_outputs", ["ai_run_id"])
    op.create_index("ix_ai_outputs_validation_status", "ai_outputs", ["validation_status"])

    op.create_table(
        "match_reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("session_id", sa.String(length=120), nullable=True),
        sa.Column(
            "resume_id", sa.String(length=36), sa.ForeignKey("resumes.id", ondelete="CASCADE")
        ),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("jobs.id", ondelete="CASCADE")),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("analysis_confidence", sa.Float(), nullable=True),
        sa.Column("breakdown_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("strengths_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("gaps_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("recommendations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ats_report_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("explanation_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model_metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "generated_by_ai_run_id",
            sa.String(length=36),
            sa.ForeignKey("ai_runs.id", ondelete="SET NULL"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("resume_id", "job_id", name="uq_match_report_resume_job"),
    )
    op.create_index("ix_match_reports_user_id", "match_reports", ["user_id"])
    op.create_index("ix_match_reports_session_id", "match_reports", ["session_id"])
    op.create_index("ix_match_reports_resume_id", "match_reports", ["resume_id"])
    op.create_index("ix_match_reports_job_id", "match_reports", ["job_id"])
    op.create_index("ix_match_reports_overall_score", "match_reports", ["overall_score"])

    op.create_table(
        "match_evidence",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "match_report_id",
            sa.String(length=36),
            sa.ForeignKey("match_reports.id", ondelete="CASCADE"),
        ),
        sa.Column("requirement_id", sa.String(length=120), nullable=True),
        sa.Column("job_requirement_text", sa.Text(), nullable=False),
        sa.Column("resume_section_id", sa.String(length=120), nullable=True),
        sa.Column("resume_section_type", sa.String(length=80), nullable=True),
        sa.Column("resume_evidence_text", sa.Text(), nullable=True),
        sa.Column("match_type", sa.String(length=40), nullable=False, server_default="missing"),
        sa.Column("match_status", sa.String(length=40), nullable=False, server_default="missing"),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_match_evidence_match_report_id", "match_evidence", ["match_report_id"])
    op.create_index("ix_match_evidence_match_type", "match_evidence", ["match_type"])
    op.create_index("ix_match_evidence_match_status", "match_evidence", ["match_status"])
    op.create_index("ix_match_evidence_similarity_score", "match_evidence", ["similarity_score"])


def downgrade() -> None:
    op.drop_table("match_evidence")
    op.drop_table("match_reports")
    op.drop_table("ai_outputs")
    op.drop_table("ai_runs")
    op.drop_table("jobs")
    op.drop_table("resumes")
    op.drop_table("users")
