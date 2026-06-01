from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.config import Settings, get_settings
from app.schemas.analyze import AnalyzeRead
from app.schemas.job import JobRead
from app.schemas.match_report import MatchReportRead
from app.schemas.optimization import OptimizedResumeRead
from app.schemas.resume import ResumeRead
from app.services.ingestion.extractors import IngestionError
from app.services.ingestion.workflow import (
    create_job_from_text,
    create_job_from_upload,
    create_job_from_url,
    create_resume_from_text,
    create_resume_from_upload,
    ingestion_http_error,
    run_analysis,
)

DbSession = Depends(get_db_session)
SettingsDep = Depends(get_settings)
JobInputType = Literal["text", "url", "file"]

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.post("", response_model=AnalyzeRead, status_code=status.HTTP_201_CREATED)
async def analyze_endpoint(
    resume_file: Annotated[
        UploadFile | None,
        File(description="Resume PDF, DOCX, or TXT file"),
    ] = None,
    job_file: Annotated[
        UploadFile | None,
        File(description="JD PDF, DOCX, or TXT file"),
    ] = None,
    resume_text: Annotated[str | None, Form()] = None,
    resume_title: Annotated[str | None, Form(max_length=255)] = None,
    job_input_type: Annotated[JobInputType, Form()] = "text",
    job_text: Annotated[str | None, Form()] = None,
    job_url: Annotated[str | None, Form(max_length=2048)] = None,
    job_title: Annotated[str | None, Form(max_length=255)] = None,
    company: Annotated[str | None, Form(max_length=255)] = None,
    session_id: Annotated[str | None, Form(max_length=120)] = None,
    session: AsyncSession = DbSession,
    settings: Settings = SettingsDep,
) -> AnalyzeRead:
    try:
        if resume_file is not None:
            resume = await create_resume_from_upload(
                session,
                file=resume_file,
                settings=settings,
                title=resume_title,
                session_id=session_id,
            )
        elif resume_text:
            resume = await create_resume_from_text(
                session,
                text=resume_text,
                title=resume_title,
                session_id=session_id,
            )
        else:
            raise IngestionError("Provide a resume file or pasted resume text.")

        if job_input_type == "file":
            if job_file is None:
                raise IngestionError(
                    "Provide a job description file when job_input_type is 'file'."
                )
            job = await create_job_from_upload(
                session,
                file=job_file,
                settings=settings,
                title=job_title,
                company=company,
                session_id=session_id,
            )
        elif job_input_type == "url":
            if not job_url:
                raise IngestionError("Provide a job URL when job_input_type is 'url'.")
            job = await create_job_from_url(
                session,
                url=job_url,
                settings=settings,
                title=job_title,
                company=company,
                session_id=session_id,
            )
        elif job_input_type == "text":
            if not job_text:
                raise IngestionError("Provide pasted job description text.")
            job = await create_job_from_text(
                session,
                text=job_text,
                title=job_title,
                company=company,
                session_id=session_id,
            )
        else:
            raise IngestionError("job_input_type must be text, url, or file.")

        bundle = await run_analysis(session, resume=resume, job=job)
    except IngestionError as exc:
        raise ingestion_http_error(exc) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return AnalyzeRead(
        resume=ResumeRead.model_validate(bundle.resume),
        job=JobRead.model_validate(bundle.job),
        match_report=MatchReportRead.model_validate(bundle.match_report),
        optimization=OptimizedResumeRead.model_validate(bundle.optimization),
    )
