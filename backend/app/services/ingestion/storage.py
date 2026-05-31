from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.core.config import Settings
from app.services.ingestion.filenames import safe_filename


def save_upload_bytes(
    file_bytes: bytes,
    *,
    filename: str | None,
    kind: str,
    settings: Settings,
) -> str:
    """Persist an uploaded source file under the configured local storage directory."""

    safe_name = safe_filename(filename, fallback="upload")
    storage_root = Path(settings.upload_storage_dir)
    destination_dir = storage_root / kind
    destination_dir.mkdir(parents=True, exist_ok=True)

    destination = destination_dir / f"{uuid4()}-{safe_name}"
    destination.write_bytes(file_bytes)
    return str(destination)
