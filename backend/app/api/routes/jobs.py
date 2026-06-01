from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.pipeline import parse_job_record
from app.api.deps import get_db_session
from app.core.config import Settings, get_settings
from app.db.models.enums import AITaskType, ParseStatus
from app.db.repositories.ai_run_repository import list_ai_runs_for_session
from app.db.repositories.job_repository import create_job, get_job
from app.schemas.job import JobCreate, JobFromUrlCreate, JobRead
from app.schemas.parsing import AIRunRead, JobParseRead, JobParseRequest, ParseDiagnosticsRead
from app.services.ingestion.extractors import IngestionError
from app.services.ingestion.workflow import (
    create_job_from_upload,
    create_job_from_url,
    ingestion_http_error,
)

DbSession = Depends(get_db_session)
SettingsDep = Depends(get_settings)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job_endpoint(
    payload: JobCreate,
    session: AsyncSession = DbSession,
) -> JobRead:
    job = await create_job(session, payload)
    return JobRead.model_validate(job)


@router.post("/upload", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def upload_job_endpoint(
    file: Annotated[UploadFile, File(description="Job description PDF, DOCX, or TXT file")],
    title: Annotated[str | None, Form(max_length=255)] = None,
    company: Annotated[str | None, Form(max_length=255)] = None,
    session_id: Annotated[str | None, Form(max_length=120)] = None,
    parse_immediately: Annotated[bool, Form()] = False,
    session: AsyncSession = DbSession,
    settings: Settings = SettingsDep,
) -> JobRead:
    try:
        job = await create_job_from_upload(
            session,
            file=file,
            settings=settings,
            title=title,
            company=company,
            session_id=session_id,
            parse_immediately=parse_immediately,
        )
    except IngestionError as exc:
        raise ingestion_http_error(exc) from exc
    return JobRead.model_validate(job)


@router.post("/from-url", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job_from_url_endpoint(
    payload: JobFromUrlCreate,
    session: AsyncSession = DbSession,
    settings: Settings = SettingsDep,
) -> JobRead:
    try:
        job = await create_job_from_url(
            session,
            url=payload.url,
            settings=settings,
            title=payload.title,
            company=payload.company,
            session_id=payload.session_id,
            parse_immediately=payload.parse_immediately,
        )
    except IngestionError as exc:
        raise ingestion_http_error(exc) from exc
    return JobRead.model_validate(job)


@router.get("/{job_id}", response_model=JobRead)
async def get_job_endpoint(
    job_id: str,
    session: AsyncSession = DbSession,
) -> JobRead:
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobRead.model_validate(job)


@router.post("/{job_id}/parse", response_model=JobParseRead)
async def parse_job_endpoint(
    job_id: str,
    payload: JobParseRequest,
    session: AsyncSession = DbSession,
) -> JobParseRead:
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.parse_status == ParseStatus.COMPLETED.value and not payload.force_reparse:
        return JobParseRead.model_validate(job)

    parsed_job = await parse_job_record(session, job)
    return JobParseRead.model_validate(parsed_job)


@router.get("/{job_id}/parse-diagnostics", response_model=ParseDiagnosticsRead)
async def get_job_parse_diagnostics(
    job_id: str,
    session: AsyncSession = DbSession,
) -> ParseDiagnosticsRead:
    job = await get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    ai_runs = await list_ai_runs_for_session(session, job.session_id, AITaskType.JOB_PARSE)
    return ParseDiagnosticsRead(ai_runs=[AIRunRead.model_validate(ai_run) for ai_run in ai_runs])
