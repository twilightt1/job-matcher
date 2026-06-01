from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.job import Job
from app.schemas.job import JobCreate


async def create_job(session: AsyncSession, payload: JobCreate) -> Job:
    job = Job(
        title=payload.title,
        company=payload.company,
        description=payload.description,
        session_id=payload.session_id,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def create_job_from_ingestion(
    session: AsyncSession,
    *,
    description: str,
    title: str | None = None,
    company: str | None = None,
    session_id: str | None = None,
    source_url: str | None = None,
) -> Job:
    job = Job(
        title=title,
        company=company,
        description=description,
        session_id=session_id,
        source_url=source_url,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_job(session: AsyncSession, job_id: str) -> Job | None:
    return await session.get(Job, job_id)
