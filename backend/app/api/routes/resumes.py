from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.pipeline import parse_resume_record
from app.api.deps import get_db_session
from app.core.config import Settings, get_settings
from app.db.models.enums import AITaskType, ParseStatus
from app.db.repositories.ai_run_repository import list_ai_runs_for_session
from app.db.repositories.resume_repository import create_resume, get_resume
from app.schemas.parsing import (
    AIRunRead,
    ParseDiagnosticsRead,
    ResumeParseRead,
    ResumeParseRequest,
)
from app.schemas.resume import ResumeCreate, ResumeRead
from app.services.ingestion.extractors import IngestionError
from app.services.ingestion.workflow import create_resume_from_upload, ingestion_http_error

DbSession = Depends(get_db_session)
SettingsDep = Depends(get_settings)

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def create_resume_endpoint(
    payload: ResumeCreate,
    session: AsyncSession = DbSession,
) -> ResumeRead:
    resume = await create_resume(session, payload)
    return ResumeRead.model_validate(resume)


@router.post("/upload", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def upload_resume_endpoint(
    file: Annotated[UploadFile, File(description="Resume PDF, DOCX, or TXT file")],
    title: Annotated[str | None, Form(max_length=255)] = None,
    session_id: Annotated[str | None, Form(max_length=120)] = None,
    parse_immediately: Annotated[bool, Form()] = False,
    session: AsyncSession = DbSession,
    settings: Settings = SettingsDep,
) -> ResumeRead:
    try:
        resume = await create_resume_from_upload(
            session,
            file=file,
            settings=settings,
            title=title,
            session_id=session_id,
            parse_immediately=parse_immediately,
        )
    except IngestionError as exc:
        raise ingestion_http_error(exc) from exc
    return ResumeRead.model_validate(resume)


@router.get("/{resume_id}", response_model=ResumeRead)
async def get_resume_endpoint(
    resume_id: str,
    session: AsyncSession = DbSession,
) -> ResumeRead:
    resume = await get_resume(session, resume_id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return ResumeRead.model_validate(resume)


@router.post("/{resume_id}/parse", response_model=ResumeParseRead)
async def parse_resume_endpoint(
    resume_id: str,
    payload: ResumeParseRequest,
    session: AsyncSession = DbSession,
) -> ResumeParseRead:
    resume = await get_resume(session, resume_id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    if resume.parse_status == ParseStatus.COMPLETED.value and not payload.force_reparse:
        return ResumeParseRead.model_validate(resume)

    parsed_resume = await parse_resume_record(session, resume)
    return ResumeParseRead.model_validate(parsed_resume)


@router.get("/{resume_id}/parse-diagnostics", response_model=ParseDiagnosticsRead)
async def get_resume_parse_diagnostics(
    resume_id: str,
    session: AsyncSession = DbSession,
) -> ParseDiagnosticsRead:
    resume = await get_resume(session, resume_id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    ai_runs = await list_ai_runs_for_session(session, resume.session_id, AITaskType.RESUME_PARSE)
    return ParseDiagnosticsRead(ai_runs=[AIRunRead.model_validate(ai_run) for ai_run in ai_runs])
