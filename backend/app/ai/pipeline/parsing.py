from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.clients.local_job_parser import LocalJobParserClient
from app.ai.clients.local_resume_parser import LocalResumeParserClient
from app.ai.prompt_loader import load_prompt_template
from app.db.models.ai_run import AIOutput, AIRun
from app.db.models.enums import (
    AIProvider,
    AIRunStatus,
    AITaskType,
    ParseStatus,
    ValidationStatus,
)
from app.db.models.job import Job
from app.db.models.resume import Resume

RESUME_PROMPT_NAME = "resume_parser.v1.md"
JOB_PROMPT_NAME = "job_parser.v1.md"
PROMPT_VERSION = "v1"
SCHEMA_VERSION = "v1"


async def parse_resume_record(session: AsyncSession, resume: Resume) -> Resume:
    client = LocalResumeParserClient()
    prompt_template = load_prompt_template(RESUME_PROMPT_NAME)
    prompt_text = prompt_template.replace("<<<RESUME_TEXT>>>", resume.raw_text)
    input_hash = hashlib.sha256(resume.raw_text.encode("utf-8")).hexdigest()

    ai_run = AIRun(
        session_id=resume.session_id,
        task_type=AITaskType.RESUME_PARSE.value,
        status=AIRunStatus.RUNNING.value,
        provider=AIProvider.LOCAL.value,
        model_name=client.model_name,
        prompt_name=RESUME_PROMPT_NAME,
        prompt_version=PROMPT_VERSION,
        schema_version=SCHEMA_VERSION,
        temperature=0.0,
        input_hash=input_hash,
        input_summary_json={
            "resume_id": resume.id,
            "char_count": len(resume.raw_text),
            "prompt_preview": prompt_text[:120],
        },
        validation_status=ValidationStatus.NOT_VALIDATED.value,
        started_at=datetime.now(UTC),
    )
    session.add(ai_run)

    resume.parse_status = ParseStatus.PROCESSING.value
    await session.flush()

    try:
        result = client.parse_resume(resume.raw_text)
        output_json = _model_dump(result.extraction)
        ai_run.status = AIRunStatus.SUCCESS.value
        ai_run.validation_status = ValidationStatus.VALID.value
        ai_run.completed_at = datetime.now(UTC)
        ai_run.input_token_count = len(prompt_text.split())
        ai_run.output_token_count = max(1, len(str(output_json).split()))
        ai_run.total_token_count = ai_run.input_token_count + ai_run.output_token_count
        ai_run.latency_ms = 1

        session.add(
            AIOutput(
                ai_run=ai_run,
                output_json=output_json,
                validation_status=ValidationStatus.VALID.value,
                validation_errors=None,
                repair_attempted=False,
                metadata_json={"warnings": result.warnings},
            )
        )

        resume.parsed_json = output_json
        resume.parse_confidence = result.confidence
        resume.parse_warnings = result.warnings
        resume.parse_error = None
        resume.parse_status = ParseStatus.COMPLETED.value

        await session.commit()
        await session.refresh(resume)
        return resume
    except Exception as exc:
        ai_run.status = AIRunStatus.FAILED.value
        ai_run.validation_status = ValidationStatus.INVALID.value
        ai_run.error_type = exc.__class__.__name__
        ai_run.error_message = str(exc)
        ai_run.completed_at = datetime.now(UTC)

        resume.parse_status = ParseStatus.FAILED.value
        resume.parse_error = str(exc)
        resume.parse_warnings = ["Parsing failed."]

        await session.commit()
        raise


async def parse_job_record(session: AsyncSession, job: Job) -> Job:
    client = LocalJobParserClient()
    prompt_template = load_prompt_template(JOB_PROMPT_NAME)
    prompt_text = prompt_template.replace("<<<JOB_DESCRIPTION>>>", job.description)
    input_hash = hashlib.sha256(job.description.encode("utf-8")).hexdigest()

    ai_run = AIRun(
        session_id=job.session_id,
        task_type=AITaskType.JOB_PARSE.value,
        status=AIRunStatus.RUNNING.value,
        provider=AIProvider.LOCAL.value,
        model_name=client.model_name,
        prompt_name=JOB_PROMPT_NAME,
        prompt_version=PROMPT_VERSION,
        schema_version=SCHEMA_VERSION,
        temperature=0.0,
        input_hash=input_hash,
        input_summary_json={
            "job_id": job.id,
            "char_count": len(job.description),
            "prompt_preview": prompt_text[:120],
        },
        validation_status=ValidationStatus.NOT_VALIDATED.value,
        started_at=datetime.now(UTC),
    )
    session.add(ai_run)

    job.parse_status = ParseStatus.PROCESSING.value
    await session.flush()

    try:
        result = client.parse_job(job.description)
        output_json = _model_dump(result.extraction)
        ai_run.status = AIRunStatus.SUCCESS.value
        ai_run.validation_status = ValidationStatus.VALID.value
        ai_run.completed_at = datetime.now(UTC)
        ai_run.input_token_count = len(prompt_text.split())
        ai_run.output_token_count = max(1, len(str(output_json).split()))
        ai_run.total_token_count = ai_run.input_token_count + ai_run.output_token_count
        ai_run.latency_ms = 1

        session.add(
            AIOutput(
                ai_run=ai_run,
                output_json=output_json,
                validation_status=ValidationStatus.VALID.value,
                validation_errors=None,
                repair_attempted=False,
                metadata_json={"warnings": result.warnings},
            )
        )

        job.parsed_json = output_json
        job.parse_confidence = result.confidence
        job.parse_warnings = result.warnings
        job.parse_error = None
        job.parse_status = ParseStatus.COMPLETED.value

        if result.extraction.title:
            job.title = job.title or result.extraction.title
        if result.extraction.company:
            job.company = job.company or result.extraction.company
        if result.extraction.work_mode:
            job.work_mode = result.extraction.work_mode
        if result.extraction.employment_type:
            job.employment_type = result.extraction.employment_type
        if result.extraction.seniority:
            job.seniority = result.extraction.seniority

        await session.commit()
        await session.refresh(job)
        return job
    except Exception as exc:
        ai_run.status = AIRunStatus.FAILED.value
        ai_run.validation_status = ValidationStatus.INVALID.value
        ai_run.error_type = exc.__class__.__name__
        ai_run.error_message = str(exc)
        ai_run.completed_at = datetime.now(UTC)

        job.parse_status = ParseStatus.FAILED.value
        job.parse_error = str(exc)
        job.parse_warnings = ["Parsing failed."]

        await session.commit()
        raise


def _model_dump(model: Any) -> dict[str, Any]:
    return dict(model.model_dump(mode="json"))
