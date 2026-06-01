from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.resume import Resume
from app.schemas.resume import ResumeCreate


async def create_resume(session: AsyncSession, payload: ResumeCreate) -> Resume:
    resume = Resume(
        title=payload.title,
        raw_text=payload.raw_text,
        session_id=payload.session_id,
    )
    session.add(resume)
    await session.commit()
    await session.refresh(resume)
    return resume


async def create_resume_from_ingestion(
    session: AsyncSession,
    *,
    title: str,
    raw_text: str,
    session_id: str | None,
    source_type: str,
    original_file_key: str | None = None,
    original_file_url: str | None = None,
) -> Resume:
    resume = Resume(
        title=title,
        raw_text=raw_text,
        session_id=session_id,
        source_type=source_type,
        original_file_key=original_file_key,
        original_file_url=original_file_url,
    )
    session.add(resume)
    await session.commit()
    await session.refresh(resume)
    return resume


async def get_resume(session: AsyncSession, resume_id: str) -> Resume | None:
    return await session.get(Resume, resume_id)
