from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app.core.config import Settings


async def ensure_embedding_vector_schema(engine: AsyncEngine, settings: Settings) -> None:
    """Keep pgvector embedding columns aligned with EMBEDDING_DIMENSION.

    Embeddings are derived/cache data, so when the configured dimension changes we
    clear existing embedding rows and alter the vector column type. This avoids
    pgvector insert failures such as "expected 384 dimensions, not 1024" after
    switching providers/models in .env.
    """

    dimension = settings.embedding_dimension
    if dimension <= 0:
        raise ValueError("EMBEDDING_DIMENSION must be greater than 0.")

    async with engine.begin() as connection:
        current_dimensions = await _get_current_dimensions(connection)
        if current_dimensions == {
            "resume_embeddings": dimension,
            "job_embeddings": dimension,
        }:
            return

        await connection.execute(text("DROP INDEX IF EXISTS resume_embeddings_embedding_hnsw_idx"))
        await connection.execute(text("DROP INDEX IF EXISTS job_embeddings_embedding_hnsw_idx"))
        await connection.execute(text("DELETE FROM resume_embeddings"))
        await connection.execute(text("DELETE FROM job_embeddings"))

        await connection.execute(
            text(
                f"ALTER TABLE resume_embeddings "
                f"ALTER COLUMN embedding TYPE vector({dimension}) "
                "USING NULL"
            )
        )
        await connection.execute(
            text(
                f"ALTER TABLE job_embeddings "
                f"ALTER COLUMN embedding TYPE vector({dimension}) "
                "USING NULL"
            )
        )
        await connection.execute(
            text(
                "ALTER TABLE resume_embeddings "
                f"ALTER COLUMN dimension SET DEFAULT {dimension}"
            )
        )
        await connection.execute(
            text(
                "ALTER TABLE job_embeddings "
                f"ALTER COLUMN dimension SET DEFAULT {dimension}"
            )
        )
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS resume_embeddings_embedding_hnsw_idx "
                "ON resume_embeddings USING hnsw (embedding vector_cosine_ops)"
            )
        )
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS job_embeddings_embedding_hnsw_idx "
                "ON job_embeddings USING hnsw (embedding vector_cosine_ops)"
            )
        )


async def _get_current_dimensions(connection: AsyncConnection) -> dict[str, int | None]:
    result = await connection.execute(
        text(
            "SELECT table_name, atttypmod - 4 AS dimension "
            "FROM information_schema.columns "
            "JOIN pg_attribute ON attname = column_name "
            "JOIN pg_class ON pg_class.oid = attrelid "
            "AND pg_class.relname = table_name "
            "WHERE table_schema = 'public' "
            "AND table_name IN ('resume_embeddings', 'job_embeddings') "
            "AND column_name = 'embedding'"
        )
    )
    return {str(row.table_name): row.dimension for row in result}
